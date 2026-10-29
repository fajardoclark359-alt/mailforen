# mailforen

Advanced OSINT toolkit for email forensics and digital investigations.

## ⚠️ Disclaimer

**For authorized use only.** This tool is intended for legitimate security investigations, phishing incident response, and defensive OSINT. Users must have explicit permission to investigate targets. Use of this tool for unauthorized reconnaissance, harassment, or malicious purposes is strictly prohibited and may be illegal in your jurisdiction.

## Features

- **Email Forensics**: Parse `.eml` headers, analyze authentication (SPF/DMARC/MX), check MX records, trace Received chains
- **Domain & IP Intelligence**: DNS lookups, ASN/org lookup via public IP APIs, Certificate Transparency search
- **URL Tracing**: Safe redirect chain analysis
- **Username Pivoting**: Correlate identities across public sources
- **File Metadata**: Extract EXIF data from images/documents
- **Case Management**: Organize investigations with SQLite-backed case tracking
- **Evidence Export**: Generate reports in Markdown, HTML, PDF, and JSON/SIEM formats
- **Passive-First**: All checks are passive by default; active checks require `--unsafe` flag with explicit confirmation

🚧 **Planned**: DKIM selector lookups, WHOIS/RDAP queries, automated phishing risk scoring — see [CONTRIBUTING.md](CONTRIBUTING.md) if you'd like to help build these.

## Installation

```bash
cd mailforen
pip install -e .
```

## Quick Start

```bash
# Create a case
mailforen case new "Phishing-Incident-001" --target suspicious.example.com

# Analyze email headers
mailforen email headers suspicious.eml

# Check email authentication
mailforen email auth example.com

# Domain intelligence
mailforen domain intel example.com

# IP intelligence
mailforen ip intel 1.1.1.1

# Certificate transparency search
mailforen ct search example.com

# URL redirect trace
mailforen url trace https://bit.ly/example

# Generate report
mailforen report generate --case-id 1 --format html
```

## Safety

- **Passive by default**: No direct connections to target mail servers without `--unsafe`
- **Rate limiting**: Built-in rate limits to avoid overwhelming APIs
- **Evidence logging**: All requests and results are timestamped
- **API key optional**: Works with free public sources; keys only needed for enriched data
- **Configurable timeouts**: Prevents hanging on slow requests

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest -q                    # hermetic test suite (no network access)
ruff check mailforen tests   # lint
```

CI runs the lint and tests on Python 3.11–3.13. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the project layout, architecture notes, and good first issues.

## License

MIT
