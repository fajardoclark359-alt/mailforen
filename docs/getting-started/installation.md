# Installation

## Requirements

- **Python** ≥ 3.11
- **pip** ≥ 21.0
- **Git** (for cloning)

Optional system dependencies for PDF generation:
- **weasyprint** — `pip install weasyprint` (requires system libraries: pango, cairo, gdk-pixbuf)
- **wkhtmltopdf** — `apt-get install wkhtmltopdf` (for pdfkit fallback)

## From Source (Recommended)

```bash
git clone https://github.com/ritchegerona/mailforen.git
cd mailforen
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Development Install

Includes test, lint, and type-check dependencies:

```bash
pip install -e ".[dev]"
```

## Verify Installation

```bash
mailforen version
```

Expected output:
```
╭─────────────────────────────── Version ───────────────────────────────╮
│ mailforen v0.1.0                                                      │
│ Advanced OSINT toolkit for email forensics and digital investigations │
│                                                                       │
│ ⚠️  For authorized use only                                           │
╰───────────────────────────────────────────────────────────────────────╯
```

## GUI Installation

The GUI requires PySide6 (installed by default):

```bash
mailforen-gui
```

Or run as module:
```bash
python -m mailforen.gui
```

**Note:** GUI requires a display server (X11/Wayland). For headless testing:
```bash
QT_QPA_PLATFORM=offscreen mailforen-gui
```

---

## Configuration

### Data Directory

Default: `~/.mailforen/`

Contains:
- `cases.db` — SQLite case database
- `logs/mailforen.log` — Debug logs
- `reports/` — Generated reports

Override with `MAILFOREN_DATA_DIR`:
```bash
export MAILFOREN_DATA_DIR=/custom/path
mailforen case new "Test"
```

### Environment Variables

Create `.env` in working directory or export:

```bash
# Debug logging
MAILFOREN_DEBUG=true

# Network
MAILFOREN_TIMEOUT=30
MAILFOREN_RATE_LIMIT_DELAY=1.0
MAILFOREN_PROXY=http://127.0.0.1:8080

# Safety
MAILFOREN_ALLOW_UNSAFE=false

# API Keys (optional, for enriched data)
MAILFOREN_VIRUSTOTAL_API_KEY=...
MAILFOREN_SHODAN_API_KEY=...
MAILFOREN_SECURITYTRAILS_API_KEY=...
MAILFOREN_EMAILREP_API_KEY=...
```

---

## Updating

```bash
cd mailforen
git pull
pip install -e . --upgrade
```

---

## Uninstall

```bash
pip uninstall mailforen
rm -rf ~/.mailforen  # optional: remove data
```