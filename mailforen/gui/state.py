"""Shared application state (selected case, findings context)."""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal


class AppState(QObject):
    """Holds globally shared GUI state.

    The selected case is shared by every tab: tool tabs save findings to it,
    the findings/report tabs read from it.
    """

    case_changed = Signal(object)  # emits the selected case dict or None
    cases_changed = Signal()
    status_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cases: List[Dict[str, Any]] = []
        self._current: Optional[Dict[str, Any]] = None

    # -- cases -----------------------------------------------------------
    @property
    def cases(self) -> List[Dict[str, Any]]:
        return self._cases

    def refresh_cases(self) -> None:
        from ..core.db import db

        self._cases = db.list_cases()
        if self._cases:
            if self._current is None or not any(
                c["id"] == self._current["id"] for c in self._cases
            ):
                self.select_case(self._cases[0]["id"], notify=False)
        else:
            self._current = None
        self.cases_changed.emit()
        self.case_changed.emit(self._current)

    def create_case(self, name: str, target: str = "", description: str = "") -> int:
        from ..core.db import db

        case_id = db.create_case(name, target or None, description or None)
        self.refresh_cases()
        self.select_case(case_id)
        return case_id

    def select_case(self, case_id: int, notify: bool = True) -> None:
        from ..core.db import db

        case = db.get_case(case_id)
        self._current = case
        if notify:
            self.case_changed.emit(self._current)

    @property
    def current_case(self) -> Optional[Dict[str, Any]]:
        return self._current

    @property
    def current_case_id(self) -> Optional[int]:
        return self._current["id"] if self._current else None

    # -- status bar --------------------------------------------------------
    def set_status(self, message: str) -> None:
        self.status_message.emit(message)
