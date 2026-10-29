---
title: DomainIntel (DNS records)
tags: [dns, domain, osint]
sourceRefs: [mailforen/modules/forensic/domain.py]
lastReviewed: 2026-10-29
---

# `DomainIntel` (`mailforen/modules/forensic/domain.py`)

Singleton `domain_intel`. Pure `dnspython` record harvesting; no WHOIS, no RDAP, no HTTP.

```python
get_all_records(self, domain) -> {"domain", "a", "aaaa", "mx", "ns", "txt", "cname"}
get_a_records(self, domain) -> List[str]
get_aaaa_records(self, domain) -> List[str]
get_mx_records(self, domain) -> [{"priority": int, "host": str}]  # sorted ascending
get_ns_records(self, domain) -> List[str]                          # trailing "." stripped
get_txt_records(self, domain) -> List[str]
get_cname_records(self, domain) -> List[str]                       # trailing "." stripped
```

Every helper returns `[]` and logs at DEBUG on resolver failure, so a fully NXDOMAIN domain
looks identical to one with no records — the caller cannot distinguish the two.

The README advertises WHOIS/RDAP lookups for this module; they are not implemented. See
[[concepts/known-gaps]]. Compare [[entities/email-auth-checker]], which does its own
overlapping TXT queries for SPF/DMARC.
