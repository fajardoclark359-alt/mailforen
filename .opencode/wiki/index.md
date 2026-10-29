# mailforen wiki — index

Content catalog for the `mailforen` codebase: a Python CLI (Typer + Rich) OSINT toolkit
for email forensics, plus an uncommitted PySide6 desktop GUI.

## Overview
- [[concepts/case-workflow]] — the case → analysis → finding → report loop every command follows
- [[concepts/known-gaps]] — what the README promises that the code does not do

## Concepts
- [[concepts/passive-first-gating]] — the "passive by default, `--unsafe` opt-in" policy and why it is unenforced
- [[concepts/risk-levels]] — the four-level risk vocabulary and the single rule that produces it
- [[concepts/opencode-rag-runtime]] — how the local RAG plugin is installed for this machine

## Entities
- [[entities/cli]] — `mailforen/cli.py`, the whole command tree
- [[entities/core-config]] — `Settings` (pydantic-settings) and on-disk data locations
- [[entities/case-db]] — `CaseDB`, the SQLite case/evidence store
- [[entities/http-client]] — `HTTPClient`, the thin httpx wrapper
- [[entities/header-analyzer]] — `.eml` header + Received-chain parsing
- [[entities/email-auth-checker]] — SPF / DMARC / MX over raw DNS
- [[entities/domain-intel]] — DNS record harvesting
- [[entities/ip-intel]] — reverse DNS + ipinfo.io
- [[entities/ct-search]] — certificate transparency via crt.sh
- [[entities/url-tracer]] — redirect-chain tracing
- [[entities/file-meta-extractor]] — file stats + EXIF
- [[entities/report-generator]] — JSON / Markdown / HTML / PDF reports
- [[entities/gui]] — the PySide6 desktop app (untracked working tree)

## Sources
- (none yet)
