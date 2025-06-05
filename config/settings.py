"""
Application Configuration Settings

Centralized configuration management for the IDX Signal Scraping API.
Supports environment-based configuration for development and production.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Info
    APP_NAME: str = "IDX Signal Scraping API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API untuk mengambil data historis saham IDX dari Investing.com"
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = Field(default=100, env="API_RATE_LIMIT")  # requests per minute
    API_RATE_LIMIT_BURST: int = Field(default=20, env="API_RATE_LIMIT_BURST")
    
    # External API Settings
    INVESTING_API_BASE_URL: str = "https://api.investing.com/api"
    INVESTING_API_TIMEOUT: int = Field(default=15, env="INVESTING_API_TIMEOUT")
    INVESTING_API_RETRIES: int = Field(default=3, env="INVESTING_API_RETRIES")
    
    # Cache Settings
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Rate Limiting
    MAX_BULK_STOCKS: int = Field(default=20, env="MAX_BULK_STOCKS")
    MAX_DATE_RANGE_DAYS: int = Field(default=365, env="MAX_DATE_RANGE_DAYS")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Security
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    API_KEY_HEADER: str = "X-API-Key"
    REQUIRE_API_KEY: bool = Field(default=False, env="REQUIRE_API_KEY")
    
    # Database (for future use)
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # IDX Signal Specific
    DEFAULT_SIGNAL_INTERVAL_MONTHS: int = 4
    DEFAULT_CAPITAL: int = 5000000  # 5 million IDR
    DEFAULT_MAX_LOSS: int = 200000  # 200K IDR
    DEFAULT_MIN_SCORE: int = 2
    
    # Trading Journal Integration
    GOOGLE_SHEETS_ENABLED: bool = Field(default=False, env="GOOGLE_SHEETS_ENABLED")
    GOOGLE_SHEETS_ID: Optional[str] = Field(default=None, env="GOOGLE_SHEETS_ID")
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = Field(default=None, env="GOOGLE_SERVICE_ACCOUNT_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    CACHE_TTL: int = 60  # Shorter cache for development
    API_RATE_LIMIT: int = 1000  # More lenient for development

class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 4
    API_RATE_LIMIT: int = 100
    REQUIRE_API_KEY: bool = True
    ALLOWED_HOSTS: List[str] = ["api.idxsignal.com", "localhost"]
    CORS_ORIGINS: List[str] = ["https://idxsignal.com", "https://app.idxsignal.com"]

class TestingSettings(Settings):
    """Testing environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    CACHE_ENABLED: bool = False  # Disable cache for testing
    API_RATE_LIMIT: int = 10000  # No limits for testing
    INVESTING_API_TIMEOUT: int = 5  # Shorter timeout for tests
    DATABASE_URL: str = "sqlite:///./test.db"

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings based on environment.
    Uses caching to avoid reloading settings multiple times.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Global settings instance
settings = get_settings()

# Helper functions for common configurations
def get_database_url() -> str:
    """Get database URL with fallback"""
    return settings.DATABASE_URL or "sqlite:///./idx_signal.db"

def get_redis_url() -> Optional[str]:
    """Get Redis URL for caching"""
    return settings.REDIS_URL

def is_production() -> bool:
    """Check if running in production environment"""
    return settings.ENVIRONMENT.lower() == "production"

def is_development() -> bool:
    """Check if running in development environment"""
    return settings.ENVIRONMENT.lower() == "development"

def get_cors_config() -> dict:
    """Get CORS configuration"""
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

def get_logging_config() -> dict:
    """Get logging configuration"""
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default" if is_development() else "json",
                "level": settings.LOG_LEVEL,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # Add file handler for production
    if settings.LOG_FILE and is_production():
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": settings.LOG_FILE,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": settings.LOG_LEVEL,
        }
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
    
    return config

# Export commonly used settings
__all__ = [
    "Settings",
    "DevelopmentSettings", 
    "ProductionSettings",
    "TestingSettings",
    "get_settings",
    "settings",
    "get_database_url",
    "get_redis_url", 
    "is_production",
    "is_development",
    "get_cors_config",
    "get_logging_config",
]