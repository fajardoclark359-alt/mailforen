# API Reference

Python API reference for mailforen modules. All modules expose a singleton instance at module level.

---

## Core Modules

### `mailforen.core.config.Settings`

Pydantic Settings configuration. All fields overrideable via `MAILFOREN_` environment variables or `.env` file.

```python
from mailforen.core.config import settings

settings.data_dir        # Path: ~/.mailforen (created on import)
settings.debug           # bool: False
settings.user_agent      # str: "mailforen/0.1.0 (OSINT Research Tool)"
settings.timeout         # int: 30 (seconds)
settings.max_retries     # int: 3 (not currently used)
settings.rate_limit_delay # float: 1.0 (seconds between requests)
settings.proxy           # str | None
settings.allow_unsafe    # bool: False (set by --unsafe flag)
settings.virustotal_api_key   # str | None
settings.shodan_api_key       # str | None
settings.securitytrails_api_key # str | None
settings.emailrep_api_key     # str | None
```

---

### `mailforen.core.db.CaseDB`

SQLite-backed case and evidence management. Singleton: `db = CaseDB()`.

```python
from mailforen.core.db import db

# Create a new case
case_id = db.create_case(name: str, target: str | None = None, description: str | None = None) -> int

# List all cases
cases = db.list_cases() -> list[dict]

# Get case by ID
case = db.get_case(case_id: int) -> dict | None

# Add a finding to a case
finding_id = db.add_finding(
    case_id: int,
    module: str,           # e.g. "email.headers", "email.auth"
    input_data: str,       # original input (file path, domain, IP, etc.)
    result: dict,          # module output
    risk_level: str = "info",  # "info" | "low" | "medium" | "high"
    tags: list[str] | None = None,
    notes: str | None = None
) -> int

# Get all findings for a case
findings = db.get_findings(case_id: int) -> list[dict]
```

**Database Schema:**
- `cases(id, name UNIQUE, target, description, created_at, updated_at, status)`
- `findings(id, case_id, module, input_data, result_json, risk_level, tags, notes, timestamp)`
- `requests(id, case_id, url, method, module, timestamp, response_code)` — *schema only, not used*

**Note:** Foreign keys declared but not enforced (no `PRAGMA foreign_keys=ON`). No update/delete methods.

---

### `mailforen.core.http.HTTPClient`

HTTP client with rate limiting and safety features. Singleton: `http_client = HTTPClient()`.

```python
from mailforen.core.http import http_client

# GET request (follows redirects)
response = http_client.get(url: str, params: dict | None = None, **kwargs) -> httpx.Response | None

# HEAD request (does NOT follow redirects - for URL tracing)
response = http_client.head(url: str, **kwargs) -> httpx.Response | None
```

**Behavior:**
- New `httpx.Client` created per request
- Returns `None` on any exception (logged at ERROR)
- Rate limited by `settings.rate_limit_delay` (default 1.0s)
- Uses `settings.proxy` if configured
- `HEAD` explicitly uses `follow_redirects=False` to allow manual redirect tracing

---

### `mailforen.core.logger`

```python
from mailforen.core.logger import logger, setup_logger

logger = setup_logger(name: str = "mailforen") -> logging.Logger
```

**Configuration:**
- Log file: `~/.mailforen/logs/mailforen.log` (DEBUG level)
- Console: RichHandler at INFO level
- File format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

---

### `mailforen.core.safety`

Safety gate for active checks.

```python
from mailforen.core.safety import require_unsafe, UnsafeModeRequired

require_unsafe(action: str) -> None
    # Raises UnsafeModeRequired if settings.allow_unsafe is False
    # Logs WARNING when allowed
```

---

## Email Modules

### `mailforen.modules.email.headers.HeaderAnalyzer`

Parse `.eml` files and extract headers. Singleton: `header_analyzer = HeaderAnalyzer()`.

```python
from mailforen.modules.email.headers import header_analyzer

result = header_analyzer.analyze_file(file_path: Path) -> dict
result = header_analyzer.analyze_message(msg) -> dict  # email.message.Message
```

**Return dict keys:**
- `from`, `to`, `subject`, `date`, `message_id`, `reply_to`, `return_path`
- `received_chain`: list of `{"hop": int, "raw": str}` (newest first, hop 1 = topmost)
- `authentication_results`: raw Authentication-Results header
- `received_spf`: raw Received-SPF header
- `user_agent`: always `None` (not populated)
- `x_mailer`: X-Mailer header value
- `originating_ips`: list of IPv4 addresses from Received headers (deduped, loopback excluded)

**Errors:** Returns `{"error": str}` on parse failure.

---

### `mailforen.modules.email.auth.EmailAuthChecker`

Check SPF, DMARC, MX via DNS. Singleton: `auth_checker = EmailAuthChecker()`.

```python
from mailforen.modules.email.auth import auth_checker

result = auth_checker.check_all(domain: str) -> dict
result = auth_checker.check_spf(domain: str) -> dict
result = auth_checker.check_dmarc(domain: str) -> dict
result = auth_checker.check_mx(domain: str) -> dict
```

**Return structures:**

`check_spf` / `check_dmarc`:
```python
{"found": bool, "records": list[str]}  # on success
{"found": False, "error": str}         # on DNS failure
```

`check_mx`:
```python
{"found": bool, "records": [{"priority": int, "exchange": str}]}  # sorted by priority
```

`check_all`:
```python
{
    "domain": str,
    "spf": {...},
    "dmarc": {...},
    "mx": {...}
}
```

**Note:** DKIM verification is **not implemented** despite being advertised in docstrings/README.

---

## Forensic Modules

### `mailforen.modules.forensic.domain.DomainIntel`

DNS record gathering. Singleton: `domain_intel = DomainIntel()`.

```python
from mailforen.modules.forensic.domain import domain_intel

result = domain_intel.get_all_records(domain: str) -> dict
result = domain_intel.get_a_records(domain: str) -> list[str]
result = domain_intel.get_aaaa_records(domain: str) -> list[str]
result = domain_intel.get_mx_records(domain: str) -> list[dict]
result = domain_intel.get_ns_records(domain: str) -> list[str]
result = domain_intel.get_txt_records(domain: str) -> list[str]
result = domain_intel.get_cname_records(domain: str) -> list[str]
```

**Returns empty list on DNS failure (logged at DEBUG).**

**Note:** WHOIS/RDAP lookups **not implemented**.

---

### `mailforen.modules.forensic.ip.IPIntel`

IP intelligence via reverse DNS and ipinfo.io. Singleton: `ip_intel = IPIntel()`.

```python
from mailforen.modules.forensic.ip import ip_intel

result = ip_intel.get_info(ip: str) -> dict
result = ip_intel.reverse_dns(ip: str) -> str | None
result = ip_intel.get_asn_info(ip: str) -> dict
```

**`get_info` returns:**
```python
{
    "ip": str,
    "reverse_dns": str | None,
    "ptr": str | None  # duplicate of reverse_dns
}
```

**`get_asn_info` queries `https://ipinfo.io/{ip}/json` (no API key). Returns `{}` on failure.**

---

### `mailforen.modules.forensic.ct.CTSearch`

Certificate Transparency search via crt.sh. Singleton: `ct_search = CTSearch()`.

```python
from mailforen.modules.forensic.ct import ct_search

result = ct_search.search(domain: str) -> dict
```

**Returns:**
```python
{
    "domain": str,
    "certificates_found": int,
    "unique_subdomains": list[str],  # sorted, wildcard-free, suffix-matched
    "raw_count": int
}
```

**On error:** `{"domain": str, "error": str}`

**Algorithm:** Queries `https://crt.sh/?q=%.{domain}&output=json`, splits `name_value` on newlines, keeps names where `name.endswith(domain)` and no wildcard.

---

### `mailforen.modules.forensic.urltrace.URLTracer`

Safe redirect chain tracing. Singleton: `url_tracer = URLTracer()`.

```python
from mailforen.modules.forensic.urltrace import url_tracer

result = url_tracer.trace(url: str) -> dict
```

**Returns:**
```python
{
    "original_url": str,
    "redirect_chain": [
        {"step": int, "url": str, "status_code": int}
    ],
    "final_url": str,
    "total_redirects": int
}
```

**Behavior:**
- Max 10 hops
- Uses `HEAD` first, falls back to `GET` if no response
- Follows 301, 302, 303, 307, 308 only
- Resolves relative `Location` headers
- Tracks visited URLs to prevent loops

---

### `mailforen.modules.forensic.filemeta.FileMetaExtractor`

File metadata and EXIF extraction. Singleton: `file_meta = FileMetaExtractor()`.

```python
from mailforen.modules.forensic.filemeta import file_meta

result = file_meta.extract(file_path: Path) -> dict
```

**Returns:**
```python
{
    "filename": str,
    "path": str,          # absolute
    "size_bytes": int,
    "size_human": str,    # e.g. "1.5 MB"
    "created": str,       # ISO format from st_ctime
    "modified": str,      # ISO format from st_mtime
    "accessed": str,      # ISO format from st_atime
    "extension": str,     # lowercase suffix
    "exif": dict | None   # only for .jpg/.jpeg/.tiff/.tif
}
```

**On missing file:** `{"error": "File not found"}`

**Note:** No hashing (MD5/SHA256), no MIME detection despite `python-magic` dependency.

---

## Reports

### `mailforen.reports.generator.ReportGenerator`

Multi-format report generation. Singleton: `report_generator = ReportGenerator()`.

```python
from mailforen.reports.generator import report_generator

path = report_generator.generate(case_id: int, format: str = "html") -> Path
```

**Formats:** `"json"`, `"markdown"` / `"md"`, `"html"`, `"pdf"`

**PDF generation:** Tries `weasyprint` first, falls back to `pdfkit` (wkhtmltopdf). On total failure, returns the HTML path instead of raising.

**Output directory:** `~/.mailforen/reports/`

**Filename pattern:** `report_{case_name}_{YYYYMMDD_HHMMSS}.{ext}`

**Report data structure:**
```python
{
    "case": {...},
    "findings": [...],
    "generated_at": "2024-01-15T10:30:00Z",
    "tool": "mailforen v0.1.0"
}
```

---

## Utilities

### `mailforen.utils.validators.Validators`

Input validation helpers. Singleton: `validators = Validators()`.

```python
from mailforen.utils.validators import validators

validators.is_email(email: str) -> bool
validators.is_domain(domain: str) -> bool
validators.is_ip(ip: str) -> bool
validators.is_url(url: str) -> bool
validators.extract_domain_from_email(email: str) -> str | None
```

**Note:** Validators are defined but **not currently used** by the CLI for input validation.