---
title: Known gaps — README vs code
tags: [gaps, drift, tech-debt, honesty]
sourceRefs: [README.md, README.md, mailforen/, tests/, pyproject.toml]
lastReviewed: 2026-10-29
---

# Known gaps

State of the repo as of 2026-10-29 (branch `master`, 5 commits, dirty tree). Read this before
trusting any feature claim in `README.md` or `docs/index.html`.

## Advertised, not implemented
| Claim (README / docs) | Reality |
|---|---|
| "analyze authentication (SPF/**DKIM**/DMARC)" | No DKIM anywhere; `auth.py` even lacks a `check_dkim` ([email-auth-checker](entities/email-auth-checker.md)) |
| "**WHOIS/RDAP**" lookups | Only raw DNS records — `DomainIntel` has no WHOIS/RDAP ([domain-intel](entities/domain-intel.md)) |
| "Automated risk scoring" | One boolean rule on the auth command ([risk-levels](concepts/risk-levels.md)) |
| "Passive by default; active checks require `--unsafe` with explicit confirmation" | `--unsafe` does not exist; `allow_unsafe` is never read ([passive-first-gating](concepts/passive-first-gating.md)) |
| "SQLite-backed case tracking … evidence" | `requests` table is never written or read ([case-db](entities/case-db.md)) |
| `email headers analyze <file>` / `email auth check <domain>` | No `analyze`/`check` subcommands ([cli](entities/cli.md)) |
| "Username pivoting" via a module | Implemented inline in the CLI by string-building 4 URLs; no network, no module ([cli](entities/cli.md)) |

## Verified defects
- **`url trace` reports ~0 redirects.** `HTTPClient` sets `follow_redirects=True`, so the 3xx
  responses `URLTracer` wants are consumed by httpx ([url-tracer](entities/url-tracer.md)).
- **PDF reports silently become HTML.** `from weasyhtml import HTML` is a typo for
  `weasyprint`, and the failure path returns the HTML path instead of raising
  ([report-generator](entities/report-generator.md)).
- **CT subdomain match is a suffix match** — `notexample.com` counts as a subdomain of
  `example.com` ([ct-search](entities/ct-search.md)).
- **No input validation** before DNS/HTTP: `Validators` exists but is imported-unused in
  `auth.py` and never called by the CLI.
- **No hashing / MIME detection** in `file meta`, despite `python-magic` being a dependency
  ([file-meta-extractor](entities/file-meta-extractor.md)).
- **`user_agent` field in header output is always `None`.**
- **Unused config**: `max_retries`, `rate_limit_delay`, all four API keys.
- **Stale `mailforen.egg-info/`** committed-adjacent build metadata sits in the tree.

## Repository hygiene
- **Zero tests.** `tests/` contains only an empty `__init__.py`. Commit `c207271` is titled
  "Complete implementation with all modules tested" — there is no test in the repository.
- **No CI** of any kind (`.github/`, `.gitlab-ci.yml`, pre-commit all absent).
- **No tool config**: `pytest`, `ruff`, `black`, `mypy` are dev dependencies but have no
  `[tool.*]` sections in `pyproject.toml` and no `pytest.ini`/`tox.ini`.
- **The GUI is uncommitted** — 9 files under `mailforen/gui/` show as `??` while
  `pyproject.toml` already depends on `PySide6` and declares `mailforen-gui`
  ([gui](entities/gui.md)).
- **Version drift**: `pyproject.toml` says `0.2.0`; `core/config.py` UA string,
  `reports/generator.py` tool string, `cli.py version` panel, and `gui/app.py::_version` all
  say `0.1.0`; `mailforen/__init__.py` defines no `__version__`. Single source of truth
  needed before any release.

## Suggested order if you pick this up
1. `__version__` + read it everywhere (mechanical, unblocks packaging).
2. Tests for the offline modules (`headers`, `validators`, `db`, `generator`) — they need no
   network and would have caught the `weasyhtml` typo path.
3. Commit the GUI as its own change, with the risk logic unified (`assess(result)` shared with
   the CLI) — see [[concepts/risk-levels]].
4. Fix `urltrace` by adding `follow_redirects=False` support to [[entities/http-client]].
