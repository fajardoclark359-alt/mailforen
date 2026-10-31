---
title: EmailAuthChecker (SPF/DMARC/MX)
tags: [email, spf, dmarc, dns, authentication]
sourceRefs: [mailforen/modules/email/auth.py]
lastReviewed: 2026-10-29
---

# `EmailAuthChecker` (`mailforen/modules/email/auth.py`)

Singleton `auth_checker`. Raw `dnspython` lookups against the system resolvers — no
`pyspf`, no `checkdmarc`, no SMTP conversation, no DKIM.

```python
check_all(self, domain) -> {"domain", "spf", "dmarc", "mx"}
check_spf(self, domain)   -> {"found": bool, "records": [...]} | {"found": False, "error": str}
check_dmarc(self, domain) -> same shape, queried on f"_dmarc.{domain}"
check_mx(self, domain)    -> [{"priority": int, "exchange": str}] sorted by priority
```

## Details
- SPF: `resolve(domain, "TXT")`, keeps records starting with `v=spf1`.
- DMARC: `resolve("_dmarc.<domain>", "TXT")`, keeps records starting with `v=DMARC1`.
- TXT chunks are joined with `b"".join(rdata.strings).decode("utf-8")`.
- MX exchanges have the trailing `.` stripped.
- All DNS failures are swallowed at DEBUG level and expressed as `{"found": False, "error": ...}`.

## DKIM is advertised but absent
The module docstring and the README both claim DKIM checking; there is no `check_dkim` and
no selector lookup anywhere in the codebase. See [[concepts/known-gaps]].

## Where the only real risk rule lives
`mailforen/cli.py::email_auth` maps the result to
```python
"medium" if not spf["found"] or not dmarc["found"] else "low"
```
— the single non-`info` risk decision in the project. See [[concepts/risk-levels]].
