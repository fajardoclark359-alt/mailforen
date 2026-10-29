---
title: HTTPClient
tags: [http, httpx, networking]
sourceRefs: [mailforen/core/http.py]
lastReviewed: 2026-10-29
---

# `HTTPClient` (`mailforen/core/http.py`)

Singleton `http_client = HTTPClient()`. Two methods:

```python
get(self, url, params=None, **kwargs) -> Optional[httpx.Response]
head(self, url, **kwargs)               -> Optional[httpx.Response]
```

Each call constructs a **new** `httpx.Client` with:
- `headers = {"User-Agent": settings.user_agent, "Accept": "*/*"}`
- `timeout = settings.timeout`
- `follow_redirects = True`
- `proxy=settings.proxy` only when configured

Any exception is logged at ERROR (`HTTP GET failed for <url>: <e>`) and `None` is returned —
callers must handle `None`.

## What it does not do
Despite `Settings` declaring the knobs, there is **no rate limiting, no retry, no response
size cap, and no scheme/host allow-list**. Outbound HTTP is unrestricted: any URL handed to
it will be fetched (used by [[entities/ip-intel]], [[entities/ct-search]],
[[entities/url-tracer]]).

`follow_redirects=True` is the root cause of the redirect-tracing bug documented in
[[entities/url-tracer]].
