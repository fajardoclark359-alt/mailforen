---
title: Case-centric workflow
tags: [architecture, workflow, cli, persistence]
sourceRefs: [mailforen/cli.py, mailforen/core/db.py, mailforen/reports/generator.py]
lastReviewed: 2026-10-29
---

# Case-centric workflow

Every feature answers to the same loop: **case → analysis → finding → report**.

```
case new "Phish 2026-10" --target victim@example.com     # creates a row in `cases`
        │
email headers mail.eml -c 1                              # module run, result dict
domain intel example.com -c 1                            # → db.add_finding(case_id, module, input, result, risk, tags)
        │
case show 1                                              # table of findings, risk-coloured
report generate --case-id 1 --format html                # renders all findings via Jinja2 → ~/.mailforen/reports/
```

## Invariants
- The `-c/--case-id` option is uniform across all analysis commands ([[entities/cli]]); when
  present, results are persisted through `db.add_finding`, otherwise they are printed only.
- Module identity is a dotted string stored in `findings.module`: `email.headers`,
  `email.auth`, `domain.intel`, `ip.intel`, `ct.search`, `url.trace`, `file.meta`,
  `user.pivot`. Nothing validates these names.
- Findings are append-only; there is no way to correct or retract one ([[entities/case-db]]).
- The report generator joins `cases` + `findings` by `case_id` and needs no other state
  ([[entities/report-generator]]).

## Where it leaks
- Module singletons are imported at module scope in `cli.py`, so every command instantiates
  the whole toolkit and triggers `~/.mailforen` creation ([[entities/core-config]]).
- Nothing records *which network requests* a finding involved: the `requests` table exists but
  is never written. Evidence chain-of-custody is therefore case + finding JSON only.
- The GUI replicates this loop in its own `AppState` ([[entities/gui]]) rather than sharing a
  service layer.
