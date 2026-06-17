# LLM Wiki Schema

This repository uses a local LLM Wiki pattern inspired by Andrej Karpathy's `llm-wiki.md` gist.

## Layers

1. `raw` is the source-of-truth layer. In this repository the raw sources are the existing markdown files already present in the workspace.
2. `wiki` is the maintained knowledge layer. Generated indexes, graph files, summaries, and operator notes live here.
3. `AGENTS.md` is the schema. It tells the agent how to maintain the wiki.

## Operating Rules

1. Never edit raw source files during indexing.
2. Update `wiki/system/page_index.json`, `wiki/system/link_graph.json`, `wiki/system/query_cache.json`, `wiki/system/structure_index.json`, `wiki/system/community_graph.json`, `wiki/system/community_summaries.json`, `wiki/system/code_graph.json`, `wiki/system/code_graph_meta.json`, `wiki/system/semantic_index.faiss`, `wiki/system/semantic_meta.json`, `wiki/system/obsidian_semantic_cache.json`, `wiki/system/query_log.json`, `wiki/system/link_graph.svg`, `wiki/index.md`, `wiki/graph_report.md`, `wiki/community_report.md`, `wiki/query_log.md`, and `wiki/log.md` together when the graph is rendered.
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
6. When reading Korean documents or markdown from the workspace, do not use PowerShell console output as the source of truth for filenames or body text if mojibake appears.
7. If a Korean filename or document body looks corrupted in terminal output, first enumerate the directory programmatically to recover the exact path, then read the file bytes or load the file with Python using explicit UTF-8 decoding.
8. Prefer a safe read workflow for Korean local files: discover the path with Python or a filesystem listing, read with explicit encoding, and only then summarize or transform the content.
9. Do not describe terminal mojibake as a content problem in the source file until the file bytes or an explicit UTF-8 read confirm it.
10. For Korean local files, avoid making decisions from `Get-Content` output alone when a Python byte-safe read is available.

## Query Workflow

1. Load `wiki/system/query_cache.json`.
2. For retrieval context, also inspect `wiki/system/community_summaries.json`, `wiki/system/semantic_meta.json`, and `wiki/system/obsidian_semantic_cache.json` before broad markdown reads.
3. Rank candidate pages using title, summary, headings, tags, topics, entities, path tokens, graph neighbors, semantic similarity, community summaries, and the Smart Connections bridge bonus from the Obsidian semantic cache.
4. Prefer the `ask` workflow so the graph-first route and token savings are logged.
5. For code-oriented questions, use the code-graph workflow first and read `wiki/system/code_graph.json` or `wiki/system/code_graph_meta.json` before opening many files.
6. Read only the top-ranked markdown pages that are needed to answer the question.
7. If the question is about evolving configuration or operational state, also check `memory-search` before reading many raw pages.
8. If a useful synthesis is created, store it back into `wiki/notes/`.
9. When a code-oriented question does not already name a specific node, use `graph-query` first to discover the relevant code graph ids before broader code reads.
10. When tracing local code relationships, use `graph-neighbors` before broader code reads when a single node's adjacency is enough.
11. When a single code node needs clarification, use `graph-explain` before opening the source file broadly so you can inspect its source location and immediate relations first.
12. When using `ask`, follow the returned `workflow.instruction` and prefer its `code_read_plan` or `read_plan` before ad hoc file opens.
13. For code-oriented `ask` results, treat `code_read_plan` as the primary read target and use the markdown `selected` or `read_plan` pages only for broader context when needed.
14. When `ask` or `route` returns `query_profile.mode` as `code-first`, treat `code_context` and `code_read_plan` as the authoritative code-first routing output before broader markdown reads.
15. For code-oriented `ask` results, inspect `code_relation` when present before falling back to broader graph traversal or ad hoc code reads.
16. When the question is about how two code nodes relate, use `graph-path` before broader code reads so you can inspect the shortest graph route first.
17. For lecture, transcript, or meeting-summary requests, read the full source span before writing, then weight the summary according to where the session spent its time instead of over-indexing the opening recap.
18. When a summary request references multiple related files, inspect all relevant files first and produce a balanced synthesis that reflects the whole session, including later practical sections, setup details, and conclusions.

## Maintenance Workflow

1. Run wiki build and memory commands from the dedicated knowledge environment at `.\.venv-knowledge\Scripts\python.exe`.
2. Rebuild indexes after adding or moving markdown files with `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph`.
3. Check for orphan pages and unresolved links.
4. Keep `wiki/log.md` append-only.
5. Keep `wiki/system/query_log.json` and `wiki/query_log.md` append-only; prefer `ask` over ad hoc routing when you want the token-savings trail preserved.
6. Rebuild the semantic FAISS index, code graph, and community summaries as part of every wiki build.
7. Keep Mem0 bootstraps resumable by using offsets and small batches when local Qdrant is in use.
8. Do not run multiple Mem0 commands in parallel against the local Qdrant store.
9. After code graph or routing changes, verify the `llm_wiki` package compiles and run a compact code-graph smoke test before trusting the outputs.
10. After changing links, ignore rules, memory config, or skill docs, rebuild the wiki, confirm unresolved links are `0` or intentionally excluded, run one `ask` query, run one `memory-search` query, and verify token savings were logged.
11. After material setup-state or operational changes that `memory-search` should answer, rerun the relevant `memory-bootstrap` batches before relying on Mem0 results.
12. Before running `memory-bootstrap` or relying on `memory-search` after local model or environment changes, run `memory-check` and confirm the expected Ollama models are available.

## CLI Commands

- Build the wiki: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph`
- Route a query without logging: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli route "<query>" --root . --limit 5`
- Run the graph-first query workflow: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli ask "<query>" --root . --limit 5`
- Check memory prerequisites: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-check --root .`
- Bootstrap memory in batches: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-bootstrap --root . --user-id dxax-wiki --mode communities --offset 0 --limit 10`
- Bootstrap page summaries into memory: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-bootstrap --root . --user-id dxax-wiki --mode pages --offset 0 --limit 10`
- Search change-aware facts: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-search "<query>" --root . --user-id dxax-wiki --top-k 5`
- Add a change-aware fact manually: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-add "<fact>" --root . --user-id dxax-wiki --source manual`
- Check unresolved wiki links:
  ```powershell
  @'
  import json, pathlib
  obj = json.loads(pathlib.Path("wiki/system/link_graph.json").read_text(encoding="utf-8"))
  print(len(obj.get("unresolved_links", [])))
  for item in obj.get("unresolved_links", []):
      print(item.get("source_path"), "=>", item.get("target"))
  '@ | python -
  ```
- Inspect the code graph: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-query "<query>" --root . --limit 10`
- Inspect node neighbors in the code graph: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-neighbors "<node>" --root . --limit 20`
- Explain a code node: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-explain "<node>" --root . --limit 12`
- Trace a code path: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-path "<source>" "<target>" --root . --max-depth 8`
- Verify the package still compiles: `.\.venv-knowledge\Scripts\python.exe -m compileall llm_wiki`
- Verify code-aware ask routing: `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli ask "relationship between build_code_graph and write_outputs" --root . --limit 5`
