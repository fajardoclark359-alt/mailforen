"""Unit tests for input validators."""

from mailforen.utils.validators import validators


def test_valid_email():
    assert validators.is_email("user@example.com")
    assert validators.is_email("first.last+tag@sub.example.co.uk")


def test_invalid_email():
    assert not validators.is_email("not-an-email")
    assert not validators.is_email("missing@tld")
    assert not validators.is_email("@example.com")


def test_valid_domain():
    assert validators.is_domain("example.com")
    assert validators.is_domain("sub.example.co.uk")


def test_invalid_domain():
    assert not validators.is_domain("example")
    assert not validators.is_domain("-bad.com")
    assert not validators.is_domain("")


def test_valid_ip():
    assert validators.is_ip("192.168.0.1")
    assert validators.is_ip("::1")
    assert validators.is_ip("2606:4700::1111")


def test_invalid_ip():
    assert not validators.is_ip("999.999.999.999")
    assert not validators.is_ip("not.an.ip")


def test_ip_is_not_a_valid_domain():
    assert not validators.is_domain("192.168.0.1")


def test_extract_domain_from_email():
    assert validators.extract_domain_from_email("user@example.com") == "example.com"
    assert validators.extract_domain_from_email("bad") is None
