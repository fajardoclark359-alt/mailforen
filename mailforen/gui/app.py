"""GUI entry point: ``mailforen-gui`` or ``python -m mailforen.gui``."""

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from .main_window import MainWindow
    from .theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("mailforen")
    app.setApplicationVersion(_version())
    apply_theme(app)

    window = MainWindow()
    window.show()
    return app.exec()


def _version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("mailforen")
    except PackageNotFoundError:
        return "0.1.0"


if __name__ == "__main__":
    sys.exit(main())
