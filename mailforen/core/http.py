import httpx
from typing import Optional, Dict, Any
from .config import settings
from .logger import logger

class HTTPClient:
    """HTTP client with rate limiting and safety features"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "*/*"
        }
        self.timeout = settings.timeout
        self.proxies = {"http://": settings.proxy, "https://": settings.proxy} if settings.proxy else None
    
    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Optional[httpx.Response]:
        """Perform GET request"""
        try:
            with httpx.Client(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
                proxies=self.proxies
            ) as client:
                response = client.get(url, params=params, **kwargs)
                logger.debug(f"GET {url} -> {response.status_code}")
                return response
        except Exception as e:
            logger.error(f"HTTP GET failed for {url}: {e}")
            return None
    
    def head(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """Perform HEAD request"""
        try:
            with httpx.Client(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
                proxies=self.proxies
            ) as client:
                response = client.head(url, **kwargs)
                logger.debug(f"HEAD {url} -> {response.status_code}")
                return response
        except Exception as e:
            logger.error(f"HTTP HEAD failed for {url}: {e}")
            return None

http_client = HTTPClient()
