import requests
import os
from pathlib import Path


class VideoServiceClient:
    def __init__(self, base_url: str = "http://localhost:8001", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("VIDEO_SERVICE_API_KEY", "your-secret-api-key-change-this")
        self.headers = {"X-API-Key": self.api_key}
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def upload_video(self, file_path: str):
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'video/mp4')}
            response = requests.post(
                f"{self.base_url}/upload",
                files=files,
                headers=self.headers
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Upload failed: {response.text}")
    
    def get_video_info(self, video_id: str):
        response = requests.get(
            f"{self.base_url}/video/{video_id}",
            headers=self.headers
        )
        return response.json()
    
    def list_videos(self, limit: int = 100, offset: int = 0):
        response = requests.get(
            f"{self.base_url}/videos",
            params={"limit": limit, "offset": offset},
            headers=self.headers
        )
        return response.json()
    
    def delete_video(self, video_id: str):
        response = requests.delete(
            f"{self.base_url}/video/{video_id}",
            headers=self.headers
        )
        return response.json()
    
    def get_stream_url(self, video_id: str):
        return f"{self.base_url}/stream/{video_id}"


if __name__ == "__main__":
    client = VideoServiceClient()
    
    print("Health Check:")
    print(client.health_check())
    print()
    
    # Upload a video (replace with your video file path)
    # video_path = "path/to/your/video.mp4"
    # result = client.upload_video(video_path)
    # print("Upload Result:")
    # print(result)
    # print()
    # print(f"Stream URL: {result['stream_url']}")
    
    # List videos
    print("Listing videos:")
    videos = client.list_videos()
    print(videos)