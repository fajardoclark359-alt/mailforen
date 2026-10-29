"""Reusable widgets shared by all tabs."""

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .state import AppState
from .theme import RISK_COLORS
from .workers import WorkerPool


class JsonView(QTreeWidget):
    """Recursive tree viewer for arbitrary JSON/dict results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Field", "Value"])
        self.setAlternatingRowColors(True)
        self.setColumnWidth(0, 260)
        self.setWordWrap(False)

    def show_data(self, data: Any) -> None:
        self.clear()
        if data is None:
            return
        if isinstance(data, dict) and data.get("error"):
            self.addTopLevelItem(QTreeWidgetItem(["Error", str(data["error"])]))
            return
        self._fill(self.invisibleRootItem(), data)

    def _fill(self, parent_item, data: Any, key: str = "") -> None:
        if isinstance(data, dict):
            node = QTreeWidgetItem([str(key) if key else "result", ""])
            node.setFlags(node.flags() & ~Qt.ItemIsSelectable)
            parent_item.addChild(node)
            if not data:
                node.addChild(QTreeWidgetItem(["(empty)", ""]))
            for k, v in data.items():
                self._fill(node, v, str(k))
        elif isinstance(data, (list, tuple)):
            if key:
                node = QTreeWidgetItem([key, f"({len(data)} items)"])
                node.setFlags(node.flags() & ~Qt.ItemIsSelectable)
                parent_item.addChild(node)
                if not data:
                    node.addChild(QTreeWidgetItem(["(empty list)", ""]))
                target = node
            else:
                target = parent_item
            for i, item in enumerate(data):
                self._fill(target, item, f"[{i}]")
        elif isinstance(data, str) and (data.startswith("{") or data.startswith("[")):
            # Pretty-print embedded JSON strings
            try:
                parsed = json.loads(data)
                node = QTreeWidgetItem([str(key), "(json)"])
                node.setFlags(node.flags() & ~Qt.ItemIsSelectable)
                parent_item.addChild(node)
                self._fill(node, parsed, "")
            except (json.JSONDecodeError, ValueError):
                parent_item.addChild(QTreeWidgetItem([str(key), data]))
        else:
            value = "" if data is None else str(data)
            item = QTreeWidgetItem([str(key), value])
            if len(value) > 120:
                item.setToolTip(1, value)
            parent_item.addChild(item)


class PathPicker(QWidget):
    """QLineEdit + Browse button for choosing a file."""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        button = QPushButton("Browse…")
        button.clicked.connect(self._browse)
        layout.addWidget(self.edit, 1)
        layout.addWidget(button)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select file")
        if path:
            self.edit.setText(path)

    def text(self) -> str:
        return self.edit.text().strip()


class ToolTab(QWidget):
    """Base class for analysis tabs.

    Subclasses describe their inputs and one or more *actions*. Each action
    returns a dict result which is displayed in a JSON tree and can be saved
    as a finding to the currently selected case.
    """

    title = "Tool"

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.pool = WorkerPool(self)
        self._last_result: Optional[Dict[str, Any]] = None
        self._last_module = ""
        self._last_input = ""
        self._assess: Callable[[Dict[str, Any]], Tuple[str, List[str]]] = lambda r: ("info", [])

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QLabel(self.title)
        header.setObjectName("sidebarTitle")
        root.addWidget(header)

        self.form = QVBoxLayout()
        self.form.setSpacing(8)
        root.addLayout(self.form)

        self.build_inputs(self.form)

        self._action_buttons = QHBoxLayout()
        self.add_actions(self._action_buttons)
        self._action_buttons.addStretch(1)
        root.addLayout(self._action_buttons)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        root.addWidget(self.progress)

        self.result_view = JsonView()
        root.addWidget(self.result_view, 1)

        save_row = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save finding to case")
        self.save_btn.setObjectName("primary")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_finding)
        self.save_hint = QLabel("No case selected")
        self.save_hint.setStyleSheet("color: #8a93a3;")
        save_row.addWidget(self.save_btn)
        save_row.addWidget(self.save_hint, 1)
        root.addLayout(save_row)

        self.state.case_changed.connect(self._on_case_changed)
        self._on_case_changed(self.state.current_case)

    def _on_case_changed(self, case):
        if case:
            self.save_hint.setText(f"Will save to case #{case['id']}: {case['name']}")
        else:
            self.save_hint.setText("No case selected — create one in the Cases tab")

    # To override in subclasses -------------------------------------------
    def build_inputs(self, form):
        """Add input widgets to the form layout."""

    def add_actions(self, buttons: QHBoxLayout):
        """Add action buttons; use ``self.add_run_button(label, fn)``."""

    def assess_risk(self, result: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Return (risk_level, tags) for a result. Default: info."""
        return "info", []

    # Helpers for subclasses ------------------------------------------------
    def add_run_button(self, label: str, fn: Callable[[], Any], module: str,
                       input_summary: Optional[Callable[[], str]] = None,
                       assess: Optional[Callable[[Dict[str, Any]], Tuple[str, List[str]]]] = None):
        button = QPushButton(label)
        button.setObjectName("primary")
        button.clicked.connect(
            lambda: self._run_action(fn, module,
                                     input_summary() if input_summary else "",
                                     assess or self.assess_risk)
        )
        self._action_buttons.addWidget(button)
        return button

    # Runtime ---------------------------------------------------------------
    def _run_action(self, fn, module, input_summary, assess):
        if self.pool._workers:  # a task is already running
            return
        self._assess = assess
        self._last_module = module
        self._last_input = input_summary
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.show()
        self.state.set_status(f"Running {module}…")
        self.pool.start(fn, self._on_result, self._on_error)

    def _on_result(self, result):
        self.progress.hide()
        self.progress.setRange(0, 1)
        self._last_result = result if isinstance(result, dict) else {"result": result}
        self.result_view.show_data(self._last_result)
        self.save_btn.setEnabled(self.state.current_case_id is not None)
        err = self._last_result.get("error") if isinstance(self._last_result, dict) else None
        if err:
            self.state.set_status(f"{self._last_module} finished with error: {err}")
        else:
            self.state.set_status(f"{self._last_module} finished")

    def _on_error(self, message: str):
        self.progress.hide()
        self.progress.setRange(0, 1)
        self.result_view.show_data({"error": message})
        self.state.set_status(f"{self._last_module} failed: {message}")

    def _save_finding(self):
        case_id = self.state.current_case_id
        if case_id is None or self._last_result is None:
            return
        from ..core.db import db

        risk, tags = self._assess(self._last_result)
        try:
            db.add_finding(case_id, self._last_module, self._last_input,
                           self._last_result, risk, tags)
            self.state.set_status(
                f"Finding saved to case #{case_id} ({self._last_module}, risk={risk})")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Save failed", str(exc))

    def require_text(self, edit: QLineEdit, name: str) -> Optional[str]:
        value = edit.text().strip()
        if not value:
            self._on_error(f"Please enter a {name}.")
            return None
        return value

    def require_file(self, picker: PathPicker, name: str = "file") -> Optional[str]:
        value = picker.text()
        if not value:
            self._on_error(f"Please choose a {name}.")
            return None
        return value


class CaseSelector(QWidget):
    """Combo box + new-case button bound to AppState."""

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.setMinimumWidth(260)
        self.new_btn = QPushButton("+ New case")
        layout.addWidget(QLabel("Active case:"))
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.new_btn)

        self.combo.currentIndexChanged.connect(self._on_index)
        self.new_btn.clicked.connect(self._new_case_dialog)
        self.state.cases_changed.connect(self.reload)
        self.reload()

    def reload(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        current = self.state.current_case_id
        idx = -1
        for case in self.state.cases:
            label = f"#{case['id']} — {case['name']}"
            self.combo.addItem(label, case["id"])
            if current == case["id"]:
                idx = self.combo.count() - 1
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        self.combo.blockSignals(False)

    def _on_index(self, index: int):
        if index < 0:
            return
        case_id = self.combo.itemData(index)
        if case_id != self.state.current_case_id:
            self.state.select_case(case_id)

    def _new_case_dialog(self):
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("New investigation case")
        form = QFormLayout(dialog)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. Phishing-Incident-2024-001")
        target_edit = QLineEdit()
        target_edit.setPlaceholderText("domain / email / IP (optional)")
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Short description (optional)")
        form.addRow("Case name *", name_edit)
        form.addRow("Target", target_edit)
        form.addRow("Description", desc_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() and name_edit.text().strip():
            try:
                self.state.create_case(
                    name_edit.text().strip(),
                    target_edit.text().strip(),
                    desc_edit.text().strip(),
                )
                self.state.set_status("Case created")
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Could not create case", str(exc))
