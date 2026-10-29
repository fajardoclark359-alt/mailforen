"""End-to-end GUI tests (offscreen): window, case flow, analysis, findings, report."""

import time
from pathlib import Path

import pytest

pyside = pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication  # noqa: E402

from mailforen.gui.main_window import MainWindow  # noqa: E402
from mailforen.reports.generator import report_generator  # noqa: E402

SAMPLE_EML = """From: "IT Support" <support@suspicious.example>
To: victim@receiver.example
Subject: URGENT: verify your account
Date: Mon, 2 Jan 2025 10:00:01 +0000
Message-ID: <gui-test@suspicious.example>

Click here to verify.
"""


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def window(qapp):
    from mailforen.gui.theme import apply_theme

    apply_theme(qapp)
    w = MainWindow()
    w.show()
    yield w
    w.close()


def _drain(qapp, tab, timeout=15.0):
    """Process events until the tab's worker pool is empty."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        qapp.processEvents()
        if not tab.pool._workers:
            qapp.processEvents()
            return True
        time.sleep(0.02)
    return False


def test_window_boots_with_all_pages(window):
    assert window.pages.count() == 10
    assert window.sidebar.count() == 10
    for row in range(window.pages.count()):
        window.sidebar.setCurrentRow(row)
    assert window.pages.currentIndex() == 9


def test_case_creation_via_state(window):
    before = len(window.state.cases)
    case_id = window.state.create_case("gui-test-case", "example.com", "created by GUI test")
    assert len(window.state.cases) == before + 1
    assert window.state.current_case_id == case_id


def test_email_analysis_and_finding_flow(window, qapp, tmp_path):
    # Select a case
    case_id = window.state.create_case("gui-email-flow", None, None)

    email_tab = window.tabs[1]
    eml = tmp_path / "sample.eml"
    eml.write_text(SAMPLE_EML)
    email_tab.file_picker.edit.setText(str(eml))

    # Trigger the "Analyze headers" action (first action button)
    buttons = [email_tab._action_buttons.itemAt(i).widget()
               for i in range(email_tab._action_buttons.count()) if email_tab._action_buttons.itemAt(i).widget() is not None]
    assert len(buttons) >= 1
    buttons[0].click()

    assert _drain(qapp, email_tab), "headers analysis did not finish"
    assert email_tab._last_result is not None
    assert "error" not in email_tab._last_result
    assert email_tab._last_result["subject"] == "URGENT: verify your account"

    # Domain autofilled from From: header
    assert email_tab.domain_edit.text() == "suspicious.example"

    # Save finding to the case
    email_tab._save_finding()
    from mailforen.core.db import db

    findings = db.get_findings(case_id)
    assert len(findings) == 1
    assert findings[0]["module"] == "email.headers"
    assert findings[0]["result"]["subject"] == "URGENT: verify your account"


def test_findings_tab_displays_finding(window, qapp):
    case_id = window.state.create_case("gui-findings-view", None, None)
    from mailforen.core.db import db

    db.add_finding(case_id, "ct.search", "example.com", {"certificates_found": 3},
                   risk_level="info", tags=["subdomains:3"])
    window.state.select_case(case_id)
    qapp.processEvents()

    findings_tab = window.tabs[8]
    qapp.processEvents()
    assert findings_tab.table.rowCount() == 1
    assert findings_tab.table.item(0, 1).text() == "ct.search"


def test_report_generation_from_gui(window, qapp):
    case_id = window.state.create_case("gui-report-case", "example.com", None)
    from mailforen.core.db import db

    db.add_finding(case_id, "email.headers", "sample.eml", {"subject": "x"})

    reports_tab = window.tabs[9]
    reports_tab.format_combo.setCurrentText("markdown")
    buttons = [reports_tab._action_buttons.itemAt(i).widget()
               for i in range(reports_tab._action_buttons.count())]
    buttons[0].click()

    assert _drain(qapp, reports_tab)
    reports = list(Path(report_generator.reports_dir).glob("report_gui-report-case_*.md"))
    assert reports, "markdown report was not created"
    content = reports[0].read_text()
    assert "gui-report-case" in content


def test_domain_tab_validates_input(window, qapp):
    domain_tab = window.tabs[2]
    domain_tab.domain_edit.setText("not a domain!!")
    buttons = [domain_tab._action_buttons.itemAt(i).widget()
               for i in range(domain_tab._action_buttons.count())]
    buttons[0].click()
    assert _drain(qapp, domain_tab)
    assert "error" in (domain_tab._last_result or {"error": "none"})
