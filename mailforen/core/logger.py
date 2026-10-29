import logging

from rich.logging import RichHandler

from .config import settings


def setup_logger(name: str = "mailforen") -> logging.Logger:
    """Setup logger with rich formatting"""
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Console handler with rich
    console_handler = RichHandler(rich_tracebacks=True, markup=True)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_dir / "mailforen.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
