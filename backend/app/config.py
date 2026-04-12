import os 
from typing import Optional, List
from pydantic_settings import BaseSettings 
from pydantic import Field 
from functools import lru_cache

class Settings(BaseSettings):
    
    APP_NAME: str = Field(default = "FloatChat API", description = "Application name")
    APP_VERSION: str = Field(default = "1.0.0", description = "Application version")
    DEBUG: bool = Field(default = False, description = "Debug Mode")
    API_PREFIX: str = Field(default = "/api/v1", description = "API prefix")
    
    #Server
    HOST: str = Field(default = "0.0.0.0", description = "Server Host")
    PORT: str = Field(default = 8000, description = "Server port")
    WORKERS: str = Field(default = 1, description = "Number of workers")
    
    #Database
    DATABASE_URL : str = Field(default = "sqlite+aiosqlite:///./data/processed/argodata.db",
                               description = "Database connection URL")
    
    #REDIS URL
    REDIS_URL: str = Field(default = "redis://localhost:6379/0", description = "Redis connection URL")
    REDIS_CACHE_TTL: int = Field(default = 3600, description = "Cache TTL in seconds")
    
    #LLM Models
    GEMINI_API_KEY: Optional[str]  = Field(default=None, description="Gemini API Key")
    OPENAI_API_KEY: Optional[str]  = Field(default=None, description="OpenAI API Key")
    
    #Query Limits
    MAX_QUERY_LENGTH: int = Field(default = 500, description="Max query string length")
    MAX_RESULTS: int = Field(default = 1000, description = "Max query results")
    MAX_EXPORT_ROWS: int = Field(default=10000, description="Max export rows")
    
    #CORS
    CORS_ORIGINS: List[str] = Field(
        default = ["*"],
        description = "Allowed CORS origins"
    )
    
    #Logging
    LOG_LEVEL: str = Field(default = "INFO", description = "Logging level")
    LOG_FORMAT: str = Field(default = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",description="Log Format")
    
    
class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    case_sensitive = True
    

@lru_cache()
def get_settings() -> Settings: 
    return Settings()

settings = get_settings()