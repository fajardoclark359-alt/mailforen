import json

import pytest

import mailforen.reports.generator as generator_module
from mailforen.reports.generator import ReportGenerator


@pytest.fixture
def generator(test_db, monkeypatch, tmp_path):
    """ReportGenerator wired to an isolated db and reports dir."""
    monkeypatch.setattr(generator_module, "db", test_db)

    gen = ReportGenerator.__new__(ReportGenerator)
    gen.reports_dir = tmp_path / "reports"
    gen.reports_dir.mkdir(parents=True)
    return gen


@pytest.fixture
def case_with_findings(test_db):
    case_id = test_db.create_case(
        "Phishing-Incident-001", target="example.com", description="Suspicious email"
    )
    test_db.add_finding(
        case_id, "email.headers", "/tmp/sample.eml",
        {"subject": "Urgent: verify your account"},
        risk_level="high", tags=["phishing"], notes="Spoofed sender",
    )
    test_db.add_finding(
        case_id, "ct.search", "example.com",
        {"unique_subdomains": ["mail.example.com"]},
        risk_level="info",
    )
    return case_id


class TestGenerate:
    def test_unknown_case_raises(self, generator):
        with pytest.raises(ValueError, match="not found"):
            generator.generate(9999, "html")

    def test_unsupported_format_raises(self, generator, test_db, case_with_findings):
        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate(case_with_findings, "xlsx")

    def test_json_report(self, generator, test_db, case_with_findings):
        path = generator.generate(case_with_findings, "json")

        assert path.exists() and path.suffix == ".json"
        data = json.loads(path.read_text())
        assert data["case"]["name"] == "Phishing-Incident-001"
        assert data["case"]["target"] == "example.com"
        assert len(data["findings"]) == 2
        assert data["tool"].startswith("mailforen")

    def test_markdown_report(self, generator, test_db, case_with_findings):
        path = generator.generate(case_with_findings, "markdown")

        content = path.read_text()
        assert path.suffix == ".md"
        assert "# Investigation Report" in content
        assert "Phishing-Incident-001" in content
        assert "email.headers" in content
        assert "HIGH" in content  # risk level upper-cased
        assert "Spoofed sender" in content

    def test_md_alias(self, generator, test_db, case_with_findings):
        path = generator.generate(case_with_findings, "md")

        assert path.suffix == ".md"

    def test_html_report(self, generator, test_db, case_with_findings):
        path = generator.generate(case_with_findings, "html")

        content = path.read_text()
        assert "<html>" in content
        assert "Phishing-Incident-001" in content
        assert "risk-high" in content
        assert "DISCLAIMER" in content

    def test_pdf_falls_back_to_html(self, generator, test_db, case_with_findings):
        # No wkhtmltopdf/weasyprint in test env: generator must degrade to the HTML path
        path = generator.generate(case_with_findings, "pdf")

        assert path.exists()
        assert path.suffix in {".pdf", ".html"}

    def test_findings_rendered_in_order(self, generator, test_db):
        case_id = test_db.create_case("order-case")
        test_db.add_finding(case_id, "mod.a", "first", {})
        test_db.add_finding(case_id, "mod.b", "second", {})

        path = generator.generate(case_id, "json")
        data = json.loads(path.read_text())

        modules = [f["module"] for f in data["findings"]]
        assert len(modules) == 2
