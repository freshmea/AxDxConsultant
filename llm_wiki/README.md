# Local LLM Wiki

This package builds a lightweight Karpathy-style wiki layer over the markdown files in this repository.

## Commands

```powershell
python -m llm_wiki.cli build --root . --render-graph
python -m llm_wiki.cli route "수중드론 사업화" --root .
```

## Generated Files

- `wiki/system/page_index.json`: compact page catalog
- `wiki/system/link_graph.json`: markdown link graph
- `wiki/system/query_cache.json`: query-time cache for low-token routing
- `wiki/index.md`: human-readable catalog
- `wiki/log.md`: append-only maintenance log
- `wiki/system/link_graph.svg`: graphviz rendering

## Ignore Rules

The builder reads `.llmwikiignore` from the repository root and skips matching files and folders before indexing.

Example:

```text
tmp/
.obsidian/
drafts/
**/*_backup.md
```

## Token-Saving Flow

1. Build the JSON cache once.
2. For each question, run `route` first.
3. Open only the suggested markdown files instead of the entire corpus.
