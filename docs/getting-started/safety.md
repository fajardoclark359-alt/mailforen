# Safety & Ethics

## Authorized Use Only

**mailforen is for authorized investigations only.** You must have explicit, documented permission to investigate any target. Unauthorized use may violate:

- Computer Fraud and Abuse Act (US)
- Computer Misuse Act (UK)
- GDPR (EU) — personal data processing
- Local cybercrime laws

---

## Passive-First Design

| Check Type | Default | Requires `--unsafe` |
|------------|---------|---------------------|
| DNS queries (SPF, DMARC, MX, A, etc.) | ✅ Passive | No |
| Certificate Transparency (crt.sh) | ✅ Passive | No |
| ipinfo.io ASN/geo lookup | ✅ Passive | No |
| URL redirect tracing (HEAD/GET) | ✅ Passive* | No |
| Username pivot (URL construction) | ✅ Passive | No |
| File metadata (local) | ✅ Passive | No |
| **Future: SMTP VRFY/EXPN** | ❌ Active | **Yes** |
| **Future: Direct target contact** | ❌ Active | **Yes** |

*URL tracing contacts the URL endpoint but follows standard HTTP semantics (no exploitation).

---

## Safety Features

### Rate Limiting
- Default: 1 request/second per HTTPClient instance
- Configurable: `MAILFOREN_RATE_LIMIT_DELAY`
- Applies to all HTTP calls (APIs, URL tracing)

### Timeouts
- Default: 30 seconds
- Configurable: `MAILFOREN_TIMEOUT`
- Prevents hanging on slow/unresponsive targets

### Evidence Logging
- All findings timestamped and stored in SQLite
- HTTP requests logged (when implemented)
- Reports include generation timestamp and tool version

### No Credential Handling
- mailforen never stores or transmits credentials
- API keys read from environment only
- No authentication mechanisms implemented

---

## Unsafe Mode

```bash
mailforen --unsafe email auth example.com
```

```
⚠ Unsafe mode enabled: active checks may contact targets directly.
```

**Currently:** No active checks implemented. The flag exists as a gate for future features that may contact target systems directly (e.g., SMTP verification, web application scanning).

**When active checks are added:** They will call `require_unsafe("action_name")` which raises `UnsafeModeRequired` unless `--unsafe` was passed.

---

## Data Handling

### What We Store Locally
- Case metadata (name, target, description)
- Findings (module, input, results, risk level, tags, notes)
- Logs (debug level to file, info to console)

### What We Don't Store
- No cloud sync
- No telemetry
- No automatic updates
- No target data beyond what you explicitly analyze

### Data Retention
- You control `~/.mailforen/` — delete anytime
- `mailforen case delete` — not yet implemented (manual SQLite)

---

## Reporting Security Issues

Found a vulnerability in mailforen itself?

1. **Do not** open a public issue
2. Email: security@[project-domain] (or GitHub Security Advisories)
3. Include: description, reproduction steps, impact assessment

---

## Ethical Guidelines for Investigators

1. **Scope** — Define and document investigation scope before starting
2. **Minimize** — Collect only data relevant to the investigation
3. **Document** — Record all steps, tools, and timestamps
4. **Preserve** — Maintain chain of custody for evidence
5. **Report** — Share findings only with authorized stakeholders
6. **Destroy** — Securely delete data when investigation concludes

---

## Disclaimer

See [DISCLAIMER.md](../disclaimer.md) for the full legal disclaimer.

> **TL;DR:** You are responsible for your use of this tool. The authors accept no liability.