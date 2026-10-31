import socket

import mailforen.modules.forensic.ip as ip_module
from mailforen.modules.forensic.ip import ip_intel


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class TestGetInfo:
    def test_reverse_dns_resolved(self, monkeypatch):
        monkeypatch.setattr(
            ip_module.socket, "gethostbyaddr", lambda ip: ("host.example.com", [], [ip])
        )

        result = ip_intel.get_info("192.0.2.1")

        assert result["ip"] == "192.0.2.1"
        assert result["reverse_dns"] == "host.example.com"
        assert result["ptr"] == "host.example.com"

    def test_reverse_dns_failure(self, monkeypatch):
        def boom(ip):
            raise socket.herror(1, "Unknown host")

        monkeypatch.setattr(ip_module.socket, "gethostbyaddr", boom)

        result = ip_intel.get_info("192.0.2.1")

        assert result["reverse_dns"] is None
        assert result["ptr"] is None


class TestGetAsnInfo:
    def test_successful_lookup(self, monkeypatch):
        class FakeClient:
            def get(self, url):
                assert url == "https://ipinfo.io/192.0.2.1/json"
                return FakeResponse(200, {"org": "AS64496 ExampleNet", "country": "US"})

        monkeypatch.setattr("mailforen.core.http.http_client", FakeClient())

        result = ip_intel.get_asn_info("192.0.2.1")

        assert result["org"] == "AS64496 ExampleNet"

    def test_non_200_returns_empty(self, monkeypatch):
        class FakeClient:
            def get(self, url):
                return FakeResponse(429, {})

        monkeypatch.setattr("mailforen.core.http.http_client", FakeClient())

        assert ip_intel.get_asn_info("192.0.2.1") == {}

    def test_network_error_returns_empty(self, monkeypatch):
        class FakeClient:
            def get(self, url):
                raise ConnectionError("down")

        monkeypatch.setattr("mailforen.core.http.http_client", FakeClient())

        assert ip_intel.get_asn_info("192.0.2.1") == {}
