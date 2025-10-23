from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import uuid
from pathlib import Path
import aiofiles
from datetime import datetime
import mimetypes

app = FastAPI(
    title="Video Streaming Service",
    description="Microservice for video file hosting and streaming",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploaded_videos")
UPLOAD_DIR.mkdir(exist_ok=True)

API_KEY = os.getenv("VIDEO_SERVICE_API_KEY", "your-secret-api-key-change-this")

ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  

video_metadata = {}


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_video_file(filename: str) -> bool:
    extension = get_file_extension(filename)
    return extension in ALLOWED_EXTENSIONS


@app.get("/")
async def root():
    return {
        "service": "Video Streaming Service",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "stream": "GET /stream/{video_id}",
            "info": "GET /video/{video_id}",
            "list": "GET /videos",
            "delete": "DELETE /video/{video_id}",
            "health": "GET /health"
        },
        "note": "All endpoints except /health require X-API-Key header"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "videos_count": len(video_metadata)
    }


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    if not validate_video_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    video_id = str(uuid.uuid4())
    file_extension = get_file_extension(file.filename)
    saved_filename = f"{video_id}{file_extension}"
    file_path = UPLOAD_DIR / saved_filename
    
    try:
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  
                file_size += len(chunk)
                
                if file_size > MAX_FILE_SIZE:
                    await f.close()
                    file_path.unlink()  
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024**3):.2f}GB"
                    )
                
                await f.write(chunk)
        
        video_metadata[video_id] = {
            "video_id": video_id,
            "original_filename": file.filename,
            "saved_filename": saved_filename,
            "file_path": str(file_path),
            "size": file_size,
            "content_type": file.content_type or "video/mp4",
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
        stream_url = f"http://localhost:8001/stream/{video_id}"
        
        return {
            "success": True,
            "video_id": video_id,
            "stream_url": stream_url,
            "filename": file.filename,
            "size": file_size,
            "message": "Video uploaded successfully"
        }
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


@app.get("/stream/{video_id}")
async def stream_video(video_id: str, request: Request):
    if video_id not in video_metadata:
        raise HTTPException(status_code=404, detail="Video not found")
    
    metadata = video_metadata[video_id]
    file_path = Path(metadata["file_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    
    file_size = file_path.stat().st_size
    
    range_header = request.headers.get("range")
    
    if range_header:
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if len(range_match) > 1 and range_match[1] else file_size - 1
        
        if start >= file_size or end >= file_size:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        
        chunk_size = end - start + 1
        
        async def stream_file():
            async with aiofiles.open(file_path, 'rb') as video_file:
                await video_file.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(1024 * 1024, remaining)  # Read 1MB at a time
                    data = await video_file.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": metadata["content_type"],
        }
        
        return StreamingResponse(
            stream_file(),
            status_code=206,
            headers=headers
        )
    
    else:
        async def stream_file():
            async with aiofiles.open(file_path, 'rb') as video_file:
                while chunk := await video_file.read(1024 * 1024):  # Read 1MB at a time
                    yield chunk
        
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": metadata["content_type"],
        }
        
        return StreamingResponse(
            stream_file(),
            headers=headers
        )


@app.get("/video/{video_id}")
async def get_video_info(
    video_id: str,
    api_key: str = Depends(verify_api_key)
):
    if video_id not in video_metadata:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video_metadata[video_id]


@app.get("/videos")
async def list_videos(
    api_key: str = Depends(verify_api_key),
    limit: int = 100,
    offset: int = 0
):
    videos = list(video_metadata.values())
    
    return {
        "total": len(videos),
        "limit": limit,
        "offset": offset,
        "videos": videos[offset:offset + limit]
    }


@app.delete("/video/{video_id}")
async def delete_video(
    video_id: str,
    api_key: str = Depends(verify_api_key)
):
    if video_id not in video_metadata:
        raise HTTPException(status_code=404, detail="Video not found")
    
    metadata = video_metadata[video_id]
    file_path = Path(metadata["file_path"])
    
    try:
        if file_path.exists():
            file_path.unlink()
        
        del video_metadata[video_id]
        
        return {
            "success": True,
            "message": "Video deleted successfully",
            "video_id": video_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting video: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )