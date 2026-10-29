---
title: ReportGenerator (JSON/MD/HTML/PDF)
tags: [reports, jinja2, pdf, evidence]
sourceRefs: [mailforen/reports/generator.py]
lastReviewed: 2026-10-29
---

# `ReportGenerator` (`mailforen/reports/generator.py`)

Singleton `report_generator`. Writes into `settings.data_dir / "reports"` (created in
`__init__`).

```python
generate(self, case_id, format="html") -> Path
generate_json(self, data, filename)  / generate_markdown / generate_html / generate_pdf
```

## Data shape
```python
report_data = {
    "case": case, "findings": findings,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "tool": "mailforen v0.1.0",
}
```
`generate` raises `ValueError(f"Case {case_id} not found")` for an unknown case.
Filenames: `report_<case name, spaces→_>_<YYYYmmdd_HHMMSS>.<ext>`.

## Formats
| `--format` | Implementation | Output |
|---|---|---|
| `json` | `json.dump(..., indent=2)` | `.json` |
| `markdown` / `md` | f-string assembly | `.md` |
| `html` | **inline Jinja2 `Template("""…""")`** — no template files on disk | `.html` |
| `pdf` | HTML → `weasyprint` → `pdfkit` | `.pdf`, else falls back to the `.html` path |

Unknown format → `ValueError(f"Unsupported format: {format}")`.

The HTML template carries the `.risk-high/#d32f2f`, `.risk-medium/#ff9800`,
`.risk-low/#4caf50`, `.risk-info/#2196f3` classes (matching [[concepts/risk-levels]]) and a
fixed "authorized use only" disclaimer block.

## Known defects
- `generate_pdf` does `from weasyhtml import HTML` — a typo for `weasyprint`, so that import
  **always** raises `ImportError` and execution always falls through to `pdfkit`.
- Any PDF failure is logged and the **HTML path is returned instead of raising**, so a caller
  asking for `pdf` can silently receive `report_*.html`.
- Files are written without an explicit `encoding=`.
- `"tool": "mailforen v0.1.0"` disagrees with `pyproject.toml`'s `0.2.0`; see
  [[concepts/known-gaps]].
