import pytest

import mailforen.modules.email.auth as auth_module
from mailforen.modules.email.auth import auth_checker


class FakeTxt:
    def __init__(self, *chunks):
        self.strings = [c.encode() for c in chunks]


class FakeMx:
    def __init__(self, preference, exchange):
        self.preference = preference
        self.exchange = exchange


class NXDOMAIN(Exception):
    pass


@pytest.fixture
def resolver(monkeypatch):
    """Replace dns.resolver.resolve with a stub backed by a (qname, rdtype) map."""
    class Helper:
        def __init__(self):
            self.calls = []
            self.queries = {}

        def add(self, qname, rdtype, answers):
            self.queries[(qname, rdtype)] = answers

        def _resolve(self, qname, rdtype):
            self.calls.append((qname, rdtype))
            if (qname, rdtype) not in self.queries:
                raise NXDOMAIN(f"{qname} has no {rdtype} record")
            return self.queries[(qname, rdtype)]

    helper = Helper()
    monkeypatch.setattr(auth_module.dns.resolver, "resolve", helper._resolve)
    return helper


class TestCheckSpf:
    def test_spf_found(self, resolver):
        # One TXT record delivered in two 255-byte chunks
        resolver.add("example.com", "TXT", [
            FakeTxt("v=spf1 ", "include:_spf.example.com ~all"),
        ])

        result = auth_checker.check_spf("example.com")

        assert result["found"] is True
        assert result["records"] == ["v=spf1 include:_spf.example.com ~all"]

    def test_spf_absent_among_other_txt(self, resolver):
        resolver.add("example.com", "TXT", [
            FakeTxt("v=DMARC1; p=none"),
            FakeTxt("google-site-verification=xyz"),
        ])

        result = auth_checker.check_spf("example.com")

        assert result["found"] is False
        assert result["records"] == []

    def test_spf_lookup_error(self, resolver):
        result = auth_checker.check_spf("missing.example")

        assert result["found"] is False
        assert "error" in result


class TestCheckDmarc:
    def test_dmarc_found(self, resolver):
        resolver.add("_dmarc.example.com", "TXT", [
            FakeTxt("v=DMARC1; p=reject; rua=mailto:d@example.com"),
        ])

        result = auth_checker.check_dmarc("example.com")

        assert result["found"] is True
        assert result["records"][0].startswith("v=DMARC1")

    def test_dmarc_queries_correct_name(self, resolver):
        resolver.add("_dmarc.example.com", "TXT", [FakeTxt("v=DMARC1; p=none")])
        auth_checker.check_dmarc("example.com")

        # qname must include the _dmarc prefix
        assert ("_dmarc.example.com", "TXT") in resolver.calls

    def test_dmarc_missing(self, resolver):
        result = auth_checker.check_dmarc("example.com")

        assert result["found"] is False
        assert "error" in result


class TestCheckMx:
    def test_mx_sorted_by_priority(self, resolver):
        resolver.add("example.com", "MX", [
            FakeMx(20, "mx2.example.com."),
            FakeMx(10, "mx1.example.com."),
        ])

        result = auth_checker.check_mx("example.com")

        assert result["found"] is True
        assert result["records"] == [
            {"priority": 10, "exchange": "mx1.example.com"},
            {"priority": 20, "exchange": "mx2.example.com"},
        ]

    def test_mx_missing(self, resolver):
        result = auth_checker.check_mx("example.com")

        assert result["found"] is False
        assert "error" in result


class TestCheckAll:
    def test_aggregates_all_checks(self, resolver, monkeypatch):
        calls = []

        def fake_resolve(qname, rdtype):
            calls.append((qname, rdtype))
            if rdtype == "MX":
                return [FakeMx(5, "mail.example.com.")]
            return {
                ("example.com", "TXT"): [FakeTxt("v=spf1 -all")],
                ("_dmarc.example.com", "TXT"): [FakeTxt("v=DMARC1; p=quarantine")],
            }[(qname, rdtype)]

        monkeypatch.setattr(auth_module.dns.resolver, "resolve", fake_resolve)

        result = auth_checker.check_all("example.com")

        assert result["domain"] == "example.com"
        assert result["spf"]["found"] is True
        assert result["dmarc"]["found"] is True
        assert result["mx"]["found"] is True
        assert ("_dmarc.example.com", "TXT") in calls
