from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for mailforen"""
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MAILFOREN_")
    
    # App settings
    app_name: str = "mailforen"
    data_dir: Path = Path.home() / ".mailforen"
    debug: bool = False
    
    # Network settings
    user_agent: str = "mailforen/0.1.0 (OSINT Research Tool)"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    proxy: str | None = None
    
    # Safety
    allow_unsafe: bool = False
    
    # API keys (optional)
    virustotal_api_key: str | None = None
    shodan_api_key: str | None = None
    securitytrails_api_key: str | None = None
    emailrep_api_key: str | None = None
    
settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)
