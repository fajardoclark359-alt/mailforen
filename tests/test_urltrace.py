import pytest

import mailforen.modules.forensic.urltrace as urltrace_module
from mailforen.modules.forensic.urltrace import url_tracer


class FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


class StubClient:
    """Stub for core.http.http_client driven by a url -> response map."""

    def __init__(self, responses):
        self.responses = responses
        self.head_calls = []
        self.get_calls = []

    def head(self, url, **kwargs):
        self.head_calls.append(url)
        return self._lookup(url)

    def get(self, url, **kwargs):
        self.get_calls.append(url)
        return self._lookup(url)

    def _lookup(self, url):
        entry = self.responses.get(url)
        if entry is None:
            raise ConnectionError(f"no route for {url}")
        if isinstance(entry, Exception):
            raise entry
        return entry


@pytest.fixture
def stub(monkeypatch):
    holder = {}

    def install(responses):
        client = StubClient(responses)
        holder["client"] = client
        monkeypatch.setattr(urltrace_module, "http_client", client)
        return client

    return install


class TestTrace:
    def test_no_redirect_single_hop(self, stub):
        client = stub({"https://a.example/": FakeResponse(200)})

        result = url_tracer.trace("https://a.example/")

        assert result["redirect_chain"] == [
            {"step": 1, "url": "https://a.example/", "status_code": 200}
        ]
        assert result["final_url"] == "https://a.example/"
        assert result["total_redirects"] == 0
        assert client.head_calls == ["https://a.example/"]
        assert client.get_calls == []

    def test_head_returns_none_falls_back_to_get(self, stub, monkeypatch):
        class HeadlessClient:
            def __init__(self):
                self.get_calls = []

            def head(self, url, **kwargs):
                return None

            def get(self, url, **kwargs):
                self.get_calls.append(url)
                return FakeResponse(200)

        client = HeadlessClient()
        monkeypatch.setattr(urltrace_module, "http_client", client)

        result = url_tracer.trace("https://a.example/")

        assert result["redirect_chain"][0]["status_code"] == 200
        assert result["total_redirects"] == 0
        assert client.get_calls == ["https://a.example/"]

    def test_both_head_and_get_none_stops(self, stub, monkeypatch):
        class DeadClient:
            def head(self, url, **kwargs):
                return None

            def get(self, url, **kwargs):
                return None

        monkeypatch.setattr(urltrace_module, "http_client", DeadClient())

        result = url_tracer.trace("https://a.example/")

        assert result["redirect_chain"] == []
        assert result["final_url"] == "https://a.example/"
        assert result["total_redirects"] == 0

    def test_absolute_redirect_chain(self, stub):
        stub({
            "https://bit.ly/x": FakeResponse(301, {"Location": "https://evil.example/final"}),
            "https://evil.example/final": FakeResponse(200),
        })

        result = url_tracer.trace("https://bit.ly/x")

        assert [hop["url"] for hop in result["redirect_chain"]] == [
            "https://bit.ly/x", "https://evil.example/final",
        ]
        assert result["final_url"] == "https://evil.example/final"
        assert result["total_redirects"] == 1

    def test_relative_redirect_resolved(self, stub):
        stub({
            "https://a.example/start": FakeResponse(302, {"Location": "/landing?x=1"}),
            "https://a.example/landing?x=1": FakeResponse(200),
        })

        result = url_tracer.trace("https://a.example/start")

        assert result["final_url"] == "https://a.example/landing?x=1"

    def test_redirect_without_location_stops(self, stub):
        stub({"https://a.example/": FakeResponse(301)})

        result = url_tracer.trace("https://a.example/")

        assert len(result["redirect_chain"]) == 1
        assert result["final_url"] == "https://a.example/"

    def test_redirect_loop_terminates(self, stub):
        stub({
            "https://a.example/1": FakeResponse(302, {"Location": "https://a.example/2"}),
            "https://a.example/2": FakeResponse(302, {"Location": "https://a.example/1"}),
        })

        result = url_tracer.trace("https://a.example/1")

        urls = [hop["url"] for hop in result["redirect_chain"]]
        assert urls == ["https://a.example/1", "https://a.example/2"]
        assert result["final_url"] == "https://a.example/2"

    def test_max_ten_hops(self, stub):
        responses = {}
        for i in range(12):
            responses[f"https://a.example/{i}"] = FakeResponse(
                302, {"Location": f"https://a.example/{i + 1}"}
            )
        stub(responses)

        result = url_tracer.trace("https://a.example/0")

        assert len(result["redirect_chain"]) == 10  # capped loop
        assert result["final_url"] == "https://a.example/9"

    def test_unreachable_url_returns_error(self, stub):
        stub({})  # nothing routable -> head raises

        result = url_tracer.trace("https://unreachable.example/")

        assert "error" in result
        assert result["original_url"] == "https://unreachable.example/"
