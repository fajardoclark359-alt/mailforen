import re
import ipaddress
from typing import Optional

class Validators:
    @staticmethod
    def is_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_domain(domain: str) -> bool:
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    @staticmethod
    def is_ip(ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_url(url: str) -> bool:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def extract_domain_from_email(email: str) -> Optional[str]:
        """Extract domain from a mailto-style or display-name email address."""
        # Strip display name and angle brackets if present
        email = email.strip()
        if '<' in email and '>' in email:
            # "Name" <user@example.com> format
            addr = email[email.index('<') + 1:email.index('>')]
        else:
            addr = email
        if '@' in addr:
            domain = addr.split('@')[1].rstrip('>')
            if domain:
                return domain
        return None

validators = Validators()
