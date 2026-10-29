"""Tests for SPF/DKIM/DMARC auth logic with DNS mocked (no network)."""

from unittest.mock import MagicMock, patch

from mailforen.modules.email.auth import auth_checker


def _txt_answer(records):
    answer = []
    for text in records:
        rdata = MagicMock()
        rdata.strings = [text.encode()]
        answer.append(rdata)
    return answer


def test_spf_found():
    with patch("dns.resolver.resolve", return_value=_txt_answer(["v=spf1 include:_spf.example.com ~all"])):
        result = auth_checker.check_spf("example.com")
    assert result["found"] is True
    assert result["records"] == ["v=spf1 include:_spf.example.com ~all"]


def test_spf_missing():
    with patch("dns.resolver.resolve", return_value=_txt_answer(["some other txt"])):
        result = auth_checker.check_spf("example.com")
    assert result["found"] is False


def test_dmarc_found():
    with patch("dns.resolver.resolve", return_value=_txt_answer(["v=DMARC1; p=reject"])):
        result = auth_checker.check_dmarc("example.com")
    assert result["found"] is True


def test_check_all_aggregates():
    answers = {
        "example.com": _txt_answer(["v=spf1 -all"]),
        "_dmarc.example.com": _txt_answer(["v=DMARC1; p=none"]),
    }
    mx_answer = []
    rdata = MagicMock()
    rdata.preference = 10
    rdata.exchange = "mail.example.com."
    mx_answer.append(rdata)

    def resolve(name, rtype, *a, **kw):
        if rtype == "MX":
            return mx_answer
        return answers[name]

    with patch("dns.resolver.resolve", side_effect=resolve):
        result = auth_checker.check_all("example.com")

    assert result["domain"] == "example.com"
    assert result["spf"]["found"] is True
    assert result["dmarc"]["found"] is True
    assert result["mx"]["found"] is True
    assert result["mx"]["records"] == [{"priority": 10, "exchange": "mail.example.com"}]


def test_dns_failure_is_graceful():
    with patch("dns.resolver.resolve", side_effect=Exception("NXDOMAIN")):
        result = auth_checker.check_all("nonexistent.invalid")
    assert result["spf"]["found"] is False
    assert result["dmarc"]["found"] is False
    assert result["mx"]["found"] is False
