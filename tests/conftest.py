"""Shared fixtures for the mailforen test suite.

Isolation strategy (two layers):
1. ``MAILFOREN_DATA_DIR`` is forced to a throwaway directory *before* any
   mailforen import happens, so module-level singletons (db, report_generator)
   never touch ~/.mailforen.
2. Tests that need their own CaseDB get a per-test instance via ``case_db``
   (or ``test_db``), and the CLI/report singletons are swapped for it via
   ``patched_db``.

No test in this suite performs network access: DNS is stubbed in
test_auth.py / test_domain.py, HTTP is stubbed in test_urltrace.py.
"""
import os
import tempfile
import uuid

_TEST_DATA_DIR = tempfile.mkdtemp(prefix="mailforen-test-data-")
os.environ["MAILFOREN_DATA_DIR"] = _TEST_DATA_DIR

from email import policy  # noqa: E402
from email.message import Message  # noqa: E402
from email.parser import BytesParser  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

from mailforen.core.config import settings  # noqa: E402
from mailforen.core.db import CaseDB  # noqa: E402
from mailforen.reports.generator import ReportGenerator  # noqa: E402

SAMPLE_EML = b"""From: Attacker <phisher@sender-example.com>
To: Victim <victim@dest-example.org>
Subject: Urgent: verify your account
Date: Tue, 28 Oct 2026 10:00:00 +0000
Message-ID: <phish-001@sender-example.com>
Reply-To: phish@evil-example.net
Return-Path: <bounce@sender-example.com>
X-Mailer: PhishingKit 1.0
Authentication-Results: mx.dest-example.org; spf=fail smtp.mailfrom=sender-example.com
Received: from mx.dest-example.org (mx.dest-example.org [198.51.100.10]) by mail.dest-example.org with ESMTPS id 42; Tue, 28 Oct 2026 10:00:02 +0000
Received: from relay.sender-example.com (relay.sender-example.com [203.0.113.77]) by mx.dest-example.org with ESMTP id 41; Tue, 28 Oct 2026 10:00:01 +0000
Received: from attacker-host (unknown [203.0.113.77]) (localhost [127.0.0.1]) by relay.sender-example.com with SMTP id 40; Tue, 28 Oct 2026 10:00:00 +0000

Verify your account now. Internal host: 10.0.0.99
"""


def unique_name(base: str) -> str:
    """Suffix a case name so tests never collide on the UNIQUE(name) constraint."""
    return f"{base}-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point settings.data_dir at a per-test directory (reports land here)."""
    data_dir = tmp_path / "mailforen-data"
    data_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", data_dir)
    return data_dir


@pytest.fixture()
def case_db(isolated_data_dir: Path) -> CaseDB:
    """A fresh CaseDB in the isolated per-test data directory."""
    return CaseDB()


@pytest.fixture()
def test_db(tmp_path: Path) -> CaseDB:
    """A CaseDB fully isolated in tmp_path (bypasses settings entirely)."""
    db = CaseDB.__new__(CaseDB)
    db.db_path = tmp_path / "cases.db"
    db.init_db()
    return db


@pytest.fixture()
def patched_db(case_db: CaseDB, monkeypatch: pytest.MonkeyPatch) -> CaseDB:
    """Swap the module-level db singletons used by the CLI and report generator."""
    import mailforen.cli as cli_module
    import mailforen.reports.generator as generator_module

    monkeypatch.setattr(cli_module, "db", case_db)
    monkeypatch.setattr(generator_module, "db", case_db)
    return case_db


@pytest.fixture()
def generator(patched_db: CaseDB) -> ReportGenerator:
    """A ReportGenerator writing into the isolated per-test data directory."""
    return ReportGenerator()


@pytest.fixture()
def case_with_finding(case_db: CaseDB) -> tuple[int, int]:
    """A case containing one finding; returns (case_id, finding_id)."""
    case_id = case_db.create_case(
        "Test-Case-001", target="example.com", description="A test case"
    )
    finding_id = case_db.add_finding(
        case_id,
        module="email.auth",
        input_data="example.com",
        result={"spf": {"found": False}, "dmarc": {"found": True}},
        risk_level="medium",
        tags=["spf", "auth"],
        notes="SPF record missing",
    )
    return case_id, finding_id


@pytest.fixture()
def sample_eml(tmp_path: Path) -> Path:
    """A sample phishing-style .eml file with a 3-hop Received chain."""
    eml_path = tmp_path / "sample.eml"
    eml_path.write_bytes(SAMPLE_EML)
    return eml_path


@pytest.fixture()
def parsed_sample_message() -> Message:
    """The sample .eml parsed into an email.message.Message object."""
    return BytesParser(policy=policy.default).parsebytes(SAMPLE_EML)
