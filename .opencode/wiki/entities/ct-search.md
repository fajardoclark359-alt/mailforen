---
title: CTSearch (crt.sh certificate transparency)
tags: [ct, tls, subdomains, osint, external-api]
sourceRefs: [mailforen/modules/forensic/ct.py]
lastReviewed: 2026-10-29
---

# `CTSearch` (`mailforen/modules/forensic/ct.py`)

Singleton `ct_search`. One method:

```python
search(self, domain) -> {
    "domain", "certificates_found": int, "unique_subdomains": List[str], "raw_count": int
}
```

Calls `GET https://crt.sh/?q=%.{domain}&output=json` through [[entities/http-client]].

## Processing
For every certificate, `name_value` is split on newlines, lowercased, stripped, and kept when
`"*" not in name and name.endswith(domain)`. Wildcards are dropped, results de-duplicated and
sorted.

**Suffix-match bug:** `endswith(domain)` means `notexample.com` is accepted as a subdomain of
`example.com`. Compare against a strict `== domain or endswith("." + domain)` if this ever
matters for reporting accuracy.

## Failure shape
Non-200 → `{"domain", "error": "HTTP <code>"}`; exception → `{"domain", "error": ...}`.
The CLI prints the first 50 subdomains then "... and N more" ([[entities/cli]]).
