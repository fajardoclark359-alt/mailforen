---
title: OpenCodeRAG runtime on this machine
tags: [tooling, rag, environment, opencode]
sourceRefs: [~/.cache/opencode/npm/opencode-rag-plugin@latest/, ~/.config/opencode/opencode.json, .opencode/rag_db]
lastReviewed: 2026-10-29
---

# OpenCodeRAG runtime (environment, not project code)

The `search_semantic` / `get_file_skeleton` / `find_usages` / `describe_image` /
`recall_quirks` tools come from the **`opencode-rag-plugin`** npm plugin, listed by bare name
in `~/.config/opencode/opencode.json` → `plugins`.

## Where it is installed
opencode resolves bare plugin names itself; it does **not** use a global npm install. The
resolved copy lives in a per-spec cache:

```
~/.cache/opencode/npm/<pkg>@latest/<timestamp>/node_modules/<pkg>
```

For this machine: `opencode-rag-plugin@latest/1792064420617/` — currently **2.12.2**
(upgraded from 2.4.4 on 2026-10-29; the old tree is kept as `1792064420617.bak-2.4.4`).
The cache dir's `package.json` pins the concrete version opencode installed.

## Runtime layout
- Vector store: **`./.opencode/rag_db`** (LanceDB), per workspace. Index state for this repo
  lives there and was ~empty at upgrade time (`__manifest` only, 24 KB).
- Config resolution order (2.12.2): defaults → `~/.config/opencode/opencode-rag.json` →
  workspace `.opencode/opencode-rag.json` → legacy root `opencode-rag.json`.
  This repo has none of those files yet.
- Default embedder: **`ollama` / `qwen3-embedding:0.6b`**.

## Blocking issue: no embedding backend
**Ollama is not installed on this machine** (`which ollama` empty, `ollama` service inactive,
nothing listening on `127.0.0.1:11434`). Consequences: indexing cannot embed, `recall_quirks`
returns "backend down", and `search_semantic` degrades. Options: install Ollama and pull
`qwen3-embedding:0.6b`, or point `embedding.provider`/`baseUrl` at an API-compatible embedder
in `opencode-rag.json`.

## CLI
`opencode-rag` is not on `PATH` (no global install). Run the cached copy directly:
```bash
node ~/.cache/opencode/npm/opencode-rag-plugin@latest/*/node_modules/opencode-rag-plugin/dist/cli/index.js --version
```
Useful subcommands: `setup` (runtime check + workspace init), `init` (re-sync workspace),
`update`, `index`, `query "…"`, `decide`. `setup` writes `.opencode/opencode-rag.json` and a
skill file — it also touches the global opencode config, so back that up first.

## Upgrade procedure that works here
1. `tar czf` the workspace `.opencode/rag_db` (schemas may change across versions).
2. `mv` the cached `<timestamp>` dir aside.
3. Recreate it with `package.json` pinning the target version, then `npm install` inside it.
4. Smoke-test: `node dist/cli/index.js --version`, `import("@lancedb/lancedb")`,
   `import('./dist/plugin-entry.js')`.
5. Restart opencode — plugins load at startup only.
