import socket
from typing import Any

from ...core.logger import logger


class IPIntel:
    """IP intelligence gathering"""
    
    def get_info(self, ip: str) -> dict[str, Any]:
        """Get IP information"""
        results = {
            "ip": ip,
            "reverse_dns": self.reverse_dns(ip),
            "ptr": None
        }
        if results["reverse_dns"]:
            results["ptr"] = results["reverse_dns"]
        return results
    
    def reverse_dns(self, ip: str) -> str | None:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception as e:
            logger.debug(f"Reverse DNS failed for {ip}: {e}")
            return None
    
    def get_asn_info(self, ip: str) -> dict[str, Any]:
        """Get ASN info via ipinfo.io (free, no key needed for basic)"""
        from ...core.http import http_client
        try:
            resp = http_client.get(f"https://ipinfo.io/{ip}/json")
            if resp and resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.debug(f"ipinfo lookup failed: {e}")
        return {}

ip_intel = IPIntel()
