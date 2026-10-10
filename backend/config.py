"""
Configuration settings for the OMR Evaluator system.
"""
import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./omr_evaluator.db")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: list = ['.jpg', '.jpeg', '.png', '.pdf']
    
    # OMR Processing settings
    ALLOW_RESUBMISSION: bool = os.getenv("ALLOW_RESUBMISSION", "true").lower() == "true"
    REQUIRE_TEACHER_APPROVAL_FOR_RESUBMISSION: bool = os.getenv("REQUIRE_TEACHER_APPROVAL", "false").lower() == "true"
    
    # API settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        # Current production frontend deployment
        "https://scanalyze-omr-evaluator-app.vercel.app",
        # Active deployment used currently
        "https://scanalyze-smart-omr-evaluator.vercel.app",
        # Planned custom domains (add both apex and www)
        "https://scanalyze-omr-evaluator.com",
        "https://www.scanalyze-omr-evaluator.com",
        # Other historical Vercel preview/alt domains (keep for safety)
        "https://scanalyze-gamma.vercel.app",
        "https://scanalyze-omr-evaluator.vercel.app",
        "https://markit-omr-evaluator.vercel.app",
    ] if not os.getenv("CORS_ORIGINS") else os.getenv("CORS_ORIGINS").split(",")
    
    @classmethod
    def get_upload_path(cls) -> str:
        """Get the absolute path for uploads directory"""
        return os.path.abspath(cls.UPLOAD_DIR)

# Create global settings instance
settings = Settings()