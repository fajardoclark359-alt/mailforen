---
title: Risk levels
tags: [risk, scoring, convention]
sourceRefs: [mailforen/cli.py, mailforen/gui/tabs.py, mailforen/core/db.py, mailforen/reports/generator.py]
lastReviewed: 2026-10-29
---

# Risk levels

Four implicit levels, never validated and never enumerated in code: `info`, `low`, `medium`,
`high`. `info` is the default in both the DB column and the report CSS.

## Where risk is calculated
There is **no scoring engine and no numeric points anywhere**. Risk is set at three sites:

1. **CLI `email auth`** (`mailforen/cli.py`):
   ```python
   "medium" if not spf["found"] or not dmarc["found"] else "low"
   ```
2. **GUI `EmailTab._auth_risk`** (`mailforen/gui/tabs.py`) — a *different* rule:
   `high` if both SPF and DMARC missing; `medium` if any of SPF/DMARC/MX missing; `low` if all
   present.
3. **Everything else** hardcodes `"info"` — `email headers`, `domain intel`, `ip intel`,
   `ct search`, `url trace`, `file meta`, `user pivot`, and the GUI's CT/IP tabs.

## Where risk is consumed
- CLI display map: `{"high": "red", "medium": "yellow", "low": "green", "info": "cyan"}`
  (`case show`).
- Report CSS classes `.risk-high #d32f2f`, `.risk-medium #ff9800`, `.risk-low #4caf50`,
  `.risk-info #2196f3` (see [[entities/report-generator]]).
- Stored verbatim in the `findings.risk_level` column ([[entities/case-db]]).

## Implication
The same `.eml`/domain produces different risk levels depending on whether it was triaged via
the CLI or the GUI, and the README's "automated risk scoring for suspicious emails" is
really one boolean on the auth command. Any real scoring work should start by extracting a
single `assess(result) -> (level, tags)` function shared by CLI, GUI, and reports — the GUI's
`ToolTab.assess_risk` hook is the closest existing shape to reuse.
