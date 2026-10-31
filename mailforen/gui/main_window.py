"""Main application window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .state import AppState
from .tabs import (
    CasesTab,
    DomainTab,
    EmailTab,
    FileTab,
    FindingsTab,
    IPTab,
    ReportsTab,
    URLTab,
    UserTab,
)

DISCLAIMER = (
    "⚠ For authorized investigations only — passive OSINT on targets you are "
    "permitted to assess. Unauthorized use may be illegal."
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = AppState(self)

        self.setWindowTitle("mailforen — Email Forensics & OSINT Toolkit")
        self.resize(1180, 760)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 6)
        layout.setSpacing(10)

        # Sidebar -----------------------------------------------------------
        sidebar = QVBoxLayout()
        brand = QLabel("mailforen")
        brand.setObjectName("sidebarTitle")
        sidebar.addWidget(brand)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        for label, icon in [
            ("🗂  Cases", "🗂"),
            ("📧  Email Forensics", "📧"),
            ("🌐  Domain Intel", "🌐"),
            ("🛰  IP Intel", "🛰"),
            ("📜  CT Search", "📜"),
            ("➡  URL Trace", "➡"),
            ("📎  File Metadata", "📎"),
            ("🧩  Username Pivot", "🧩"),
            ("🔎  Findings", "🔎"),
            ("📄  Reports", "📄"),
        ]:
            self.sidebar.addItem(label)
        sidebar.addWidget(self.sidebar, 1)

        disclaimer = QLabel(DISCLAIMER)
        disclaimer.setObjectName("disclaimer")
        disclaimer.setWordWrap(True)
        sidebar.addWidget(disclaimer)
        layout.addLayout(sidebar)

        # Pages -------------------------------------------------------------
        self.pages = QStackedWidget()
        ct_tab = DomainTab(self.state)
        ct_tab.title = "CT Search"
        page_classes = [
            lambda: CasesTab(self.state),
            lambda: EmailTab(self.state),
            lambda: DomainTab(self.state),
            lambda: IPTab(self.state),
            lambda: ct_tab,
            lambda: URLTab(self.state),
            lambda: FileTab(self.state),
            lambda: UserTab(self.state),
            lambda: FindingsTab(self.state),
            lambda: ReportsTab(self.state),
        ]
        self.tabs = []
        for factory in page_classes:
            tab = factory()
            self.tabs.append(tab)
            self.pages.addWidget(tab)

        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        # Status bar ---------------------------------------------------------
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_message = QLabel("Ready — select or create a case to begin")
        self.status.addWidget(self.status_message, 1)

        # Wiring --------------------------------------------------------------
        self.sidebar.currentRowChanged.connect(self._switch_page)
        self.state.status_message.connect(self.status_message.setText)
        self.sidebar.setCurrentRow(0)
        self.state.refresh_cases()

    def _switch_page(self, row: int):
        if 0 <= row < self.pages.count():
            self.pages.setCurrentIndex(row)
