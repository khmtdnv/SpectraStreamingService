from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    video_service_api_key: str = "my-super-secret-key-12345"
    upload_dir: Path = Path("uploaded_videos")
    max_file_size: int = 5 * 1024 * 1024 * 1024  # 5GB
    
    allowed_extensions: set = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    
    host: str = "0.0.0.0"
    port: int = 8001
    reload: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()