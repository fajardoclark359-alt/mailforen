# Changelog

All notable changes to mailforen.

## [0.1.0] - 2026-10-29

### Added
- Comprehensive test suite (154 tests, hermetic, no network)
- GitHub Actions CI (ruff, mypy, pytest on Python 3.11-3.13)
- `--unsafe` global flag and `require_unsafe()` safety gate
- Rate limiting in `HTTPClient` (`settings.rate_limit_delay`)
- Single-sourced version from `mailforen.__version__`
- Fixed URL tracer: `HEAD` no longer follows redirects
- Fixed PDF generation: `weasyprint` import (was `weasyhtml`)
- Corrected README CLI examples to match actual commands
- CONTRIBUTING.md and MIT LICENSE
- PySide6 GUI (9 files, ~1380 LOC)
- MkDocs documentation site
- OpenCodeRAG plugin upgraded to 2.12.2

### Changed
- `pyproject.toml`: dynamic version, pytest-cov, ruff/mypy config
- `extract_domain_from_email()`: robust display-name/angle-bracket handling
- `ReportGenerator`: uses `__version__`, ISO timestamps with Z suffix
- `HTTPClient.head()`: `follow_redirects=False` for manual redirect tracing

### Fixed
- Version inconsistency (all now 0.1.0 via `__version__`)
- weasyprint import typo in PDF generation
- README command syntax drift
- `requests` table schema existed but was never used (still unused)

---

## [0.0.1] - 2026 (Initial Scaffold)

### Added
- Core modules: config, db, http, logger
- Email modules: headers, auth (SPF/DMARC/MX)
- Forensic modules: domain, ip, ct, urltrace, filemeta
- Reports: generator (JSON, MD, HTML, PDF)
- CLI with case management and analysis commands
- SQLite case database with findings tracking
- Basic documentation (README, DISCLAIMER)

---

## Upcoming

See [CONTRIBUTING.md](../CONTRIBUTING.md#ideas-welcome-here) for planned features:

- DKIM selector lookups
- WHOIS/RDAP queries
- Automated phishing risk scoring
- Improved PDF generation backend
- Received chain hop numbering per RFC 5321