---
title: IPIntel (reverse DNS + ipinfo)
tags: [ip, dns, osint, external-api]
sourceRefs: [mailforen/modules/forensic/ip.py]
lastReviewed: 2026-10-29
---

# `IPIntel` (`mailforen/modules/forensic/ip.py`)

Singleton `ip_intel`.

```python
get_info(self, ip) -> {"ip", "reverse_dns", "ptr"}
reverse_dns(self, ip) -> Optional[str]     # socket.gethostbyaddr(ip)[0]
get_asn_info(self, ip) -> Dict             # httpx GET https://ipinfo.io/{ip}/json
```

## Behaviour
- `ptr` is a duplicate of `reverse_dns`, set only when a PTR exists.
- The only external call is **`https://ipinfo.io/{ip}/json` with no API key**; the JSON body
  is returned as-is on HTTP 200, otherwise `{}`. Rate limits and ToS are therefore whatever
  ipinfo.io applies to anonymous traffic.
- `get_asn_info` is merged into the finding only by the CLI (`{**results, **asn_info}` in
  [[entities/cli]]); called standalone it is not persisted.
- `shodan_api_key` exists in [[entities/core-config]] but no Shodan lookup is implemented.

No input validation is performed before the lookup — `ip` is passed straight to
`socket.gethostbyaddr` and into the URL path.
