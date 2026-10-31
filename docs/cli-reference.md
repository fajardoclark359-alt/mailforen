# CLI Reference

Complete command reference for the `mailforen` CLI toolkit.

## Global Options

| Option | Description |
|--------|-------------|
| `--unsafe` | Enable active checks that may contact targets directly (requires explicit confirmation) |
| `--help` | Show help message and exit |

## Command Tree

```
mailforen [OPTIONS] COMMAND [ARGS]...
```

### Subcommands

- `case` - Case management
- `email` - Email forensics and analysis
- `domain` - Domain intelligence
- `ip` - IP intelligence
- `ct` - Certificate Transparency
- `url` - URL analysis and tracing
- `user` - Username/identity pivoting
- `file` - File metadata analysis
- `report` - Report generation
- `version` - Show version information
- `disclaimer` - Show disclaimer

---

## `mailforen version`

Show version information.

```bash
mailforen version
```

**Output:** Rich panel displaying version and disclaimer notice.

---

## `mailforen disclaimer`

Show the project disclaimer.

```bash
mailforen disclaimer
```

**Output:** Contents of `DISCLAIMER.md`.

---

## `mailforen case` — Case Management

### `case new`

Create a new investigation case.

```bash
mailforen case new NAME [OPTIONS]
```

**Arguments:**
- `NAME` (required) — Case name (must be unique)

**Options:**
- `-t, --target TEXT` — Target domain, email, or IP
- `-d, --desc TEXT` — Case description

**Example:**
```bash
mailforen case new "Phishing-2024-001" --target suspicious.example.com --desc "Phishing campaign targeting finance dept"
```

### `case list`

List all cases.

```bash
mailforen case list
```

**Output:** Rich table with columns: ID, Name, Target, Status, Created.

### `case show`

Show details for a specific case.

```bash
mailforen case show CASE_ID
```

**Arguments:**
- `CASE_ID` (required) — Numeric case ID

**Output:** Case details with findings table (risk levels color-coded: high=red, medium=yellow, low=green, info=cyan).

---

## `mailforen email` — Email Forensics

### `email headers`

Parse and analyze `.eml` file headers.

```bash
mailforen email headers FILE [OPTIONS]
```

**Arguments:**
- `FILE` (required) — Path to `.eml` file

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:**
- From, To, Subject, Date, Message-ID, Reply-To, Return-Path
- Received chain (hop-by-hop, newest first)
- Authentication-Results header
- Received-SPF header
- X-Mailer
- Originating IPs (extracted from Received headers, loopback excluded)

**Example:**
```bash
mailforen email headers suspicious.eml --case-id 1
```

### `email auth`

Check email authentication (SPF, DMARC, MX) for a domain.

```bash
mailforen email auth DOMAIN [OPTIONS]
```

**Arguments:**
- `DOMAIN` (required) — Domain to check

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:** SPF records, DMARC policy, MX records with priorities.

**Risk Assessment:**
- `medium` — SPF or DMARC missing
- `low` — Both SPF and DMARC present

**Example:**
```bash
mailforen email auth example.com --case-id 1
```

---

## `mailforen domain` — Domain Intelligence

### `domain intel`

Gather DNS records for a domain.

```bash
mailforen domain intel DOMAIN [OPTIONS]
```

**Arguments:**
- `DOMAIN` (required) — Domain to query

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:** A, AAAA, MX, NS, TXT, CNAME records.

**Example:**
```bash
mailforen domain intel example.com --case-id 1
```

---

## `mailforen ip` — IP Intelligence

### `ip intel`

Gather intelligence for an IP address.

```bash
mailforen ip intel IP [OPTIONS]
```

**Arguments:**
- `IP` (required) — IP address (IPv4 or IPv6)

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:**
- Reverse DNS (PTR)
- ASN info via ipinfo.io (org, ASN, country, etc.)
- Geolocation data

**Example:**
```bash
mailforen ip intel 1.1.1.1 --case-id 1
```

---

## `mailforen ct` — Certificate Transparency

### `ct search`

Search Certificate Transparency logs via crt.sh.

```bash
mailforen ct search DOMAIN [OPTIONS]
```

**Arguments:**
- `DOMAIN` (required) — Domain to search for

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:** Unique subdomains found in certificates (limited to 50 displayed, with count of additional).

**Example:**
```bash
mailforen ct search example.com --case-id 1
```

---

## `mailforen url` — URL Analysis

### `url trace`

Trace URL redirect chain safely.

```bash
mailforen url trace URL [OPTIONS]
```

**Arguments:**
- `URL` (required) — URL to trace

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:** Redirect chain with step, status code, and URL. Max 10 hops.

**Example:**
```bash
mailforen url trace https://bit.ly/example --case-id 1
```

---

## `mailforen user` — Username Pivoting

### `user pivot`

Generate potential profile URLs for a username across platforms.

```bash
mailforen user pivot USERNAME [OPTIONS]
```

**Arguments:**
- `USERNAME` (required) — Username to pivot on

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Platforms checked:** GitHub, Twitter/X, Instagram, Reddit

**Note:** This performs **passive URL construction only** — no network requests are made.

**Example:**
```bash
mailforen user pivot johndoe --case-id 1
```

---

## `mailforen file` — File Metadata

### `file meta`

Extract file metadata and EXIF data.

```bash
mailforen file meta FILE [OPTIONS]
```

**Arguments:**
- `FILE` (required) — Path to file

**Options:**
- `-c, --case-id INTEGER` — Associate findings with a case

**Output:**
- Filename, size (human-readable), timestamps (created, modified, accessed)
- EXIF data (for JPEG/TIFF files only)

**Example:**
```bash
mailforen file meta evidence.jpg --case-id 1
```

---

## `mailforen report` — Report Generation

### `report generate`

Generate an investigation report.

```bash
mailforen report generate [OPTIONS]
```

**Options:**
- `-c, --case-id INTEGER` (required) — Case ID to generate report for
- `-f, --format [html|markdown|md|pdf|json]` — Output format (default: html)

**Output:** Report file saved to `~/.mailforen/reports/`

**Example:**
```bash
mailforen report generate --case-id 1 --format html
mailforen report generate --case-id 1 --format pdf
mailforen report generate --case-id 1 --format json
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, missing file, case not found, etc.) |

---

## Environment Variables

All settings can be configured via environment variables with the `MAILFOREN_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAILFOREN_DATA_DIR` | `~/.mailforen` | Data directory (cases.db, logs, reports) |
| `MAILFOREN_DEBUG` | `false` | Enable debug logging |
| `MAILFOREN_TIMEOUT` | `30` | HTTP timeout in seconds |
| `MAILFOREN_RATE_LIMIT_DELAY` | `1.0` | Minimum delay between requests (seconds) |
| `MAILFOREN_PROXY` | — | HTTP proxy URL |
| `MAILFOREN_ALLOW_UNSAFE` | `false` | Enable unsafe mode (same as `--unsafe`) |
| `MAILFOREN_VIRUSTOTAL_API_KEY` | — | VirusTotal API key |
| `MAILFOREN_SHODAN_API_KEY` | — | Shodan API key |
| `MAILFOREN_SECURITYTRAILS_API_KEY` | — | SecurityTrails API key |
| `MAILFOREN_EMAILREP_API_KEY` | — | EmailRep API key |

Can also be set in a `.env` file in the current working directory.