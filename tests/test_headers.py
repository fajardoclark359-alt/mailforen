"""Tests for .eml header analysis (offline, uses embedded sample)."""

from pathlib import Path

from mailforen.modules.email.headers import header_analyzer

SAMPLE_EML = """Return-Path: <bounce@suspicious.example>
Received: from mail-out.suspicious.example (unknown [203.0.113.66])
\tby mx.receiver.example (Postfix) with ESMTPS id 4A1B2C3D4E
\tfor <victim@receiver.example>; Mon, 2 Jan 2025 10:00:00 +0000 (UTC)
Received: from [192.0.2.9] (helo=evil.example)
\tby mail-out.suspicious.example with SMTP id X9Y8Z7
\tMon, 2 Jan 2025 09:59:58 +0000 (UTC)
Authentication-Results: mx.receiver.example; spf=fail smtp.mail=suspicious.example
From: "IT Support" <support@suspicious.example>
To: victim@receiver.example
Subject: URGENT: verify your account now
Date: Mon, 2 Jan 2025 10:00:01 +0000
Message-ID: <20250102100001.1234@suspicious.example>
X-Mailer: EvilMailer 1.0

Click here to verify.
"""


def test_analyze_headers(tmp_path: Path):
    eml = tmp_path / "sample.eml"
    eml.write_text(SAMPLE_EML)
    result = header_analyzer.analyze_file(eml)

    assert "error" not in result
    # Email parser may output From differently; check key fields exist
    assert "IT Support" in result["from"]
    assert "suspicious.example" in result["from"]
    assert result["subject"] == "URGENT: verify your account now"
    assert result["message_id"] == "<20250102100001.1234@suspicious.example>"
    assert len(result["received_chain"]) == 2
    # Originating IPs found in Received headers, loopback excluded
    assert "203.0.113.66" in result["originating_ips"]
    assert "192.0.2.9" in result["originating_ips"]
    assert "127.0.0.1" not in result["originating_ips"]
    assert result["authentication_results"].startswith("mx.receiver.example")


def test_analyze_missing_file(tmp_path: Path):
    result = header_analyzer.analyze_file(tmp_path / "nope.eml")
    assert "error" in result