"""Tests for the SQLite case database."""

import pytest

from mailforen.core.db import db


def test_create_and_list_case():
    case_id = db.create_case("test-case-alpha", "example.com", "unit test")
    cases = db.list_cases()
    assert any(c["id"] == case_id and c["name"] == "test-case-alpha" for c in cases)
    case = db.get_case(case_id)
    assert case["target"] == "example.com"
    assert case["status"] == "open"


def test_duplicate_case_name_raises():
    db.create_case("test-case-dup", None, None)
    with pytest.raises(Exception):
        db.create_case("test-case-dup", None, None)


def test_add_and_get_findings():
    case_id = db.create_case("test-case-findings", None, None)
    fid = db.add_finding(
        case_id, "email.auth", "example.com",
        {"spf": {"found": True}, "dmarc": {"found": False}},
        risk_level="medium", tags=["no-dmarc"], notes="phase 1",
    )
    findings = db.get_findings(case_id)
    assert len(findings) == 1
    assert findings[0]["id"] == fid
    assert findings[0]["risk_level"] == "medium"
    assert findings[0]["result"]["spf"]["found"] is True
    assert findings[0]["tags"] == ["no-dmarc"]
    assert findings[0]["notes"] == "phase 1"


def test_get_missing_case():
    assert db.get_case(999999) is None
