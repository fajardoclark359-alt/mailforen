---
title: CLI command tree
tags: [cli, typer, entry-point]
sourceRefs: [mailforen/cli.py, pyproject.toml]
lastReviewed: 2026-10-29
---

# CLI command tree (`mailforen/cli.py`, ~393 LOC)

A single Typer `app` (`add_completion=False`) with nine registered sub-apps:
`case`, `email`, `domain`, `ip`, `ct`, `url`, `user`, `file`, `report`.

## Commands

| Command | Shape | Notes |
|---|---|---|
| `version` | no args | Rich panel, literal text `mailforen v0.1.0` |
| `disclaimer` | no args | prints `<repo root>/DISCLAIMER.md` (`Path(__file__).parent.parent`) |
| `case new` | `NAME` positional; `-t/--target`, `-d/--desc` | relies on `UNIQUE(name)` in [[entities/case-db]] |
| `case list` | — | Rich table: ID / Name / Target / Status / Created |
| `case show` | `CASE_ID` positional | risk→colour map defined here |
| `email headers` | `FILE` positional (`.eml`); `-c/--case-id` | module `email.headers`, risk `info` |
| `email auth` | `DOMAIN` positional; `-c` | only command that computes a non-`info` risk |
| `domain intel` | `DOMAIN`; `-c` | module `domain.intel` |
| `ip intel` | `IP`; `-c` | merges `get_info` + `get_asn_info` results |
| `ct search` | `DOMAIN`; `-c` | prints at most 50 subdomains, then "... and N more" |
| `url trace` | `URL`; `-c` | module `url.trace` |
| `file meta` | `FILE`; `-c` | first 20 EXIF tags, each truncated to 60 chars |
| `user pivot` | `USERNAME`; `-c` | **no network call** — just builds profile URLs |
| `report generate` | `-c/--case-id` **required option**; `-f/--format` default `html` | see [[entities/report-generator]] |

## Conventions
- Every analysis command takes the same optional `-c/--case-id`; when present it calls
  `db.add_finding(...)` and prints `✓ Added to case N`.
- Failure style: print `[red]✗[/red] <msg>` then `raise typer.Exit(1)`.
- Commands are thin: parse args → call a module singleton → render with Rich. No business
  logic lives here (the one exception is the risk rule in `email auth`).

## Drift
The README documents `email headers analyze <file>` and `email auth check <domain>`; neither
`analyze` nor `check` subcommand exists. See [[concepts/known-gaps]].
