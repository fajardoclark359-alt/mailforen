from typing import Any

import dns.resolver

from ...core.logger import logger


class DomainIntel:
    """Domain intelligence gathering"""
    
    def get_all_records(self, domain: str) -> dict[str, Any]:
        """Get all DNS records"""
        results = {
            "domain": domain,
            "a": self.get_a_records(domain),
            "aaaa": self.get_aaaa_records(domain),
            "mx": self.get_mx_records(domain),
            "ns": self.get_ns_records(domain),
            "txt": self.get_txt_records(domain),
            "cname": self.get_cname_records(domain)
        }
        return results
    
    def get_a_records(self, domain: str) -> list[str]:
        try:
            answers = dns.resolver.resolve(domain, 'A')
            return [str(rdata) for rdata in answers]
        except Exception as e:
            logger.debug(f"A lookup failed: {e}")
            return []
    
    def get_aaaa_records(self, domain: str) -> list[str]:
        try:
            answers = dns.resolver.resolve(domain, 'AAAA')
            return [str(rdata) for rdata in answers]
        except Exception as e:
            logger.debug(f"AAAA lookup failed: {e}")
            return []
    
    def get_mx_records(self, domain: str) -> list[dict]:
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            records = [{"priority": r.preference, "host": str(r.exchange).rstrip('.')} for r in answers]
            return sorted(records, key=lambda x: x['priority'])
        except Exception as e:
            logger.debug(f"MX lookup failed: {e}")
            return []
    
    def get_ns_records(self, domain: str) -> list[str]:
        try:
            answers = dns.resolver.resolve(domain, 'NS')
            return [str(rdata).rstrip('.') for rdata in answers]
        except Exception as e:
            logger.debug(f"NS lookup failed: {e}")
            return []
    
    def get_txt_records(self, domain: str) -> list[str]:
        try:
            answers = dns.resolver.resolve(domain, 'TXT')
            records = []
            for rdata in answers:
                records.append(b''.join(rdata.strings).decode('utf-8'))
            return records
        except Exception as e:
            logger.debug(f"TXT lookup failed: {e}")
            return []
    
    def get_cname_records(self, domain: str) -> list[str]:
        try:
            answers = dns.resolver.resolve(domain, 'CNAME')
            return [str(rdata).rstrip('.') for rdata in answers]
        except Exception as e:
            logger.debug(f"CNAME lookup failed: {e}")
            return []

domain_intel = DomainIntel()
