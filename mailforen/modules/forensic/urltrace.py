from typing import Any

from ...core.http import http_client
from ...core.logger import logger


class URLTracer:
    """Trace URL redirects safely"""
    
    def trace(self, url: str) -> dict[str, Any]:
        """Trace redirect chain"""
        chain = []
        current_url = url
        visited = set()
        
        try:
            for i in range(10):  # Max 10 redirects
                if current_url in visited:
                    break
                visited.add(current_url)
                
                resp = http_client.head(current_url)
                if not resp:
                    # Try GET
                    resp = http_client.get(current_url)
                
                if not resp:
                    break
                
                chain.append({
                    "step": i + 1,
                    "url": current_url,
                    "status_code": resp.status_code
                })
                
                if resp.status_code in [301, 302, 303, 307, 308]:
                    location = resp.headers.get('Location')
                    if not location:
                        break
                    # Handle relative URLs
                    if location.startswith('http'):
                        current_url = location
                    else:
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, location)
                else:
                    break
            
            return {
                "original_url": url,
                "redirect_chain": chain,
                "final_url": chain[-1]['url'] if chain else url,
                "total_redirects": len(chain) - 1 if chain else 0
            }
        except Exception as e:
            logger.error(f"URL trace failed: {e}")
            return {"original_url": url, "error": str(e)}

url_tracer = URLTracer()
