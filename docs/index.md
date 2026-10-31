# mailforen Documentation

**Advanced OSINT toolkit for email forensics and digital investigations.**

---

## ⚠️ For Authorized Use Only

This tool is intended for legitimate security investigations, phishing incident response, and defensive OSINT. Users must have explicit permission to investigate targets. Use for unauthorized reconnaissance, harassment, or malicious purposes is strictly prohibited and may be illegal.

---

## Features

- **Email Forensics** — Parse `.eml` headers, analyze authentication (SPF/DMARC/MX), trace Received chains
- **Domain & IP Intelligence** — DNS lookups, ASN/org lookup via public APIs, Certificate Transparency search
- **URL Tracing** — Safe redirect chain analysis with loop detection
- **Username Pivoting** — Correlate identities across public platforms
- **File Metadata** — Extract EXIF data from images/documents
- **Case Management** — SQLite-backed investigation case tracking
- **Evidence Export** — Reports in Markdown, HTML, PDF, and JSON/SIEM formats
- **Passive-First Design** — All checks passive by default; active checks require `--unsafe` opt-in

---

## Quick Links

| Section | Description |
|---------|-------------|
| [Installation](getting-started/installation.md) | Install mailforen |
| [Quick Start](getting-started/quick-start.md) | Your first investigation in 5 minutes |
| [CLI Reference](cli-reference.md) | Complete command documentation |
| [Usage Guide](usage-guide.md) | Practical workflows and examples |
| [API Reference](api-reference.md) | Python module reference |
| [Architecture](architecture.md) | System design and data flow |
| [Contributing](contributing.md) | Development setup and guidelines |

---

## Installation

```bash
git clone https://github.com/fajardoclark359-alt/mailforen.git
cd mailforen
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

---

## First Investigation

```bash
# 1. Create a case
mailforen case new "Phishing-001" --target suspicious.example.com

# 2. Analyze email
mailforen email headers suspicious.eml --case-id 1
mailforen email auth suspicious.example.com --case-id 1

# 3. Investigate infrastructure
mailforen domain intel suspicious.example.com --case-id 1
mailforen ip intel 203.0.113.42 --case-id 1

# 4. Generate report
mailforen report generate --case-id 1 --format html
```

---

## Project Status

| Component | Status |
|-----------|--------|
| Core CLI | ✅ Stable |
| Test Suite | ✅ 154 tests passing |
| CI/CD | ✅ GitHub Actions (3.11-3.13) |
| PySide6 GUI | ✅ Implemented (untracked) |
| Documentation | 🚧 In progress |

**Version:** 0.1.0  
**License:** MIT  
**Python:** ≥3.11

---

## Community

- **Issues:** [GitHub Issues](https://github.com/fajardoclark359-alt/mailforen/issues)
- **Discussions:** [GitHub Discussions](https://github.com/fajardoclark359-alt/mailforen/discussions)
- **Security:** See [DISCLAIMER.md](disclaimer.md) for reporting

---

## Planned Features

- [ ] DKIM selector lookups
- [ ] WHOIS/RDAP queries
- [ ] Automated phishing risk scoring
- [ ] Improved PDF generation backend
- [ ] Received chain hop numbering per RFC 5321

See [CONTRIBUTING.md](contributing.md) for good first issues.