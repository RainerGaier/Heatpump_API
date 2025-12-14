"""
Configuration settings for the FastAPI application.

This module manages environment variables and configuration settings
for the API server, including host, port, CORS, and security settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in:
    - .env file in project root
    - System environment variables
    - Docker/Kubernetes configuration
    """

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="API server host")
    PORT: int = Field(default=8000, description="API server port")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    WORKERS: int = Field(default=1, description="Number of worker processes")

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="Allowed CORS origins",
    )

    # API Configuration
    API_PREFIX: str = Field(default="/api/v1", description="API route prefix")
    API_TITLE: str = Field(default="Heatpump Simulator API", description="API title")
    API_VERSION: str = Field(default="0.1.0", description="API version")

    # Security (TODO: Implement authentication)
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT tokens",
    )
    API_KEY_ENABLED: bool = Field(
        default=False,
        description="Enable API key authentication",
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=False,
        description="Enable rate limiting",
    )
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Max requests per minute per client",
    )

    # Task Queue (for future Celery/RQ integration)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for task queue and caching",
    )
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL",
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    # Simulation Configuration
    SIMULATION_TIMEOUT: int = Field(
        default=300,
        description="Maximum simulation time in seconds",
    )
    CACHE_ENABLED: bool = Field(
        default=False,
        description="Enable result caching",
    )
    CACHE_TTL: int = Field(
        default=3600,
        description="Cache TTL in seconds",
    )

    # Google Cloud Storage Configuration
    GCP_PROJECT_ID: str = Field(
        default="",
        description="GCP project ID",
    )
    GCS_BUCKET_NAME: str = Field(
        default="heatpump-reports",
        description="Cloud Storage bucket name for reports",
    )
    GCS_LOCATION: str = Field(
        default="europe-west2",
        description="Cloud Storage bucket location",
    )
    REPORTS_EXPIRY_DAYS: int = Field(
        default=30,
        description="Number of days before reports expire",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency for accessing settings in route handlers.

    Usage:
        settings: Settings = Depends(get_settings)
    """
    return settings
