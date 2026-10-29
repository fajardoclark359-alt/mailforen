# Testing

## Overview

- **Framework:** pytest 9.x
- **Coverage:** pytest-cov
- **Async:** pytest-asyncio
- **Hermetic:** Zero network access in tests

Run all tests:
```bash
pytest -q
```

Run with coverage:
```bash
pytest --cov=mailforen --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures, temp data dir isolation
├── test_auth.py             # EmailAuthChecker (DNS stubbed)
├── test_cli.py              # Typer CLI commands (CliRunner)
├── test_ct.py               # CTSearch (HTTP stubbed)
├── test_db.py               # CaseDB CRUD
├── test_domain.py           # DomainIntel (DNS stubbed)
├── test_filemeta.py         # FileMetaExtractor
├── test_headers.py          # HeaderAnalyzer (embedded .eml)
├── test_http.py             # HTTPClient (respx stubbed)
├── test_ip.py               # IPIntel (HTTP stubbed)
├── test_reports.py          # ReportGenerator
├── test_safety.py           # require_unsafe gate
├── test_urltrace.py         # URLTracer (HTTP stubbed)
└── test_validators.py       # Validators
```

## Key Fixtures (conftest.py)

```python
# Isolates data dir before any mailforen import
os.environ.setdefault("MAILFOREN_DATA_DIR", tempfile.mkdtemp(prefix="mailforen-test-"))

# Headless Qt for GUI tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Fixtures
@pytest.fixture
def case_db():          # Fresh CaseDB instance
@pytest.fixture
def patched_db():       # CaseDB with patched db_path
```

## Stubbing Patterns

### DNS (dnspython)
```python
from unittest.mock import patch, MagicMock

def _txt_answer(records):
    answer = []
    for text in records:
        rdata = MagicMock()
        rdata.strings = [text.encode()]
        answer.append(rdata)
    return answer

with patch("dns.resolver.resolve", return_value=_txt_answer(["v=spf1 -all"])):
    result = auth_checker.check_spf("example.com")
```

### HTTP (respx/httpx)
```python
import respx
from httpx import Response

with respx.mock:
    respx.get("https://ipinfo.io/1.1.1.1/json").mock(
        return_value=Response(200, json={"ip": "1.1.1.1", "org": "AS13335 Cloudflare"})
    )
    result = ip_intel.get_asn_info("1.1.1.1")
```

### HTTPClient (tests/test_http.py)
```python
with patch.object(http_client, "get") as mock_get:
    mock_get.return_value = Response(200, text="OK")
    result = http_client.get("https://example.com")
```

## Adding Tests

1. Create `tests/test_<module>.py`
2. Mirror module path: `mailforen/modules/email/auth.py` → `tests/test_auth.py`
3. Use existing stubbing patterns
4. Add fixtures to `conftest.py` if reusable
5. Run: `pytest tests/test_<module>.py -v`

## CI Requirements

GitHub Actions runs on Python 3.11, 3.12, 3.13:
- `ruff check mailforen tests`
- `mypy mailforen`
- `pytest -q --cov=mailforen --cov-report=term-missing:skip-covered`

All must pass for PR merge.

## Coverage Targets

| Module | Target |
|--------|--------|
| Core (config, db, http, logger, safety) | 100% |
| Email modules | 95% |
| Forensic modules | 90% |
| Reports | 95% |
| CLI | 85% (UI-heavy) |
| Validators | 100% |

Current: ~92% overall.