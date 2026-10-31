---
title: Settings and data locations
tags: [config, pydantic-settings, paths]
sourceRefs: [mailforen/core/config.py]
lastReviewed: 2026-10-29
---

# `Settings` (`mailforen/core/config.py`)

```python
class Settings(BaseSettings):          # pydantic-settings, legacy `class Config`
    app_name: str = "mailforen"
    data_dir: Path = Path.home() / ".mailforen"
    debug: bool = False
    user_agent: str = "mailforen/0.1.0 (OSINT Research Tool)"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    proxy: Optional[str] = None
    allow_unsafe: bool = False
    virustotal_api_key / shodan_api_key / securitytrails_api_key / emailrep_api_key: Optional[str]
```
Module-level singleton `settings = Settings()`. Importing the module **creates
`settings.data_dir`** as a side effect (`mkdir(parents=True, exist_ok=True)`).

Configuration comes from `MAILFOREN_*` environment variables (prefix `MAILFOREN_`) and an
optional `.env` in the current working directory.

## On-disk layout
| Artifact | Path |
|---|---|
| data root | `$MAILFOREN_DATA_DIR` → default `~/.mailforen` |
| cases | `<data_dir>/cases.db` (see [[entities/case-db]]) |
| logs | `<data_dir>/logs/mailforen.log` |
| reports | `<data_dir>/reports/` (see [[entities/report-generator]]) |

## Declared but unused
`max_retries`, `rate_limit_delay`, `proxy` (only [[entities/http-client]] reads `proxy`),
`allow_unsafe` (see [[concepts/passive-first-gating]]), and all four API keys are never read
by any non-GUI module — no VirusTotal/Shodan/SecurityTrails/EmailRep integration exists.

The `user_agent` string hardcodes `0.1.0` while `pyproject.toml` says `0.2.0`; see
[[concepts/known-gaps]].
