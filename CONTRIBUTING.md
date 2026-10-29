# Contributing to mailforen

Thanks for your interest in improving mailforen! This guide covers setting up
a development environment, running the test suite, and submitting changes.

## ⚠️ Ground rule

mailforen is a **defensive** OSINT/forensics tool for **authorized**
investigations only. Contributions must respect the passive-first design:

- No new functionality that contacts target systems without the `--unsafe` gate
- No exploit code, credential attacks, or bulk scanning features
- New network-facing features must be rate-limited, timeout-bounded, and
  log their requests for evidence purposes

See [DISCLAIMER.md](DISCLAIMER.md) for the full policy.

## Development setup

Requires Python 3.11+.

```bash
git clone https://github.com/<your-username>/mailforen.git
cd mailforen
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest -q
```

The test suite is **hermetic**: it performs no network access. DNS is stubbed
(`tests/test_auth.py`, `tests/test_domain.py`), HTTP is stubbed
(`tests/test_urltrace.py`, `tests/test_ct.py`, `tests/test_ip.py`), and the
`MAILFOREN_DATA_DIR` environment variable is pointed at a throwaway directory
in `tests/conftest.py` *before* any `mailforen` import, so module-level
singletons never touch `~/.mailforen`.

If you add a feature, please add tests for it. Keep network stubs in the test
file that uses them; keep cross-test state out by relying on the `case_db` /
`patched_db` fixtures.

## Linting

```bash
ruff check mailforen tests
```

CI runs `ruff check` and `pytest` on Python 3.11, 3.12, and 3.13 — both must
pass before a pull request can be merged.

## Project layout

```
mailforen/
├── core/       # config, SQLite case DB, HTTP client, logging
├── modules/
│   ├── email/      # .eml header analysis, SPF/DMARC/MX checks
│   └── forensic/   # domain/IP/CT intel, URL tracing, file metadata
├── reports/    # Markdown/HTML/JSON/PDF report generation
└── utils/      # validators
tests/          # hermetic pytest suite (mirrors the layout above)
```

## Ideas welcome here

Feature gaps that currently exist between the README and the code — good
first issues, all passive:

- **DKIM lookup** (`mailforen/modules/email/auth.py`): query selector
  `_selector._domainkey.<domain>` TXT records; the CLI docstring already
  promises it
- **WHOIS/RDAP lookups** for the domain module (RDAP preferred: structured,
  rate-friendly)
- **Phishing triage scoring**: turn the per-finding `risk_level` values into
  an explainable weighted score for an email
- **Hop numbering in Received chains**: `header_analyzer` currently numbers
  hops descending from the bottom-most header; verify against RFC 5321
  semantics and make it consistent
- **PDF report backend**: generation currently falls back to HTML when
  neither weasyprint nor wkhtmltopdf is installed

## Submitting changes

1. Fork the repository and create a feature branch from `master`:
   `git checkout -b feat/my-feature`
2. Make your change with focused commits
3. Run `ruff check mailforen tests && pytest -q` locally
4. Push and open a pull request describing **what** changed and **why**
5. Link any related issues

Small, single-purpose pull requests get reviewed and merged faster than
large ones.

## Reporting bugs

Open a [GitHub issue](https://github.com/fajardoclark359-alt/mailforen/issues)
with the command you ran, the unexpected output, and your Python version.
For reports that themselves contain sensitive investigation data, redact
targets and IOCs first — issues are public.
