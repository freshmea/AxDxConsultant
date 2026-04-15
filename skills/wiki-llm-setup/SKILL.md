---
name: wiki-llm-setup
description: "Set up or repair a local markdown-first LLM wiki in this repository pattern: root AGENTS.md guidance, markdown-to-JSON indexing, .llmwikiignore exclusions, graph-first query routing, and Obsidian graph filtering. Use when Codex needs to install, rebuild, validate, or migrate the wiki LLM workflow for another workspace."
---

# Wiki LLM Setup

Recreate the wiki layer in this order.

## 1. Confirm the required layout

Expect these files:

- `AGENTS.md`
- `.llmwikiignore`
- `llm_wiki/indexer.py`
- `llm_wiki/cli.py`
- `llm_wiki/README.md`
- `.obsidian/graph.json`

If any are missing, rebuild them before trusting the graph.

## 2. Build the wiki artifacts

Run:

```powershell
python -m llm_wiki.cli build --root . --render-graph
```

The build is healthy when these files exist:

- `wiki/system/page_index.json`
- `wiki/system/link_graph.json`
- `wiki/system/query_cache.json`
- `wiki/system/structure_index.json`
- `wiki/system/query_log.json`
- `wiki/index.md`
- `wiki/graph_report.md`
- `wiki/query_log.md`
- `wiki/log.md`
- `wiki/system/link_graph.svg`

## 3. Keep query flow graph-first

Do not read the full markdown corpus first.

Use:

```powershell
python -m llm_wiki.cli ask "질문" --root .
```

Expected behavior:

- rank pages from title, summary, headings, tags, topics, entities, path tokens, and graph neighbors
- estimate full-corpus tokens vs targeted-read tokens
- log the result to `wiki/system/query_log.json` and `wiki/query_log.md`

Use `route` only when candidate routing is needed without logging.

## 4. Maintain explicit ignore rules

The builder must honor `.llmwikiignore`.

Current exclusions for this workspace include:

```text
.git/
.mypy_cache/
.obsidian/
wiki/
output/
tmp/
나의업무분석/
.venv-whisper/
local_whisper/
**/*_backup.md
**/*.pdf.md
```

If a folder should not appear in the wiki graph, add it here and rebuild.

## 5. Keep Obsidian graph filtering separate

`.llmwikiignore` does not affect Obsidian.

Mirror hidden folders in `.obsidian/graph.json` with negative `path:` filters, for example:

```json
"search": "-path:\"나의업무분석\" -path:\"tmp\" -path:\"wiki\" -path:\"output\""
```

Reload Obsidian if the graph view still shows stale nodes.

## 6. Repair unresolved links before expanding the corpus

Check unresolved links from the generated graph:

```powershell
@'
import json, pathlib
obj = json.loads(pathlib.Path("wiki/system/link_graph.json").read_text(encoding="utf-8"))
print(len(obj.get("unresolved_links", [])))
for item in obj.get("unresolved_links", []):
    print(item.get("source_path"), "=>", item.get("target"))
'@ | python -
```

Fix source markdown links, decode URL-style local links, or add hub pages when same-date notes are isolated.

## 7. Re-verify after every structural change

After changing links, ignore rules, or skill docs:

1. rebuild the wiki
2. confirm unresolved links are `0` or intentionally excluded
3. run one `ask` query
4. verify token savings are logged

For failure cases, read `../troubleshooting.md`.
