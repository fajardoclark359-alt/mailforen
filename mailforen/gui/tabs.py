"""All tab panels for the mailforen GUI."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.db import db
from ..modules.email.auth import auth_checker
from ..modules.email.headers import header_analyzer
from ..modules.forensic.ct import ct_search
from ..modules.forensic.domain import domain_intel
from ..modules.forensic.filemeta import file_meta
from ..modules.forensic.ip import ip_intel
from ..modules.forensic.urltrace import url_tracer
from ..reports.generator import report_generator
from ..utils.validators import validators
from .components import CaseSelector, JsonView, PathPicker, ToolTab
from .state import AppState
from .theme import RISK_COLORS


# --------------------------------------------------------------------------
# Cases / dashboard
# --------------------------------------------------------------------------
class CasesTab(QWidget):
    """Case management + dashboard overview."""

    title = "Cases"

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QLabel(self.title)
        header.setObjectName("sidebarTitle")
        root.addWidget(header)

        root.addWidget(CaseSelector(self.state))

        self.stats = QLabel()
        root.addWidget(self.stats)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Target", "Status", "Created"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.clicked.connect(self.state.refresh_cases)
        delete_btn = QPushButton("🗑 Delete selected case")
        delete_btn.clicked.connect(self._delete_case)
        actions.addWidget(refresh_btn)
        actions.addWidget(delete_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self.state.cases_changed.connect(self._reload)
        self.state.case_changed.connect(self._on_case_changed)
        self._reload()

    def _reload(self):
        cases = self.state.cases
        self.table.setRowCount(len(cases))
        total_findings = 0
        for row, case in enumerate(cases):
            findings = db.get_findings(case["id"])
            total_findings += len(findings)
            values = [str(case["id"]), case["name"], case["target"] or "—",
                      case["status"], case["created_at"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 3:  # status
                    color = {"open": RISK_COLORS["low"], "closed": "#8a93a3"}.get(
                        value, RISK_COLORS["info"])
                    item.setForeground(QColor(color))
                self.table.setItem(row, col, item)
        self.stats.setText(
            f"{len(cases)} case(s) · {total_findings} finding(s) stored in "
            f"{db.db_path}"
        )

    def _on_row_selected(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self.state.cases):
            self.state.select_case(self.state.cases[row]["id"])

    def _on_case_changed(self, case):
        if not case:
            return
        for row, c in enumerate(self.state.cases):
            if c["id"] == case["id"]:
                self.table.selectRow(row)
                break

    def _delete_case(self):
        case = self.state.current_case
        if not case:
            return
        answer = QMessageBox.question(
            self, "Delete case",
            f"Delete case #{case['id']} “{case['name']}” and all its findings?")
        if answer != QMessageBox.Yes:
            return
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("DELETE FROM findings WHERE case_id = ?", (case["id"],))
            conn.execute("DELETE FROM requests WHERE case_id = ?", (case["id"],))
            conn.execute("DELETE FROM cases WHERE id = ?", (case["id"],))
        self.state.refresh_cases()
        self.state.set_status(f"Deleted case #{case['id']}")


# --------------------------------------------------------------------------
# Email forensics
# --------------------------------------------------------------------------
class EmailTab(ToolTab):
    title = "Email Forensics"

    def __init__(self, state: AppState, parent=None):
        self.domain_edit = None
        super().__init__(state, parent)

    def build_inputs(self, form):
        form.addWidget(QLabel("Email file (.eml):"))
        self.file_picker = PathPicker("Path to .eml file…")
        form.addWidget(self.file_picker)

        row = QHBoxLayout()
        row.addWidget(QLabel("Domain for auth check:"))
        self.domain_edit = QLineEdit()
        self.domain_edit.setPlaceholderText("auto-filled from From: header")
        row.addWidget(self.domain_edit, 1)
        form.addLayout(row)

    def add_actions(self, buttons):
        self.add_run_button(
            "🔍 Analyze headers", self._analyze_headers, "email.headers",
            input_summary=lambda: self.file_picker.text(),
        )
        self.add_run_button(
            "🛡 Check SPF/DKIM/DMARC", self._check_auth, "email.auth",
            input_summary=lambda: self.domain_edit.text().strip(),
            assess=self._auth_risk,
        )

    def _analyze_headers(self):
        path = Path(self.require_file(self.file_picker, ".eml file"))
        if not path:
            return {"error": "No file selected"}
        result = header_analyzer.analyze_file(path)
        if "error" not in result and result.get("from"):
            domain = validators.extract_domain_from_email(result["from"])
            if domain and not self.domain_edit.text().strip():
                self.domain_edit.setText(domain)
        return result

    def _check_auth(self):
        domain = self.domain_edit.text().strip()
        if not domain:
            return {"error": "No domain specified"}
        return auth_checker.check_all(domain)

    @staticmethod
    def _auth_risk(result) -> Tuple[str, List[str]]:
        try:
            domain = result.get("domain", "")
            missing = []
            if not result["spf"]["found"]:
                missing.append("no-spf")
            if not result["dmarc"]["found"]:
                missing.append("no-dmarc")
            if not result["mx"]["found"]:
                missing.append("no-mx")
            if "no-dmarc" in missing and "no-spf" in missing:
                return "high", missing
            if missing:
                return "medium", missing
            return "low", [f"auth-ok:{domain}"]
        except (KeyError, TypeError):
            return "info", []


# --------------------------------------------------------------------------
# Domain / IP / CT
# --------------------------------------------------------------------------
class DomainTab(ToolTab):
    title = "Domain Intelligence"

    def build_inputs(self, form):
        self.domain_edit = QLineEdit()
        self.domain_edit.setPlaceholderText("example.com")
        form.addWidget(QLabel("Domain:"))
        form.addWidget(self.domain_edit)

    def add_actions(self, buttons):
        self.add_run_button(
            "🌐 DNS records", self._dns, "domain.intel",
            input_summary=lambda: self.domain_edit.text().strip(),
        )
        self.add_run_button(
            "📜 CT logs (crt.sh)", self._ct, "ct.search",
            input_summary=lambda: self.domain_edit.text().strip(),
            assess=self._ct_risk,
        )

    def _validated_domain(self):
        domain = self.domain_edit.text().strip().lower()
        if not domain:
            return None
        if not validators.is_domain(domain):
            return None
        return domain

    def _dns(self):
        domain = self._validated_domain()
        if not domain:
            return {"error": "Enter a valid domain (e.g. example.com)"}
        return domain_intel.get_all_records(domain)

    def _ct(self):
        domain = self._validated_domain()
        if not domain:
            return {"error": "Enter a valid domain (e.g. example.com)"}
        return ct_search.search(domain)

    @staticmethod
    def _ct_risk(result) -> Tuple[str, List[str]]:
        subs = result.get("unique_subdomains", []) if isinstance(result, dict) else []
        if not subs:
            return "info", ["ct-empty"]
        return "info", [f"subdomains:{len(subs)}"]


class IPTab(ToolTab):
    title = "IP Intelligence"

    def build_inputs(self, form):
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("203.0.113.10")
        form.addWidget(QLabel("IP address:"))
        form.addWidget(self.ip_edit)

    def add_actions(self, buttons):
        self.add_run_button(
            "🛰 Look up IP", self._lookup, "ip.intel",
            input_summary=lambda: self.ip_edit.text().strip(),
            assess=self._ip_risk,
        )

    def _lookup(self):
        ip = self.ip_edit.text().strip()
        if not ip:
            return {"error": "Enter an IP address"}
        if not validators.is_ip(ip):
            return {"error": f"“{ip}” is not a valid IP address"}
        result = ip_intel.get_info(ip)
        asn = ip_intel.get_asn_info(ip)
        if isinstance(asn, dict) and asn:
            result["asn"] = asn
        return result

    @staticmethod
    def _ip_risk(result) -> Tuple[str, List[str]]:
        org = ""
        if isinstance(result, dict):
            org = str(result.get("asn", {}).get("org", ""))
        tags = []
        if org:
            tags.append(f"org:{org[:60]}")
        return "info", tags


# --------------------------------------------------------------------------
# URL / file / user
# --------------------------------------------------------------------------
class URLTab(ToolTab):
    title = "URL Trace"

    def build_inputs(self, form):
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://suspicious.example/link")
        form.addWidget(QLabel("URL to trace:"))
        form.addWidget(self.url_edit)

    def add_actions(self, buttons):
        self.add_run_button(
            "➡ Trace redirects", self._trace, "url.trace",
            input_summary=lambda: self.url_edit.text().strip(),
            assess=self._url_risk,
        )

    def _trace(self):
        url = self.url_edit.text().strip()
        if not url:
            return {"error": "Enter a URL"}
        if not validators.is_url(url):
            return {"error": f"“{url}” is not a valid http(s) URL"}
        return url_tracer.trace(url)

    @staticmethod
    def _url_risk(result) -> Tuple[str, List[str]]:
        if not isinstance(result, dict):
            return "info", []
        final = result.get("final_url", "")
        original = result.get("original_url", "")
        hops = result.get("total_redirects", 0)
        tags = [f"redirects:{hops}"]
        # Cross-domain redirect = classic phishing marker
        try:
            o_domain = original.split("/")[2].lower() if "://" in original else ""
            f_domain = final.split("/")[2].lower() if "://" in final else ""
            if o_domain and f_domain and o_domain != f_domain:
                return "medium", tags + [f"cross-domain:{o_domain}->{f_domain}"]
        except (IndexError, AttributeError):
            pass
        return "info", tags


class FileTab(ToolTab):
    title = "File Metadata"

    def build_inputs(self, form):
        form.addWidget(QLabel("File to inspect:"))
        self.file_picker = PathPicker("Any file (images get EXIF extraction)…")
        form.addWidget(self.file_picker)

    def add_actions(self, buttons):
        self.add_run_button(
            "📎 Extract metadata", self._extract, "file.meta",
            input_summary=lambda: self.file_picker.text(),
        )

    def _extract(self):
        path = Path(self.require_file(self.file_picker, "file"))
        if not path:
            return {"error": "No file selected"}
        return file_meta.extract(path)


class UserTab(ToolTab):
    title = "Username Pivot"

    def build_inputs(self, form):
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("username or handle")
        form.addWidget(QLabel("Username:"))
        form.addWidget(self.user_edit)

    def add_actions(self, buttons):
        self.add_run_button(
            "🧩 Build profile URLs", self._pivot, "user.pivot",
            input_summary=lambda: self.user_edit.text().strip(),
        )

    def _pivot(self):
        username = self.user_edit.text().strip()
        if not username:
            return {"error": "Enter a username"}
        platforms = ["github.com", "twitter.com", "instagram.com", "reddit.com"]
        return {
            "username": username,
            "checks": [
                {"platform": p, "url": f"https://{p}/{username}",
                 "method": "passive_url_construction"}
                for p in platforms
            ],
        }


# --------------------------------------------------------------------------
# Findings & reports
# --------------------------------------------------------------------------
class FindingsTab(QWidget):
    title = "Findings"

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QLabel(self.title)
        header.setObjectName("sidebarTitle")
        root.addWidget(header)

        root.addWidget(CaseSelector(self.state))

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Risk", "Module", "Input", "Tags", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_row)
        root.addWidget(self.table, 1)

        self.detail = JsonView()
        root.addWidget(self.detail, 1)

        actions = QHBoxLayout()
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Notes for selected finding…")
        save_notes = QPushButton("Save notes")
        save_notes.clicked.connect(self._save_notes)
        delete_btn = QPushButton("🗑 Delete finding")
        delete_btn.clicked.connect(self._delete_finding)
        actions.addWidget(QLabel("Notes:"), 0)
        actions.addWidget(self.notes_edit, 1)
        actions.addWidget(save_notes)
        actions.addWidget(delete_btn)
        root.addLayout(actions)

        self._findings: List[Dict[str, Any]] = []
        self.state.case_changed.connect(self._reload)
        self._reload(self.state.current_case)

    def _reload(self, case):
        self.table.setRowCount(0)
        self.detail.clear()
        self._findings = db.get_findings(case["id"]) if case else []
        self.table.setRowCount(len(self._findings))
        for row, finding in enumerate(self._findings):
            tags = finding.get("tags")
            tags_str = ",".join(tags) if isinstance(tags, list) else (tags or "")
            values = [finding["risk_level"].upper(), finding["module"],
                      finding["input_data"], tags_str, finding["timestamp"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    color = RISK_COLORS.get(finding["risk_level"], "#d8dee9")
                    item.setForeground(QColor(color))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row, col, item)
        self.notes_edit.clear()

    def _on_row(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._findings):
            finding = self._findings[row]
            self.detail.show_data(finding.get("result", {}))
            self.notes_edit.setText(finding.get("notes") or "")
            self.state.set_status(
                f"Finding #{finding['id']} — {finding['module']} ({finding['risk_level']})")

    def _save_notes(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self._findings)):
            return
        finding = self._findings[row]
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("UPDATE findings SET notes = ? WHERE id = ?",
                         (self.notes_edit.text().strip(), finding["id"]))
        self.state.set_status(f"Notes saved for finding #{finding['id']}")

    def _delete_finding(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self._findings)):
            return
        finding = self._findings[row]
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("DELETE FROM findings WHERE id = ?", (finding["id"],))
        self.state.set_status(f"Deleted finding #{finding['id']}")
        self._reload(self.state.current_case)


class ReportsTab(ToolTab):
    title = "Reports"

    def build_inputs(self, form):
        form.addWidget(CaseSelector(self.state))
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["html", "markdown", "json", "pdf"])
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch(1)
        form.addLayout(fmt_row)

    def add_actions(self, buttons):
        self.add_run_button(
            "📄 Generate report", self._generate, "report.generate",
            input_summary=lambda: f"case={self.state.current_case_id} "
                                  f"format={self.format_combo.currentText()}",
        )
        open_btn = QPushButton("📂 Open report folder")
        open_btn.clicked.connect(self._open_folder)
        buttons.addWidget(open_btn)

    def _generate(self):
        case_id = self.state.current_case_id
        if case_id is None:
            return {"error": "No case selected"}
        try:
            path = report_generator.generate(case_id, self.format_combo.currentText())
            self.state.set_status(f"Report written to {path}")
            return {
                "status": "ok",
                "format": self.format_combo.currentText(),
                "path": str(path),
                "case": f"#{case_id} {self.state.current_case['name']}",
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def _open_folder(self):
        folder = report_generator.reports_dir
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", str(folder)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            elif sys.platform == "win32":
                subprocess.Popen(["explorer", str(folder)])
        except OSError as exc:
            QMessageBox.warning(self, "Could not open folder", str(exc))
