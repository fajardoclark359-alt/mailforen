---
title: Passive-first gating (unimplemented)
tags: [safety, ethics, active-checks, unimplemented]
sourceRefs: [mailforen/core/config.py, mailforen/cli.py, README.md, DISCLAIMER.md]
lastReviewed: 2026-10-29
---

# The "passive-first" policy and why it is unenforced

README: *"All checks are passive by default; active checks require the `--unsafe` flag with
explicit confirmation."* `DISCLAIMER.md` repeats it.

## What the code actually has
- `Settings.allow_unsafe: bool = False` (`MAILFOREN_ALLOW_UNSAFE` env var) — **declared and
  never read** by any module.
- **No `--unsafe` option exists** anywhere in the Typer tree ([[entities/cli]]).
- **No `typer.confirm`** and therefore no confirmation prompt in the codebase.

## Why nothing has broken yet
The toolkit contains no active capability at all: no SMTP verification, no mailbox login, no
credential testing, no port scanning. The "active" surface is ordinary outbound HTTP:
- `GET https://ipinfo.io/{ip}/json` ([[entities/ip-intel]])
- `GET https://crt.sh/?q=%.{domain}&output=json` ([[entities/ct-search]])
- arbitrary `HEAD`/`GET` on user-supplied URLs ([[entities/url-tracer]])
- DNS queries to the system resolver ([[entities/email-auth-checker]], [[entities/domain-intel]])

`user pivot` makes no requests at all — it only string-builds profile URLs.

## Consequence for changes
Any new feature that *does* connect to a target (e.g. real SMTP RCPT probing, DKIM selector
guessing, mailbox enumeration) must also introduce the gate, because nothing today would stop
it from running by default. The natural place is a single decorator or Typer callback reading
`settings.allow_unsafe` plus an explicit confirmation, applied at the CLI boundary so the
modules stay transport-agnostic.
