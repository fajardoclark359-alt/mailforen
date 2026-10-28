import pytest

import mailforen.modules.forensic.domain as domain_module
from mailforen.modules.forensic.domain import domain_intel


class FakeTxt:
    def __init__(self, text):
        self.strings = [text.encode()]


class FakeMx:
    def __init__(self, preference, exchange):
        self.preference = preference
        self.exchange = exchange


class FakeStr:
    def __init__(self, text):
        self._text = text

    def __str__(self):
        return self._text


@pytest.fixture
def resolver(monkeypatch):
    class Helper:
        def __init__(self):
            self.calls = []
            self.queries = {}

        def add(self, qname, rdtype, answers):
            self.queries[(qname, rdtype)] = answers

        def _resolve(self, qname, rdtype):
            self.calls.append((qname, rdtype))
            if (qname, rdtype) not in self.queries:
                raise domain_module.dns.resolver.NXDOMAIN(f"{qname}/{rdtype}")
            return self.queries[(qname, rdtype)]

    helper = Helper()
    monkeypatch.setattr(domain_module.dns.resolver, "resolve", helper._resolve)
    return helper


class TestRecordLookups:
    def test_a_records(self, resolver):
        resolver.add("example.com", "A", [FakeStr("192.0.2.1"), FakeStr("192.0.2.2")])

        assert domain_intel.get_a_records("example.com") == ["192.0.2.1", "192.0.2.2"]

    def test_aaaa_records(self, resolver):
        resolver.add("example.com", "AAAA", [FakeStr("2001:db8::1")])

        assert domain_intel.get_aaaa_records("example.com") == ["2001:db8::1"]

    def test_ns_records_trailing_dot_stripped(self, resolver):
        resolver.add("example.com", "NS", [FakeStr("ns1.example.com.")])

        assert domain_intel.get_ns_records("example.com") == ["ns1.example.com"]

    def test_txt_records(self, resolver):
        resolver.add("example.com", "TXT", [FakeTxt("v=spf1 -all")])

        assert domain_intel.get_txt_records("example.com") == ["v=spf1 -all"]

    def test_mx_sorted_by_priority(self, resolver):
        resolver.add("example.com", "MX", [
            FakeMx(30, "mx3.example.com."),
            FakeMx(10, "mx1.example.com."),
        ])

        assert domain_intel.get_mx_records("example.com") == [
            {"priority": 10, "host": "mx1.example.com"},
            {"priority": 30, "host": "mx3.example.com"},
        ]

    @pytest.mark.parametrize("method", [
        "get_a_records",
        "get_aaaa_records",
        "get_mx_records",
        "get_ns_records",
        "get_txt_records",
        "get_cname_records",
    ])
    def test_lookup_failure_returns_empty_list(self, resolver, method):
        assert getattr(domain_intel, method)("missing.example") == []


class TestGetAllRecords:
    def test_aggregates_every_type(self, resolver):
        resolver.add("example.com", "A", [FakeStr("192.0.2.1")])
        resolver.add("example.com", "AAAA", [FakeStr("2001:db8::1")])
        resolver.add("example.com", "MX", [FakeMx(5, "mail.example.com.")])
        resolver.add("example.com", "NS", [FakeStr("ns1.example.com.")])
        resolver.add("example.com", "TXT", [FakeTxt("v=spf1 -all")])

        results = domain_intel.get_all_records("example.com")

        assert results["domain"] == "example.com"
        assert results["a"] == ["192.0.2.1"]
        assert results["aaaa"] == ["2001:db8::1"]
        assert results["mx"] == [{"priority": 5, "host": "mail.example.com"}]
        assert results["ns"] == ["ns1.example.com"]
        assert results["txt"] == ["v=spf1 -all"]
        assert results["cname"] == []
