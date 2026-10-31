import json

import pytest
from typer.testing import CliRunner

import mailforen.cli as cli_module
import mailforen.reports.generator as generator_module
from mailforen.core.config import settings

EML = b"""From: attacker@example.com
To: victim@target.org
Subject: Urgent: verify your account
Date: Tue, 28 Oct 2026 10:00:00 +0000
Message-ID: <abc123@example.com>
Received: from mail.example.com (mail.example.com [203.0.113.5]) by mx.target.org with ESMTPS id 42; Tue, 28 Oct 2026 10:00:02 +0000

Verify your account now.
"""


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def eml_file(tmp_path):
    path = tmp_path / "cli-sample.eml"
    path.write_bytes(EML)
    return path


@pytest.fixture
def cli_db(test_db, monkeypatch):
    """Route every db access in the CLI (and report generator) to the test db."""
    monkeypatch.setattr(cli_module, "db", test_db)
    monkeypatch.setattr(generator_module, "db", test_db)
    return test_db


class TestBasicCommands:
    def test_version(self, runner):
        result = runner.invoke(cli_module.app, ["version"])

        assert result.exit_code == 0
        assert "mailforen" in result.output

    def test_disclaimer(self, runner):
        result = runner.invoke(cli_module.app, ["disclaimer"])

        assert result.exit_code == 0
        # "authorized" survives rich's line wrapping (phrases may not)
        assert "authorized" in result.output.lower()


class TestCaseCommands:
    def test_case_new(self, runner, cli_db):
        result = runner.invoke(
            cli_module.app,
            ["case", "new", "Phishing-001", "--target", "example.com", "--desc", "test"],
        )

        assert result.exit_code == 0
        case = cli_db.get_case(1)
        assert case["name"] == "Phishing-001"
        assert case["target"] == "example.com"

    def test_case_new_duplicate_fails(self, runner, cli_db):
        cli_db.create_case("Phishing-001")

        result = runner.invoke(cli_module.app, ["case", "new", "Phishing-001"])

        assert result.exit_code == 1

    def test_case_list_empty(self, runner, cli_db):
        result = runner.invoke(cli_module.app, ["case", "list"])

        assert result.exit_code == 0
        assert "No cases found" in result.output

    def test_case_list_with_cases(self, runner, cli_db):
        cli_db.create_case("Case-A")
        cli_db.create_case("Case-B")

        result = runner.invoke(cli_module.app, ["case", "list"])

        assert result.exit_code == 0
        assert "Case-A" in result.output
        assert "Case-B" in result.output

    def test_case_show(self, runner, cli_db):
        case_id = cli_db.create_case("Case-A", target="example.com")
        cli_db.add_finding(case_id, "email.auth", "example.com", {"spf": True}, risk_level="low")

        result = runner.invoke(cli_module.app, ["case", "show", str(case_id)])

        assert result.exit_code == 0
        assert "Case-A" in result.output
        assert "Findings (1)" in result.output

    def test_case_show_missing(self, runner, cli_db):
        result = runner.invoke(cli_module.app, ["case", "show", "999"])

        assert result.exit_code == 1


class TestEmailCommands:
    def test_headers_missing_file(self, runner, cli_db, tmp_path):
        result = runner.invoke(
            cli_module.app, ["email", "headers", str(tmp_path / "nope.eml")]
        )

        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_headers_with_case(self, runner, cli_db, eml_file):
        case_id = cli_db.create_case("eml-case")

        result = runner.invoke(
            cli_module.app, ["email", "headers", str(eml_file), "--case-id", str(case_id)]
        )

        assert result.exit_code == 0
        assert "attacker@example.com" in result.output
        findings = cli_db.get_findings(case_id)
        assert len(findings) == 1
        assert findings[0]["module"] == "email.headers"
        assert findings[0]["result"]["subject"] == "Urgent: verify your account"


class TestUserPivot:
    def test_pivot_builds_profile_urls(self, runner, cli_db):
        result = runner.invoke(cli_module.app, ["user", "pivot", "johndoe"])

        assert result.exit_code == 0
        assert "https://github.com/johndoe" in result.output
        assert "https://twitter.com/johndoe" in result.output

    def test_pivot_records_finding(self, runner, cli_db):
        case_id = cli_db.create_case("pivot-case")

        result = runner.invoke(
            cli_module.app, ["user", "pivot", "johndoe", "--case-id", str(case_id)]
        )

        assert result.exit_code == 0
        finding = cli_db.get_findings(case_id)[0]
        assert finding["module"] == "user.pivot"
        urls = [c["url"] for c in finding["result"]["checks"]]
        assert "https://reddit.com/johndoe" in urls


class TestUnsafeFlag:
    def test_unsafe_flag_enables_mode_and_warns(self, runner, monkeypatch):
        monkeypatch.setattr(settings, "allow_unsafe", False)

        result = runner.invoke(cli_module.app, ["--unsafe", "version"])

        assert result.exit_code == 0
        assert "Unsafe mode enabled" in result.output
        assert settings.allow_unsafe is True

    def test_without_flag_stays_passive(self, runner, monkeypatch):
        monkeypatch.setattr(settings, "allow_unsafe", True)

        result = runner.invoke(cli_module.app, ["version"])

        assert result.exit_code == 0
        assert "Unsafe mode" not in result.output
        assert settings.allow_unsafe is False


class TestReportCommand:
    def test_report_generate_unsupported_format(self, runner, cli_db, tmp_path, monkeypatch):
        case_id = cli_db.create_case("rep-case")
        gen = generator_module.report_generator
        monkeypatch.setattr(gen, "reports_dir", tmp_path / "reports")

        result = runner.invoke(
            cli_module.app,
            ["report", "generate", "--case-id", str(case_id), "--format", "xlsx"],
        )

        assert result.exit_code == 1
        assert "Unsupported format" in result.output

    def test_report_generate_json(self, runner, cli_db, tmp_path, monkeypatch):
        case_id = cli_db.create_case("rep-case")
        cli_db.add_finding(case_id, "user.pivot", "johndoe", {"checks": []})
        gen = generator_module.report_generator
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        monkeypatch.setattr(gen, "reports_dir", reports_dir)

        result = runner.invoke(
            cli_module.app,
            ["report", "generate", "--case-id", str(case_id), "--format", "json"],
        )

        assert result.exit_code == 0
        assert "Report saved" in result.output
        reports = list((tmp_path / "reports").glob("report_rep-case_*.json"))
        assert len(reports) == 1
        data = json.loads(reports[0].read_text())
        assert data["case"]["name"] == "rep-case"
        assert len(data["findings"]) == 1
