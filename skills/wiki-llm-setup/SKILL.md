---
name: wiki-llm-setup
description: "Set up or repair a local markdown-first LLM wiki with graph-first routing, FAISS semantic search, GraphRAG-lite community summaries, .llmwikiignore exclusions, Obsidian graph filtering, and a Mem0 change-aware fact layer."
---

# Wiki LLM Setup

Recreate the workspace in this order.

## Architecture stance

Keep the existing repository stack in place:

- markdown wiki graph
- FAISS semantic retrieval
- GraphRAG-lite community summaries
- Mem0 change-aware fact layer

If Graphify-style features are added, absorb them into this stack instead of replacing it.
Use `../graphify-code-wiki/SKILL.md` for code graph extraction, code query CLI, code-aware routing, and verification of that layer.

## 1. Confirm the required layout

Expect these files and folders:

- `AGENTS.md`
- `.llmwikiignore`
- `.venv-knowledge/`
- `llm_wiki/indexer.py`
- `llm_wiki/semantic.py`
- `llm_wiki/community.py`
- `llm_wiki/memory_layer.py`
- `llm_wiki/cli.py`
- `llm_wiki/README.md`
- `llm_wiki/OBSIDIAN_SMART_CONNECTIONS_SETUP.md`
- `memory_layer/mem0_config.json`
- `.obsidian/graph.json`

If any are missing, rebuild them before trusting the graph or memory layer.

## 2. Prepare the Python environment

Use the dedicated knowledge environment:

```powershell
.\.venv-knowledge\Scripts\python.exe -V
```

Required packages:

- `sentence-transformers`
- `faiss-cpu`
- `networkx`
- `graphviz`
- `mem0ai[nlp]`
- `ollama`
- `requests`

## 3. Build the wiki artifacts

Run:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
```

The build is healthy when these files exist:

- `wiki/system/page_index.json`
- `wiki/system/link_graph.json`
- `wiki/system/query_cache.json`
- `wiki/system/structure_index.json`
- `wiki/system/community_graph.json`
- `wiki/system/community_summaries.json`
- `wiki/system/semantic_index.faiss`
- `wiki/system/semantic_meta.json`
- `wiki/system/query_log.json`
- `wiki/index.md`
- `wiki/graph_report.md`
- `wiki/community_report.md`
- `wiki/query_log.md`
- `wiki/log.md`
- `wiki/system/link_graph.svg`

## 4. Keep query flow graph-first

Do not read the full markdown corpus first.

Use:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli ask "질문" --root . --limit 5
```

Expected behavior:

- rank pages from title, summary, headings, tags, topics, entities, path tokens, graph neighbors, semantic hits, and community summaries
- estimate full-corpus tokens vs targeted-read tokens
- log the result to `wiki/system/query_log.json` and `wiki/query_log.md`

Use `route` only when candidate routing is needed without logging.

## 5. Maintain explicit ignore rules

The builder must honor `.llmwikiignore`.

If a folder should not appear in the wiki graph, add it there and rebuild.

## 6. Keep Obsidian graph filtering separate

`.llmwikiignore` does not affect Obsidian.

Mirror hidden folders in `.obsidian/graph.json` with negative `path:` filters. Read `llm_wiki/OBSIDIAN_SMART_CONNECTIONS_SETUP.md` before setting up Smart Connections or graph filters.

## 7. Add the change-aware fact layer

Mem0 is for evolving operational facts, not for replacing the markdown wiki.

Check Ollama first:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-check --root .
```

Expected local models:

- `nomic-embed-text`
- `qwen2.5:1.5b`

Bootstrap the memory layer in small batches because local Qdrant is single-process:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-bootstrap --root . --user-id dxax-wiki --mode communities --offset 0 --limit 10
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-bootstrap --root . --user-id dxax-wiki --mode communities --offset 10 --limit 10
```

Use `memory-search` for setup-state questions before opening many raw files.

## 8. Repair unresolved links before expanding the corpus

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

## 9. Re-verify after every structural change

After changing links, ignore rules, memory config, or skill docs:

1. rebuild the wiki
2. confirm unresolved links are `0` or intentionally excluded
3. run one `ask` query
4. run one `memory-search` query
5. verify token savings are logged

For failure cases, read `../troubleshooting.md`.
