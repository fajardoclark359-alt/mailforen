import sqlite3

import pytest


class TestCases:
    def test_create_case_returns_id(self, test_db):
        case_id = test_db.create_case("Phishing-001", target="example.com", description="d")

        assert isinstance(case_id, int)
        assert case_id >= 1

    def test_duplicate_case_name_raises(self, test_db):
        test_db.create_case("dup-case")
        with pytest.raises(sqlite3.IntegrityError):
            test_db.create_case("dup-case")

    def test_get_case(self, test_db):
        case_id = test_db.create_case("case-a", target="example.com", description="desc")

        case = test_db.get_case(case_id)
        assert case["name"] == "case-a"
        assert case["target"] == "example.com"
        assert case["description"] == "desc"
        assert case["status"] == "open"

    def test_get_missing_case_returns_none(self, test_db):
        assert test_db.get_case(9999) is None

    def test_list_cases(self, test_db):
        test_db.create_case("one")
        test_db.create_case("two")

        cases = test_db.list_cases()
        assert {c["name"] for c in cases} == {"one", "two"}


class TestFindings:
    def test_add_and_get_finding(self, test_db):
        case_id = test_db.create_case("with-finding")
        result = {"spf": True, "records": ["v=spf1 -all"]}

        finding_id = test_db.add_finding(
            case_id, "email.auth", "example.com", result,
            risk_level="low", tags=["phishing", "spoof"], notes="note text",
        )

        findings = test_db.get_findings(case_id)
        assert len(findings) == 1
        f = findings[0]
        assert f["id"] == finding_id
        assert f["case_id"] == case_id
        assert f["module"] == "email.auth"
        assert f["input_data"] == "example.com"
        assert f["result"] == result          # JSON round-trip
        assert f["risk_level"] == "low"
        assert f["tags"] == ["phishing", "spoof"]  # comma string -> list
        assert f["notes"] == "note text"

    def test_add_finding_defaults(self, test_db):
        case_id = test_db.create_case("defaults")

        test_db.add_finding(case_id, "mod", "input", {"k": "v"})
        f = test_db.get_findings(case_id)[0]

        assert f["risk_level"] == "info"
        assert f["tags"] == ""
        assert f["notes"] is None

    def test_get_findings_empty_case(self, test_db):
        case_id = test_db.create_case("empty")
        assert test_db.get_findings(case_id) == []

    def test_findings_scoped_to_case(self, test_db):
        c1 = test_db.create_case("case-1")
        c2 = test_db.create_case("case-2")
        test_db.add_finding(c1, "mod", "in-1", {})
        test_db.add_finding(c2, "mod", "in-2", {})

        assert len(test_db.get_findings(c1)) == 1
        assert test_db.get_findings(c1)[0]["input_data"] == "in-1"
        assert len(test_db.get_findings(c2)) == 1
