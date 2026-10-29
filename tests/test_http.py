"""Regression tests for core.http against a real httpx client.

These use httpx.MockTransport injected under a stubbed httpx.Client so the
actual HTTPClient wiring (headers, timeout, follow_redirects) is exercised
end-to-end. They exist because the URL tracer's manual hop-following breaks
silently if the client follows redirects itself.
"""
import httpx
import pytest

import mailforen.core.http as http_module
from mailforen.core.http import HTTPClient


@pytest.fixture
def patched_client(monkeypatch):
    """Wrap httpx.Client so every instance created by HTTPClient gets a
    MockTransport; records the kwargs each client was created with."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/redirect":
            return httpx.Response(
                301, headers={"Location": "https://final.example/landing"}
            )
        return httpx.Response(200, json={"ok": True})

    created_kwargs = []
    real_client = http_module.httpx.Client

    def tracking_client(**kwargs):
        created_kwargs.append(kwargs)
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(**kwargs)

    monkeypatch.setattr(http_module.httpx, "Client", tracking_client)
    return created_kwargs


class TestHeadRedirectPolicy:
    def test_head_does_not_follow_redirects(self, patched_client):
        client = HTTPClient()

        resp = client.head("https://a.example/redirect")

        assert resp is not None
        assert resp.status_code == 301
        assert resp.headers["Location"] == "https://final.example/landing"
        # The contract under test: tracer callers must see raw 3xx
        assert patched_client[0]["follow_redirects"] is False

    def test_get_follows_redirects(self, patched_client):
        client = HTTPClient()

        resp = client.get("https://a.example/redirect")

        assert resp is not None
        assert resp.status_code == 200          # landed on the target
        assert patched_client[0]["follow_redirects"] is True


class TestClientDefaults:
    def test_user_agent_header(self, patched_client):
        client = HTTPClient()

        client.head("https://a.example/")

        assert patched_client[0]["headers"]["User-Agent"].startswith("mailforen/")

    def test_network_error_returns_none(self, monkeypatch):
        def failing_client(**kwargs):
            raise httpx.ConnectError("refused")

        monkeypatch.setattr(http_module.httpx, "Client", failing_client)

        assert HTTPClient().head("https://unreachable.example/") is None
        assert HTTPClient().get("https://unreachable.example/") is None
