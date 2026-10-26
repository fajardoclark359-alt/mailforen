import dns.resolver
from typing import Dict, Any
from ...core.logger import logger
from ...utils.validators import validators

class EmailAuthChecker:
    """Check SPF, DKIM, DMARC"""
    
    def check_all(self, domain: str) -> Dict[str, Any]:
        """Check all email authentication records"""
        results = {
            "domain": domain,
            "spf": self.check_spf(domain),
            "dmarc": self.check_dmarc(domain),
            "mx": self.check_mx(domain)
        }
        return results
    
    def check_spf(self, domain: str) -> Dict[str, Any]:
        """Check SPF record"""
        try:
            answers = dns.resolver.resolve(domain, 'TXT')
            spf_records = []
            for rdata in answers:
                txt = b''.join(rdata.strings).decode('utf-8')
                if txt.startswith('v=spf1'):
                    spf_records.append(txt)
            return {
                "found": len(spf_records) > 0,
                "records": spf_records
            }
        except Exception as e:
            logger.debug(f"SPF lookup failed for {domain}: {e}")
            return {"found": False, "error": str(e)}
    
    def check_dmarc(self, domain: str) -> Dict[str, Any]:
        """Check DMARC record"""
        try:
            dmarc_domain = f"_dmarc.{domain}"
            answers = dns.resolver.resolve(dmarc_domain, 'TXT')
            dmarc_records = []
            for rdata in answers:
                txt = b''.join(rdata.strings).decode('utf-8')
                if txt.startswith('v=DMARC1'):
                    dmarc_records.append(txt)
            return {
                "found": len(dmarc_records) > 0,
                "records": dmarc_records
            }
        except Exception as e:
            logger.debug(f"DMARC lookup failed for {domain}: {e}")
            return {"found": False, "error": str(e)}
    
    def check_mx(self, domain: str) -> Dict[str, Any]:
        """Check MX records"""
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            mx_records = []
            for rdata in answers:
                mx_records.append({
                    "priority": rdata.preference,
                    "exchange": str(rdata.exchange).rstrip('.')
                })
            mx_records.sort(key=lambda x: x['priority'])
            return {
                "found": True,
                "records": mx_records
            }
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")
            return {"found": False, "error": str(e)}

auth_checker = EmailAuthChecker()
