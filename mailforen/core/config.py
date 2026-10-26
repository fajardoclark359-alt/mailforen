from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Configuration for mailforen"""
    
    # App settings
    app_name: str = "mailforen"
    data_dir: Path = Path.home() / ".mailforen"
    debug: bool = False
    
    # Network settings
    user_agent: str = "mailforen/0.1.0 (OSINT Research Tool)"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    proxy: Optional[str] = None
    
    # Safety
    allow_unsafe: bool = False
    
    # API keys (optional)
    virustotal_api_key: Optional[str] = None
    shodan_api_key: Optional[str] = None
    securitytrails_api_key: Optional[str] = None
    emailrep_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "MAILFOREN_"

settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)
