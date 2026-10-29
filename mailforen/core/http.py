
import time

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
        self.rate_limit_delay = settings.rate_limit_delay
        self._last_request_at: float | None = None

    def _throttle(self) -> None:
        """Enforce settings.rate_limit_delay between consecutive requests.

        The delay applies per HTTPClient instance (attempts included), so a
        shared client never hammers an API faster than configured.
        """
        if self.rate_limit_delay <= 0:
            return
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            remaining = self.rate_limit_delay - elapsed
            if remaining > 0:
                logger.debug(f"Rate limit: sleeping {remaining:.2f}s")
                time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def get(self, url: str, params: dict | None = None, **kwargs) -> httpx.Response | None:
        """Perform GET request (follows redirects)"""
        try:
            self._throttle()
            with httpx.Client(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
                proxy=self.proxy,
            ) as client:
                response = client.get(url, params=params, **kwargs)
                logger.debug(f"GET {url} -> {response.status_code}")
                return response
        except Exception as e:
            logger.error(f"HTTP GET failed for {url}: {e}")
            return None

    def head(self, url: str, **kwargs) -> httpx.Response | None:
        """Perform HEAD request.

        Redirects are NOT followed: callers such as the URL tracer need to
        observe raw 3xx responses and Location headers themselves.
        """
        try:
            self._throttle()
            with httpx.Client(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=False,
                proxy=self.proxy,
            ) as client:
                response = client.head(url, **kwargs)
                logger.debug(f"HEAD {url} -> {response.status_code}")
                return response
        except Exception as e:
            logger.error(f"HTTP HEAD failed for {url}: {e}")
            return None

http_client = HTTPClient()
