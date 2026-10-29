---
title: HeaderAnalyzer (.eml parsing)
tags: [email, headers, parsing, received-chain]
sourceRefs: [mailforen/modules/email/headers.py]
lastReviewed: 2026-10-29
---

# `HeaderAnalyzer` (`mailforen/modules/email/headers.py`)

Singleton `header_analyzer`. Fully offline — uses `email.parser.BytesParser` with
`policy.default`; never contacts a mail server.

```python
analyze_file(self, file_path: Path) -> Dict
analyze_message(self, msg) -> Dict
```

## Output keys
`from`, `to`, `subject`, `date`, `message_id`, `reply_to`, `return_path`, `received_chain`,
`authentication_results`, `received_spf`, `user_agent`, `x_mailer`, `originating_ips`.
On a parse failure: `{"error": "<exception>"}`.

## Received chain
Iterates `reversed(msg.get_all("Received", []))`, so hop 1 is the **newest/topmost**
Received header and the list reads newest → oldest:
```python
{"hop": len(received_headers) - i, "raw": received}
```

## IP extraction
Regex `\b(?:\d{1,3}\.){3}\d{1,3}\b` over the whole header block — **IPv4 only**, no octet
range validation, no IPv6. Literal `127.0.0.1` and `0.0.0.0` are dropped; duplicates removed
with order-preserving `dict.fromkeys`.

## Gotchas
- `user_agent` is initialised to `None` and never assigned; only `X-Mailer` is captured (as
  `x_mailer`). The `User-Agent` header is not read.
- No risk scoring here — the CLI stores this finding as `risk_level="info"` (see
  [[concepts/risk-levels]]).
- Header analysis is isolated from SPF/DMARC; see [[entities/email-auth-checker]].
