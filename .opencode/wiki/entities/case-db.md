---
title: CaseDB — SQLite case store
tags: [db, sqlite, persistence]
sourceRefs: [mailforen/core/db.py]
lastReviewed: 2026-10-29
---

# `CaseDB` (`mailforen/core/db.py`)

Module-level singleton `db = CaseDB()`. Database path is `settings.data_dir / "cases.db"`
(default `~/.mailforen/cases.db`); `init_db()` runs `CREATE TABLE IF NOT EXISTS` on
construction. Every method opens a fresh `sqlite3.connect()`.

## API
```python
init_db(self)
create_case(self, name, target=None, description=None) -> int
list_cases(self) -> List[Dict]
get_case(self, case_id) -> Optional[Dict]
add_finding(self, case_id, module, input_data, result: dict,
            risk_level="info", tags: List[str] = None, notes: str = None) -> int
get_findings(self, case_id) -> List[Dict]
```
No update, delete, or close-case methods.

## Schema
`cases` — `id` (PK autoincrement), `name` TEXT **UNIQUE** NOT NULL, `target`, `description`,
`created_at`, `updated_at` (both `DEFAULT CURRENT_TIMESTAMP`), `status` TEXT default `'open'`.

`findings` — `id` (PK), `case_id` (FK → cases.id), `module` NOT NULL, `input_data`,
`result_json` TEXT, `risk_level` default `'info'`, `tags` TEXT, `notes`, `timestamp`.

`requests` — `id`, `case_id`, `url`, `method`, `module`, `timestamp`, `response_code`.

## Behaviour worth knowing
- **`requests` is dead weight**: nothing inserts or queries it. The README's "evidence and
  request tracking" is not implemented.
- Foreign keys are declarative only — no `PRAGMA foreign_keys=ON`, so `case_id` is never
  validated. A finding can point at a nonexistent case.
- `create_case` catches `sqlite3.IntegrityError` only to log `Case '<name>' already exists`,
  then re-raises; the CLI surfaces that as a traceback-worthy `typer.Exit`.
- `updated_at` and `status` are never written after insert.
- `add_finding` stores `json.dumps(result)` in `result_json` and joins `tags` with `,`;
  `get_findings` re-parses into `finding["result"]`, splits tags, returns newest first
  (`ORDER BY timestamp DESC`).

Used by [[entities/report-generator]] and every command in [[entities/cli]].
