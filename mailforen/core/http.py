
import httpx

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
        self.proxy = settings.proxy
    
    def get(self, url: str, params: dict | None = None, **kwargs) -> httpx.Response | None:
        """Perform GET request"""
        try:
            client_kwargs = {
                "headers": self.headers,
                "timeout": self.timeout,
                "follow_redirects": True,
            }
            if self.proxy:
                client_kwargs["proxy"] = self.proxy
            with httpx.Client(**client_kwargs) as client:
                response = client.get(url, params=params, **kwargs)
                logger.debug(f"GET {url} -> {response.status_code}")
                return response
        except Exception as e:
            logger.error(f"HTTP GET failed for {url}: {e}")
            return None
    
    def head(self, url: str, **kwargs) -> httpx.Response | None:
        """Perform HEAD request"""
        try:
            client_kwargs = {
                "headers": self.headers,
                "timeout": self.timeout,
                "follow_redirects": True,
            }
            if self.proxy:
                client_kwargs["proxy"] = self.proxy
            with httpx.Client(**client_kwargs) as client:
                response = client.head(url, **kwargs)
                logger.debug(f"HEAD {url} -> {response.status_code}")
                return response
        except Exception as e:
            logger.error(f"HTTP HEAD failed for {url}: {e}")
            return None

http_client = HTTPClient()
