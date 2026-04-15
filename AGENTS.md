# LLM Wiki Schema

This repository uses a local LLM Wiki pattern inspired by Andrej Karpathy's `llm-wiki.md` gist.

## Layers

1. `raw` is the source-of-truth layer. In this repository the raw sources are the existing markdown files already present in the workspace.
2. `wiki` is the maintained knowledge layer. Generated indexes, graph files, summaries, and operator notes live here.
3. `AGENTS.md` is the schema. It tells the agent how to maintain the wiki.

## Operating Rules

1. Never edit raw source files during indexing.
2. Update `wiki/system/page_index.json`, `wiki/system/link_graph.json`, `wiki/system/query_cache.json`, `wiki/system/structure_index.json`, `wiki/index.md`, `wiki/graph_report.md`, and `wiki/log.md` together.
3. Prefer answering questions by reading the JSON index/graph first, then opening only a small set of markdown files.
4. Treat markdown links and wiki links as first-class edges.
5. Preserve relative paths from the repository root in generated metadata.
6. Respect `.llmwikiignore` when deciding which markdown files belong to the wiki corpus.

## Query Workflow

1. Load `wiki/system/query_cache.json`.
2. Rank candidate pages using title, summary, headings, tags, topics, entities, path tokens, and graph neighbors.
3. Prefer the `ask` workflow so the graph-first route and token savings are logged.
4. Read only the top-ranked markdown pages that are needed to answer the question.
5. If a useful synthesis is created, store it back into `wiki/notes/`.

## Maintenance Workflow

1. Rebuild indexes after adding or moving markdown files.
2. Check for orphan pages and unresolved links.
3. Keep `wiki/log.md` append-only.
