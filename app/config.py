import os
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TraceAI"
    TAGLINE: str = "Finding Hope Through Intelligence"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:admin@localhost:3306/traceai"
    )
    
    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "8f3d2e1b9c7f4a0e5d6c3b2a1f8e7d4c9b0a3f2e1d8c7b6a5f4e3d2c1b0a99"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI Services
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Upload Directories
    UPLOAD_DIR: str = os.path.join("app", "static", "uploads")
    AGE_PROGRESSED_DIR: str = os.path.join("app", "static", "age_progressed")
    
    # MediaPipe landmarker task
    MEDIAPIPE_MODEL_PATH: str = os.getenv("MEDIAPIPE_MODEL_PATH", "face_landmarker.task")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AGE_PROGRESSED_DIR, exist_ok=True)
