# Project Layout

## Repository Structure

```
mailforen/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── .opencode/
│   ├── wiki/                   # Internal knowledge base (gitignored)
│   └── rag_db/                 # OpenCodeRAG vector index
├── docs/                       # This documentation (MkDocs)
│   ├── getting-started/
│   ├── development/
│   ├── reference/
│   ├── cli-reference.md
│   ├── api-reference.md
│   ├── architecture.md
│   ├── usage-guide.md
│   └── index.md
├── tests/                      # Hermetic pytest suite
│   ├── conftest.py
│   ├── test_*.py
├── mailforen/                  # Main package
│   ├── __init__.py             # __version__ = "0.1.0"
│   ├── cli.py                  # Typer CLI (~393 LOC)
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── db.py               # CaseDB (SQLite)
│   │   ├── http.py             # HTTPClient (httpx + rate limit)
│   │   ├── logger.py           # Rich + file logging
│   │   └── safety.py           # require_unsafe gate
│   ├── modules/
│   │   ├── email/
│   │   │   ├── headers.py      # HeaderAnalyzer
│   │   │   └── auth.py         # EmailAuthChecker (SPF/DMARC/MX)
│   │   └── forensic/
│   │       ├── domain.py       # DomainIntel (DNS)
│   │       ├── ip.py           # IPIntel (ipinfo.io)
│   │       ├── ct.py           # CTSearch (crt.sh)
│   │       ├── urltrace.py     # URLTracer
│   │       └── filemeta.py     # FileMetaExtractor (EXIF)
│   ├── reports/
│   │   └── generator.py        # ReportGenerator (Jinja2, weasyprint, pdfkit)
│   ├── utils/
│   │   └── validators.py       # Input validators
│   └── gui/                    # PySide6 desktop app
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── main_window.py
│       ├── tabs.py
│       ├── components.py
│       ├── state.py
│       ├── workers.py
│       └── theme.py
├── pyproject.toml              # Build config, deps, tooling
├── README.md
├── CONTRIBUTING.md
├── DISCLAIMER.md
├── LICENSE
├── mkdocs.yml                  # Documentation config
└── .gitignore
```

---

## Module Responsibilities

| Path | Purpose | Key Exports |
|------|---------|-------------|
| `mailforen/__init__.py` | Version | `__version__` |
| `mailforen/cli.py` | CLI entry point | `app` (Typer) |
| `mailforen/core/config.py` | Configuration | `settings` (Settings) |
| `mailforen/core/db.py` | Case database | `db` (CaseDB) |
| `mailforen/core/http.py` | HTTP client | `http_client` (HTTPClient) |
| `mailforen/core/logger.py` | Logging | `logger`, `setup_logger` |
| `mailforen/core/safety.py` | Active-check gate | `require_unsafe`, `UnsafeModeRequired` |
| `mailforen/modules/email/headers.py` | .eml parsing | `header_analyzer` (HeaderAnalyzer) |
| `mailforen/modules/email/auth.py` | SPF/DMARC/MX | `auth_checker` (EmailAuthChecker) |
| `mailforen/modules/forensic/domain.py` | DNS records | `domain_intel` (DomainIntel) |
| `mailforen/modules/forensic/ip.py` | IP intelligence | `ip_intel` (IPIntel) |
| `mailforen/modules/forensic/ct.py` | Cert transparency | `ct_search` (CTSearch) |
| `mailforen/modules/forensic/urltrace.py` | URL redirects | `url_tracer` (URLTracer) |
| `mailforen/modules/forensic/filemeta.py` | File/EXIF metadata | `file_meta` (FileMetaExtractor) |
| `mailforen/reports/generator.py` | Report generation | `report_generator` (ReportGenerator) |
| `mailforen/utils/validators.py` | Validation helpers | `validators` (Validators) |
| `mailforen/gui/*.py` | Desktop GUI | `main()` in `app.py` |

---

## Data Locations

| Artifact | Default Path | Override |
|----------|--------------|----------|
| Data root | `~/.mailforen/` | `MAILFOREN_DATA_DIR` |
| SQLite DB | `~/.mailforen/cases.db` | — |
| Logs | `~/.mailforen/logs/mailforen.log` | — |
| Reports | `~/.mailforen/reports/` | — |

---

## Entry Points

| Script | Module | Function |
|--------|--------|----------|
| `mailforen` | `mailforen.cli` | `app` |
| `mailforen-gui` | `mailforen.gui.app` | `main` |

Defined in `pyproject.toml` `[project.scripts]`.

---

## Dependencies

### Runtime (`dependencies`)

| Package | Purpose |
|---------|---------|
| `typer[all]` | CLI framework |
| `rich` | Terminal formatting |
| `httpx[http2]` | HTTP client |
| `dnspython` | DNS queries |
| `pydantic` + `pydantic-settings` | Config validation |
| `jinja2` | HTML report templates |
| `python-dateutil` | Date parsing |
| `publicsuffix2` | Domain parsing |
| `tldextract` | TLD extraction |
| `eml-parser` | .eml parsing |
| `pyspf` | SPF validation (unused, kept for future) |
| `checkdmarc` | DMARC validation (unused, kept for future) |
| `exifread` | EXIF extraction |
| `python-magic` | MIME detection (unused) |
| `pdfkit` | PDF via wkhtmltopdf |
| `PySide6` | Desktop GUI |

### Development (`optional-dependencies.dev`)

| Package | Purpose |
|---------|---------|
| `pytest` + `pytest-asyncio` + `pytest-cov` | Testing |
| `black` | Formatting |
| `ruff` | Linting |
| `mypy` | Type checking |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Build, deps, tool config (ruff, mypy, pytest) |
| `mkdocs.yml` | Documentation site config |
| `.gitignore` | Git ignores |
| `.env` (local) | Environment overrides |
| `DISCLAIMER.md` | Legal/ethical notice |
| `CONTRIBUTING.md` | Contribution guide |
| `LICENSE` | MIT license |

---

## GUI Structure (mailforen/gui/)

```
gui/
├── app.py              # QApplication bootstrap, main()
├── main_window.py      # MainWindow: sidebar + QStackedWidget
├── tabs.py             # CasesTab, EmailTab, DomainTab, IPTab, URLTab
├── components.py       # JsonView, PathPicker, CaseSelector, ToolTab
├── state.py            # AppState (QObject, signals)
├── workers.py          # Worker(QThread), WorkerPool
├── theme.py            # Dark palette + QSS
├── __main__.py         # python -m mailforen.gui
└── __init__.py         # Package init
```

**Key patterns:**
- `ToolTab` base class with `assess_risk()`, `add_run_button()`, `_run_action()`, `_on_result()`, `_save_finding()`
- `Worker` runs module calls in background thread, emits `finished(dict)` signal
- `AppState` holds `selected_case_id` and emits `case_changed(int)`
- `QT_QPA_PLATFORM=offscreen` for headless testing