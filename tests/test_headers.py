"""Unit tests for mailforen.modules.email.headers (no network access)."""
import email
from email import policy

from mailforen.modules.email.headers import HeaderAnalyzer, header_analyzer


class TestAnalyzeFile:
    def test_parses_basic_fields(self, sample_eml):
        results = header_analyzer.analyze_file(sample_eml)

        assert "error" not in results
        assert results["from"] == "Attacker <phisher@sender-example.com>"
        assert results["to"] == "Victim <victim@dest-example.org>"
        assert results["subject"] == "Urgent: verify your account"
        assert results["message_id"] == "<phish-001@sender-example.com>"
        assert results["reply_to"] == "phish@evil-example.net"
        assert results["return_path"] == "<bounce@sender-example.com>"
        assert results["x_mailer"] == "PhishingKit 1.0"

    def test_received_chain_structure(self, sample_eml):
        results = header_analyzer.analyze_file(sample_eml)

        chain = results["received_chain"]
        assert len(chain) == 3
        # Hop numbers are assigned 3..1 for 3 headers (documents current behaviour)
        assert [hop["hop"] for hop in chain] == [3, 2, 1]
        # Earliest server (bottom-most header) is walked first
        assert "attacker-host" in chain[0]["raw"]
        assert "mail.dest-example.org" in chain[-1]["raw"]

    def test_originating_ips_extracted_deduped_and_loopback_excluded(self, sample_eml):
        results = header_analyzer.analyze_file(sample_eml)

        ips = results["originating_ips"]
        # 203.0.113.77 appears in two headers (deduped), 127.0.0.1 must be excluded
        assert ips == ["203.0.113.77", "198.51.100.10"]
        assert "127.0.0.1" not in ips
        assert "0.0.0.0" not in ips
        assert len(ips) == len(set(ips))

    def test_authentication_results_captured(self, sample_eml):
        results = header_analyzer.analyze_file(sample_eml)

        assert "spf=fail" in (results["authentication_results"] or "")

    def test_missing_file_returns_error(self, tmp_path):
        results = header_analyzer.analyze_file(tmp_path / "does-not-exist.eml")

        assert "error" in results


class TestAnalyzeMessage:
    def test_message_without_received_headers(self):
        msg = email.message_from_string(
            "From: a@b.com\nTo: c@d.com\nSubject: hi\n\nbody",
            policy=policy.default,
        )
        results = header_analyzer.analyze_message(msg)

        assert results["received_chain"] == []
        assert results["originating_ips"] == []
        assert results["subject"] == "hi"

    def test_body_ips_not_scanned(self, sample_eml):
        """IPs inside Received headers are picked up, IPs in the body are not."""
        results = header_analyzer.analyze_file(sample_eml)

        assert "10.0.0.99" not in results["originating_ips"]

    def test_singleton_exported(self):
        assert isinstance(header_analyzer, HeaderAnalyzer)
