from typing import Any

from ...core.http import http_client
from ...core.logger import logger


class CTSearch:
    """Certificate Transparency log search via crt.sh"""
    
    def search(self, domain: str) -> dict[str, Any]:
        """Search crt.sh for certificates"""
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            resp = http_client.get(url)
            if resp and resp.status_code == 200:
                data = resp.json()
                # Extract unique subdomains
                subdomains = set()
                for cert in data:
                    name_value = cert.get('name_value', '')
                    for name in name_value.split('\n'):
                        name = name.strip().lower()
                        if name and '*' not in name and name.endswith(domain):
                            subdomains.add(name)
                
                return {
                    "domain": domain,
                    "certificates_found": len(data),
                    "unique_subdomains": sorted(subdomains),
                    "raw_count": len(data)
                }
            return {"domain": domain, "error": f"HTTP {resp.status_code if resp else 'None'}"}
        except Exception as e:
            logger.error(f"CT search failed: {e}")
            return {"domain": domain, "error": str(e)}

ct_search = CTSearch()
