import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from ...core.logger import logger


class HeaderAnalyzer:
    """Analyze email headers for forensics"""
    
    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze .eml file"""
        try:
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            return self.analyze_message(msg)
        except Exception as e:
            logger.error(f"Failed to parse email: {e}")
            return {"error": str(e)}
    
    def analyze_message(self, msg) -> dict[str, Any]:
        """Analyze email message object"""
        results = {
            "from": msg.get('From'),
            "to": msg.get('To'),
            "subject": msg.get('Subject'),
            "date": msg.get('Date'),
            "message_id": msg.get('Message-ID'),
            "reply_to": msg.get('Reply-To'),
            "return_path": msg.get('Return-Path'),
            "received_chain": [],
            "authentication_results": msg.get('Authentication-Results'),
            "received_spf": msg.get('Received-SPF'),
            "user_agent": None,
            "x_mailer": msg.get('X-Mailer'),
            "originating_ips": []
        }
        
        # Parse Received headers (trace path)
        received_headers = msg.get_all('Received', [])
        for i, received in enumerate(reversed(received_headers)):
            results["received_chain"].append({
                "hop": len(received_headers) - i,
                "raw": received
            })
            # Extract IPs
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', received)
            for ip in ips:
                if ip not in ['127.0.0.1', '0.0.0.0']:
                    results["originating_ips"].append(ip)
        
        # Remove duplicates while preserving order
        results["originating_ips"] = list(dict.fromkeys(results["originating_ips"]))
        
        return results

header_analyzer = HeaderAnalyzer()
