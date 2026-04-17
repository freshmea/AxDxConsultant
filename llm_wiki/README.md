# Local LLM Wiki

This package builds a markdown-first local knowledge layer over the repository and adds three retrieval tiers:

- graph-first routing from prebuilt JSON metadata
- page-level semantic search with `sentence-transformers` and FAISS
- change-aware fact memory with Mem0, Ollama, and local Qdrant

## Environment

Use the knowledge environment for wiki builds and memory commands:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
```

Required Python packages in that environment:

- `sentence-transformers`
- `faiss-cpu`
- `networkx`
- `graphviz`
- `mem0ai[nlp]`
- `ollama`
- `requests`

Local model requirements for the memory layer:

- Ollama server running on `http://127.0.0.1:11434`
- embedding model `nomic-embed-text`
- local LLM `qwen2.5:1.5b`

## Commands

Build the wiki and regenerate every artifact:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
```

Route a question without writing a query log:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli route "Smart Connections와 Mem0 설정" --root .
```

Run the graph-first query workflow and log token savings:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli ask "Smart Connections와 Mem0 설정" --root . --limit 5
```

Check the local memory stack:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-check --root .
```

Bootstrap community summaries into Mem0 in resumable batches:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-bootstrap --root . --user-id dxax-wiki --mode communities --offset 0 --limit 10
```

Add a short operational fact:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-add "Obsidian Smart Connections is installed and enabled." --root . --user-id dxax-wiki
```

Search the change-aware fact layer:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-search "Smart Connections setup status" --root . --user-id dxax-wiki --top-k 5
```

## Generated Files

- `wiki/system/page_index.json`: compact page catalog
- `wiki/system/link_graph.json`: markdown and wiki-link graph
- `wiki/system/query_cache.json`: query-time cache for graph-first routing
- `wiki/system/structure_index.json`: extracted tags, topics, entities, and neighbors
- `wiki/system/community_graph.json`: GraphRAG-lite community graph
- `wiki/system/community_summaries.json`: community summaries and metadata
- `wiki/system/semantic_index.faiss`: page embedding index
- `wiki/system/semantic_meta.json`: FAISS model and page metadata
- `wiki/system/obsidian_semantic_cache.json`: Smart Connections source-to-source related-note cache exported from `.smart-env/`
- `wiki/system/query_log.json`: machine-readable query history
- `wiki/index.md`: human-readable catalog
- `wiki/graph_report.md`: graph-first corpus report
- `wiki/community_report.md`: community-level report
- `wiki/query_log.md`: token-savings log
- `wiki/log.md`: append-only maintenance log
- `wiki/system/link_graph.svg`: Graphviz rendering

## Ignore Rules

The builder reads `.llmwikiignore` from the repository root and skips matching files and folders before indexing.

Example:

```text
tmp/
.obsidian/
wiki/
output/
drafts/
**/*_backup.md
```

## Retrieval Flow

1. Build the graph, community summaries, and semantic index once.
2. Use `ask` or `route` before opening raw markdown.
3. Read `query_cache.json`, `community_summaries.json`, `semantic_meta.json`, and `obsidian_semantic_cache.json` first.
4. Open only the suggested markdown files.
5. Let `ask` use the `smart_connections_bonus` from the exported Obsidian cache as a secondary reranking signal.
6. Use `memory-search` for setup state, changing facts, or recent operational changes.
7. Rebuild after structural changes and re-bootstrap memory if the operational state changed materially.

## Related Docs

- `llm_wiki/OBSIDIAN_SMART_CONNECTIONS_SETUP.md`
- `memory_layer/README.md`
- `skills/wiki-llm-setup/SKILL.md`
- `skills/troubleshooting.md`
