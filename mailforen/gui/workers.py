"""Background workers so network/DNS tasks never block the GUI thread."""

import traceback
from typing import Any, Callable, Optional

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Run a callable in a background thread and emit the outcome.

    Signals:
        done(object): emitted with the return value of ``fn``.
        failed(str):  emitted with a human-readable error message.
    """

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args

    def run(self) -> None:  # pragma: no cover - exercised via threads
        try:
            result = self._fn(*self._args)
            self.done.emit(result)
        except Exception as exc:  # noqa: BLE001 - surface any failure to UI
            message = str(exc) or exc.__class__.__name__
            traceback.print_exc()
            self.failed.emit(message)


class WorkerPool:
    """Keeps references to running workers and cleans them up on finish."""

    def __init__(self, parent=None):
        self._workers: list[Worker] = []
        self._parent = parent

    def start(
        self,
        fn: Callable[..., Any],
        on_done: Callable[[Any], None],
        on_fail: Optional[Callable[[str], None]] = None,
        *args,
    ) -> Worker:
        worker = Worker(fn, *args, parent=self._parent)
        self._workers.append(worker)

        def _cleanup():
            if worker in self._workers:
                self._workers.remove(worker)

        worker.done.connect(on_done)
        if on_fail is not None:
            worker.failed.connect(on_fail)
        worker.finished.connect(_cleanup)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        return worker
