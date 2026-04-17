# LLM Wiki Schema

This repository uses a local LLM Wiki pattern inspired by Andrej Karpathy's `llm-wiki.md` gist.

## Layers

1. `raw` is the source-of-truth layer. In this repository the raw sources are the existing markdown files already present in the workspace.
2. `wiki` is the maintained knowledge layer. Generated indexes, graph files, summaries, and operator notes live here.
3. `AGENTS.md` is the schema. It tells the agent how to maintain the wiki.

## Operating Rules

1. Never edit raw source files during indexing.
2. Update `wiki/system/page_index.json`, `wiki/system/link_graph.json`, `wiki/system/query_cache.json`, `wiki/system/structure_index.json`, `wiki/system/community_graph.json`, `wiki/system/community_summaries.json`, `wiki/system/semantic_index.faiss`, `wiki/system/semantic_meta.json`, `wiki/system/obsidian_semantic_cache.json`, `wiki/index.md`, `wiki/graph_report.md`, `wiki/community_report.md`, and `wiki/log.md` together.
3. Prefer answering questions by reading the JSON index/graph first, then opening only a small set of markdown files.
4. Treat markdown links and wiki links as first-class edges.
5. Preserve relative paths from the repository root in generated metadata.
6. Respect `.llmwikiignore` when deciding which markdown files belong to the wiki corpus.
7. Keep the semantic index, Smart Connections bridge cache, and GraphRAG-lite community summaries in sync with the page and link graph outputs.
8. Keep change-aware facts in `memory_layer/` and query them through Mem0 before re-reading large parts of the corpus when the question is about setup state or recent changes.

## Unicode And Chart Rules

1. When generating Korean markdown or report files from scripts, write them as UTF-8 and prefer `utf-8-sig` on Windows-facing deliverables.
2. Do not rely on the shell console to verify Korean text because PowerShell display encoding may show mojibake even when the file bytes are correct.
3. If a script-generated Korean string has any risk of console/codepage corruption, build the text from Unicode escape sequences and decode it inside Python before writing the file.
4. When generating charts with Korean labels, explicitly load a Korean font file such as `C:\Windows\Fonts\NotoSansKR-Regular.ttf` and apply that font to titles, axes, tick labels, legends, and annotations.
5. After creating a Korean report or chart, verify the output by checking file bytes or rendering the image instead of trusting terminal output alone.

## Query Workflow

1. Load `wiki/system/query_cache.json`.
2. Rank candidate pages using title, summary, headings, tags, topics, entities, path tokens, graph neighbors, semantic similarity, and community summaries.
3. Prefer the `ask` workflow so the graph-first route and token savings are logged.
4. Read only the top-ranked markdown pages that are needed to answer the question.
5. If the question is about evolving configuration or operational state, also check `memory-search` before reading many raw pages.
6. If a useful synthesis is created, store it back into `wiki/notes/`.

## Maintenance Workflow

1. Rebuild indexes after adding or moving markdown files.
2. Check for orphan pages and unresolved links.
3. Keep `wiki/log.md` append-only.
4. Rebuild the semantic FAISS index and community summaries as part of every wiki build.
5. Keep Mem0 bootstraps resumable by using offsets and small batches when local Qdrant is in use.
