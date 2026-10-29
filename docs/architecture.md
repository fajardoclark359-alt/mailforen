# Architecture Overview

High-level architecture of mailforen.

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Passive-First** | All checks are passive by default; `--unsafe` opt-in required for any target contact |
| **Hermetic Testing** | Zero network access in tests; DNS/HTTP stubbed; temp data dir per session |
| **Case-Centric** | Every finding tied to a SQLite case for evidence tracking |
| **Singleton Services** | Config, DB, HTTP, Logger are module-level singletons |
| **No External Deps Required** | Works with only Python stdlib + PyPI deps (no system services) |

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (Typer)                           │
│  version | disclaimer | case | email | domain | ip | ct |  │
│  url | user | file | report                                  │
└─────────────────────────────┬────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  core/config  │     │  core/logger  │     │  core/safety  │
│   Settings    │     │   Logger      │     │ require_unsafe│
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      core/db.CaseDB                         │
│  cases  •  findings  •  (requests - unused)                │
│  SQLite: ~/.mailforen/cases.db                              │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   core/http.HTTPClient                      │
│  rate limiting • proxy • timeout • redirect control         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   email/    │  forensic/  │  forensic/  │  forensic/  │
│  headers    │   domain    │     ip      │     ct      │
└─────────────┴─────────────┴─────────────┴─────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
   .eml parsing   DNS queries   ipinfo.io     crt.sh
   SPF/DMARC/MX   A/AAAA/MX/NS  ASN/geo       subdomains
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                  reports/generator.ReportGenerator          │
│  JSON • Markdown • HTML (Jinja2) • PDF (weasyprint/pdfkit) │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Case Creation
```
mailforen case new "Name" --target X --desc Y
       │
       ▼
CaseDB.create_case() → INSERT INTO cases → returns case_id
```

### 2. Analysis Command (e.g., `email auth example.com`)
```
mailforen email auth example.com --case-id 1
       │
       ▼
EmailAuthChecker.check_all("example.com")
       │
       ├─── DNS TXT query for SPF
       ├─── DNS TXT query for _dmarc.example.com
       └─── DNS MX query for example.com
       │
       ▼
Result dict + risk_level ("medium" if SPF/DMARC missing else "low")
       │
       ▼
CaseDB.add_finding(case_id=1, module="email.auth", input_data="example.com", result=..., risk_level=...)
       │
       ▼
Rich console output + "✓ Added to case 1"
```

### 3. Report Generation
```
mailforen report generate --case-id 1 --format html
       │
       ▼
ReportGenerator.generate(1, "html")
       │
       ├─── CaseDB.get_case(1)
       ├─── CaseDB.get_findings(1)
       │
       ▼
Template rendering (Jinja2 for HTML, f-strings for MD, json.dump for JSON)
       │
       ▼
Write to ~/.mailforen/reports/report_{name}_{timestamp}.html
       │
       ▼
Return Path → console output
```

---

## Module Responsibilities

| Module | Responsibility | External Calls |
|--------|----------------|----------------|
| `core/config` | Settings, env, data dirs | Filesystem (mkdir) |
| `core/db` | SQLite CRUD for cases/findings | SQLite (`~/.mailforen/cases.db`) |
| `core/http` | Rate-limited HTTP client | Any HTTP(S) endpoint |
| `core/logger` | Structured logging | Filesystem (`~/.mailforen/logs/`) |
| `core/safety` | Active-check gate | — |
| `email/headers` | .eml parsing, header extraction | — (stdlib email.parser) |
| `email/auth` | SPF/DMARC/MX via DNS | System DNS resolver |
| `forensic/domain` | DNS record enumeration | System DNS resolver |
| `forensic/ip` | Reverse DNS + ipinfo.io | `https://ipinfo.io` |
| `forensic/ct` | CT log search | `https://crt.sh` |
| `forensic/urltrace` | Redirect chain tracing | Target URLs (HEAD/GET) |
| `forensic/filemeta` | File stats + EXIF | — (stdlib, exifread) |
| `reports/generator` | Multi-format reports | weasyprint / wkhtmltopdf (optional) |

---

## Concurrency Model

- **Single-threaded CLI** — Typer commands run sequentially
- **GUI** — PySide6 with `QThread` workers for background DNS/HTTP
- **HTTPClient** — Not thread-safe; new `httpx.Client` per call
- **CaseDB** — New SQLite connection per method; no connection pooling

---

## Security Boundaries

| Boundary | Protection |
|----------|------------|
| Target contact | `--unsafe` flag + `require_unsafe()` gate (not yet enforced per-module) |
| Rate limiting | `settings.rate_limit_delay` (1s default) per HTTPClient instance |
| Timeouts | `settings.timeout` (30s default) on all HTTP |
| Proxy | `settings.proxy` respected by HTTPClient |
| Input validation | Validators exist but **not used** by CLI |
| Path traversal | `Path` objects, but no explicit sanitization |
| SQL injection | Parameterized queries (f-strings only for table names) |

---

## Extension Points

1. **New forensic module** — Add to `modules/forensic/`, expose singleton, wire into CLI
2. **New report format** — Add method to `ReportGenerator`, handle in `generate()`
3. **New authentication check** — Add to `EmailAuthChecker`, update `check_all()` and CLI
4. **New pivot platform** — Add to `user_pivot_cmd` platforms list
5. **API key integration** — Use `settings.*_api_key` in new modules

---

## Known Architectural Debt

1. **No dependency injection** — Singletons make testing harder (mitigated by temp data dir in conftest)
2. **Foreign keys not enforced** — `PRAGMA foreign_keys=OFF` by default
3. **`requests` table unused** — Schema exists but no request logging
4. **Validators unused** — Defined but CLI doesn't validate inputs
5. **No retry logic** — `max_retries` setting declared but not implemented
6. **GUI risk scoring diverges** — `EmailTab._auth_risk` uses different rules than CLI
7. **Version single-sourced but not everywhere** — `__version__` in `__init__.py`, but `config.py` uses f-string at import time