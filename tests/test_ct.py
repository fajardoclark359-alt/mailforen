import pytest

import mailforen.modules.forensic.ct as ct_module
from mailforen.modules.forensic.ct import ct_search


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def http(monkeypatch):
    holder = {}

    def install(response):
        class FakeClient:
            def __init__(self):
                self.requested_url = None

            def get(self, url):
                self.requested_url = url
                if isinstance(response, Exception):
                    raise response
                return response

        client = FakeClient()
        holder["client"] = client
        monkeypatch.setattr(ct_module, "http_client", client)
        return client

    return install


class TestSearch:
    def test_queries_crtsh_json(self, http):
        client = http(FakeResponse(200, []))

        result = ct_search.search("example.com")

        assert client.requested_url == "https://crt.sh/?q=%.example.com&output=json"
        assert result["certificates_found"] == 0
        assert result["unique_subdomains"] == []

    def test_extracts_unique_subdomains(self, http):
        certs = [
            {"name_value": "sub1.example.com\nexample.com"},
            {"name_value": "SUB1.EXAMPLE.COM"},          # duplicate, different case
            {"name_value": "mail.example.com\n*.wild.example.com"},  # wildcard excluded
            {"name_value": "unrelated.example.org"},     # does not end with domain
            {"name_value": "sub2.example.com\nsub2.example.com"},    # dup within cert
        ]
        http(FakeResponse(200, certs))

        result = ct_search.search("example.com")

        assert result["certificates_found"] == 5
        assert result["unique_subdomains"] == [
            "example.com", "mail.example.com", "sub1.example.com", "sub2.example.com",
        ]
        assert result["raw_count"] == 5

    def test_non_200_returns_error(self, http):
        http(FakeResponse(502, []))

        result = ct_search.search("example.com")

        assert result == {"domain": "example.com", "error": "HTTP 502"}

    def test_no_response_returns_error(self, http, monkeypatch):
        class DeadClient:
            def get(self, url):
                return None

        monkeypatch.setattr(ct_module, "http_client", DeadClient())

        result = ct_search.search("example.com")

        assert result == {"domain": "example.com", "error": "HTTP None"}

    def test_exception_returns_error(self, http):
        http(RuntimeError("boom"))

        result = ct_search.search("example.com")

        assert result["domain"] == "example.com"
        assert "boom" in result["error"]

    def test_missing_name_value_tolerated(self, http):
        http(FakeResponse(200, [{"other_field": "x"}, {}]))

        result = ct_search.search("example.com")

        assert result["unique_subdomains"] == []
        assert result["certificates_found"] == 2
