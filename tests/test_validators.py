import pytest

from mailforen.utils.validators import validators


class TestIsEmail:
    @pytest.mark.parametrize("email", [
        "user@example.com",
        "first.last@sub.domain.org",
        "user+tag@example.co.uk",
        "a_b%c@x.io",
    ])
    def test_valid(self, email):
        assert validators.is_email(email) is True

    @pytest.mark.parametrize("email", [
        "",
        "no-at-sign",
        "@example.com",
        "user@",
        "user@nodot",
        "user @spaces.com",
    ])
    def test_invalid(self, email):
        assert validators.is_email(email) is False


class TestIsDomain:
    @pytest.mark.parametrize("domain", [
        "example.com",
        "sub.example.com",
        "deep.sub.example.org",
        "a-b.co",
    ])
    def test_valid(self, domain):
        assert validators.is_domain(domain) is True

    @pytest.mark.parametrize("domain", [
        "",
        "example",
        "-leadingdash.com",
        "trailingdash-.com",
        "example.c",          # TLD too short
        "example dot com",
    ])
    def test_invalid(self, domain):
        assert validators.is_domain(domain) is False


class TestIsIP:
    @pytest.mark.parametrize("ip", [
        "192.0.2.1",
        "0.0.0.0",
        "::1",
        "2001:db8::1",
    ])
    def test_valid(self, ip):
        assert validators.is_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "",
        "999.999.999.999",
        "192.0.2",
        "not-an-ip",
    ])
    def test_invalid(self, ip):
        assert validators.is_ip(ip) is False


class TestIsURL:
    @pytest.mark.parametrize("url", [
        "http://example.com",
        "https://example.com/path?q=1",
        "https://sub.example.com:8443/x",
    ])
    def test_valid(self, url):
        assert validators.is_url(url) is True

    @pytest.mark.parametrize("url", [
        "",
        "ftp://example.com",
        "example.com",
        "https://",
    ])
    def test_invalid(self, url):
        assert validators.is_url(url) is False


class TestExtractDomainFromEmail:
    def test_valid_email(self):
        assert validators.extract_domain_from_email("user@example.com") == "example.com"

    def test_subdomain_email(self):
        assert validators.extract_domain_from_email("a@mail.example.com") == "mail.example.com"

    def test_invalid_email_returns_none(self):
        assert validators.extract_domain_from_email("not-an-email") is None

    def test_singleton_exported(self):
        from mailforen.utils.validators import Validators

        assert isinstance(validators, Validators)
