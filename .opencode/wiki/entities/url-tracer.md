---
title: URLTracer (redirect chains)
tags: [url, redirects, http, bug]
sourceRefs: [mailforen/modules/forensic/urltrace.py, mailforen/core/http.py]
lastReviewed: 2026-10-29
---

# `URLTracer` (`mailforen/modules/forensic/urltrace.py`)

Singleton `url_tracer`.

```python
trace(self, url) -> {"original_url", "redirect_chain", "final_url", "total_redirects"}
```

## Intent
Walk a redirect chain with a hard cap of **10 hops** (`for i in range(10)`), keeping a
`visited` set to break loops. Per hop it issues `HEAD` (falling back to `GET` on `None`),
records `{"step", "url", "status_code"}`, and continues only for
`{301, 302, 303, 307, 308}`, resolving relative `Location` values with `urljoin`.

## Reality: the chain is almost always length 1
`HTTPClient` builds its client with `follow_redirects=True` (see
[[entities/http-client]]), so httpx consumes the 3xx responses internally. `resp.status_code`
is normally the final 2xx and `Location` is absent, so the loop exits after the first hop and
`total_redirects` is `0` even for URLs that redirect several times.

Fixing this requires per-request control over redirect following (e.g. a
`follow_redirects=False` option on `HTTPClient`), not a change inside `URLTracer`.

No response body is downloaded, and there is no content-type or size guard.
