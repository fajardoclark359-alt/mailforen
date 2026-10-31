---
title: PySide6 desktop GUI (untracked)
tags: [gui, pyside6, qt, untracked]
sourceRefs: [mailforen/gui/app.py, mailforen/gui/main_window.py, mailforen/gui/tabs.py, mailforen/gui/components.py, mailforen/gui/state.py, mailforen/gui/workers.py, mailforen/gui/theme.py]
lastReviewed: 2026-10-29
---

# Desktop GUI (`mailforen/gui/`, 9 files, ~1,380 LOC)

**Status: entirely untracked in git** (`??` in `git status`) even though `pyproject.toml`
already declares `PySide6>=6.8.0` and the `mailforen-gui = mailforen.gui.app:main` entry
point. Nothing in `master` contains this code.

## Structure
| File | Lines | Contents |
|---|---|---|
| `app.py` | 32 | `main() -> int` — QApplication bootstrap; `_version()` returns literal `"0.1.0"` |
| `main_window.py` | 116 | `MainWindow(QMainWindow)`: sidebar list + `QStackedWidget` pages, `_switch_page(row)` |
| `tabs.py` | 549 | `CasesTab`, `EmailTab`, `DomainTab`, `IPTab`, `URLTab`, … one `ToolTab` subclass per CLI module |
| `components.py` | 334 | `JsonView(QTreeWidget)`, `PathPicker`, `CaseSelector`, and the `ToolTab` base class |
| `state.py` | 69 | `AppState(QObject)` — case list, `current_case_id`, `select_case()`, `set_status()` |
| `workers.py` | 62 | `Worker(QThread)` + `WorkerPool` for off-UI-thread DNS/HTTP |
| `theme.py` | 216 | dark palette + QSS, `apply_theme(app)` |
| `__main__.py` | 8 | `python -m mailforen.gui` shim |
| `__init__.py` | 9 | package docstring/exports |

## Design
`ToolTab` (in `components.py`) is the extension point: subclasses override `build_inputs(form)`
and `add_actions(buttons)`, then call
`add_run_button(label, fn, module, input_summary=..., assess=...)`. `_run_action` dispatches to
`WorkerPool`, `_on_result` renders JSON via `JsonView`, and `_save_finding` persists to
[[entities/case-db]] with the tags/risk returned by `assess_risk`.

## Second risk implementation
`ToolTab.assess_risk` defaults to `("info", [])`, but `EmailTab._auth_risk` implements a
**different rule than the CLI**: `high` when both SPF and DMARC are missing, `medium` when any
of SPF/DMARC/MX is missing, `low` when all present. The CLI produces only `medium`/`low` for
the same input. See [[concepts/risk-levels]].

`_ct_risk` and `_ip_risk` always return `info`, differing only in tags
(`subdomains:<n>`, `ct-empty`, `org:<name>`).

## Running it
`mailforen-gui` (after `pip install -e .`) or `python -m mailforen.gui`. Requires a working
Qt platform plugin; it is not exercised by any test — there are none (see
[[concepts/known-gaps]]).
