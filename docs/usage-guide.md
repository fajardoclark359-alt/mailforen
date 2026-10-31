# Usage Guide

Practical workflows and examples for mailforen.

---

## Typical Investigation Workflow

### 1. Create a Case

```bash
mailforen case new "Invoice-Phishing-2024-03-15" \
  --target "payroll-services.example.com" \
  --desc "Phishing email targeting HR department with fake invoice attachment"
```

Output:
```
✓ Created case Invoice-Phishing-2024-03-15 (ID: 1)
```

### 2. Analyze the Suspicious Email

```bash
# Parse headers
mailforen email headers invoice_phish.eml --case-id 1

# Check sender domain authentication
mailforen email auth payroll-services.example.com --case-id 1
```

### 3. Investigate Infrastructure

```bash
# Domain intelligence
mailforen domain intel payroll-services.example.com --case-id 1

# IP intelligence (from headers or domain A record)
mailforen ip intel 203.0.113.42 --case-id 1

# Certificate transparency
mailforen ct search payroll-services.example.com --case-id 1

# Trace any URLs in the email
mailforen url trace "https://bit.ly/fake-invoice-pdf" --case-id 1
```

### 4. Pivot on Identities

```bash
# If email mentions a username/handle
mailforen user pivot "john.doe.hr" --case-id 1

# Extract metadata from attachments
mailforen file meta invoice.pdf --case-id 1
```

### 5. Generate Report

```bash
# HTML (default) - best for viewing
mailforen report generate --case-id 1 --format html

# PDF - for evidence submission
mailforen report generate --case-id 1 --format pdf

# JSON - for SIEM ingestion
mailforen report generate --case-id 1 --format json

# Markdown - for documentation
mailforen report generate --case-id 1 --format markdown
```

Reports saved to `~/.mailforen/reports/`.

### 6. Review Case

```bash
mailforen case show 1
```

---

## Phishing Email Triage Checklist

| Step | Command | What to Look For |
|------|---------|------------------|
| 1. Headers | `email headers` | Mismatched From/Return-Path, suspicious Received hops, odd X-Mailer |
| 2. Auth | `email auth` | SPF fail/softfail, no DMARC, DMARC p=none |
| 3. Domain | `domain intel` | Newly registered, suspicious subdomains, unrelated MX |
| 4. IPs | `ip intel` | Hosting providers, VPN/proxy ASNs, geo mismatch |
| 5. CT | `ct search` | Many certs for lookalike domains |
| 6. URLs | `url trace` | Long redirect chains, URL shorteners, credential harvesters |
| 7. Attachments | `file meta` | Executables, macros, mismatched MIME |

---

## Advanced Usage

### Unsafe Mode (Active Checks)

Currently no active checks implemented. Reserved for future use:

```bash
mailforen --unsafe email auth example.com
# ⚠ Unsafe mode enabled: active checks may contact targets directly.
```

### Environment Configuration

Create `.env` in project root or working directory:

```bash
# ~/.mailforen/.env or ./.env
MAILFOREN_DEBUG=true
MAILFOREN_RATE_LIMIT_DELAY=2.0
MAILFOREN_PROXY=http://127.0.0.1:8080
MAILFOREN_VIRUSTOTAL_API_KEY=your_key_here
MAILFOREN_SHODAN_API_KEY=your_key_here
```

### Python API Usage

```python
from mailforen.core.config import settings
from mailforen.core.db import db
from mailforen.modules.email.auth import auth_checker
from mailforen.modules.forensic.domain import domain_intel
from mailforen.reports.generator import report_generator

# Configure
settings.debug = True
settings.rate_limit_delay = 2.0

# Create case
case_id = db.create_case("My Investigation", "target.com", "Description")

# Run checks
auth_result = auth_checker.check_all("target.com")
domain_result = domain_intel.get_all_records("target.com")

# Save findings
db.add_finding(case_id, "email.auth", "target.com", auth_result, "medium")
db.add_finding(case_id, "domain.intel", "target.com", domain_result, "info")

# Generate report
report_path = report_generator.generate(case_id, "html")
print(f"Report: {report_path}")
```

---

## Output Formats

### HTML Report
- Styled with embedded CSS
- Risk color-coded (high=red, medium=orange, low=green, info=blue)
- Includes disclaimer banner
- Self-contained single file

### Markdown Report
- GitHub-flavored markdown
- Code blocks for JSON results
- Easy to version control

### JSON Report
- Full case + findings structure
- ISO timestamps
- Suitable for SIEM/log aggregation

### PDF Report
- Generated via weasyprint (preferred) or pdfkit/wkhtmltopdf
- Falls back to HTML if neither available
- Page breaks between findings

---

## Tips & Tricks

### List All Cases
```bash
mailforen case list
```

### Find Case by Name
```bash
mailforen case list | grep "Phishing"
```

### View Findings for a Case
```bash
mailforen case show 1
```

### Export Findings as JSON (via Python)
```python
from mailforen.core.db import db
import json

findings = db.get_findings(1)
print(json.dumps(findings, indent=2))
```

### Increase Verbosity
```bash
MAILFOREN_DEBUG=true mailforen email auth example.com
```

### Use with Custom Data Directory
```bash
MAILFOREN_DATA_DIR=/tmp/investigation mailforen case new "Test"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: PySide6` | GUI not needed; `pip install mailforen` without GUI deps, or install PySide6 |
| `pdfkit`/`weasyprint` errors | Install system deps: `apt-get install wkhtmltopdf` or `pip install weasyprint` |
| DNS resolution fails | Check `/etc/resolv.conf`, try `dig @8.8.8.8 example.com` |
| Rate limited by APIs | Increase `MAILFOREN_RATE_LIMIT_DELAY` |
| Case name already exists | Use different name or `case show` existing |
| `originating_ips` empty | Check Received headers exist in .eml; IPv6 not extracted |

---

## Integration Examples

### Cron Job for Daily CT Monitoring
```bash
# /etc/cron.d/mailforen-ct
0 6 * * * analyst MAILFOREN_DATA_DIR=/var/lib/mailforen \
  mailforen ct search example.com --case-id 1 >> /var/log/mailforen-ct.log 2>&1
```

### SIEM Ingestion (JSON)
```bash
mailforen report generate --case-id 1 --format json
# → Feed ~/.mailforen/reports/report_*.json to log forwarder
```

### Jupyter Notebook Analysis
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("~/.mailforen/cases.db")
cases = pd.read_sql("SELECT * FROM cases", conn)
findings = pd.read_sql("SELECT * FROM findings", conn)
conn.close()
```