---
name: graphify-code-wiki
description: "Apply, extend, or verify the Graphify-style code graph layer in this dxAx repository. Use when Codex needs to build or maintain code graph artifacts, code query commands, code-aware ask routing, or verification flows for `llm_wiki`."
---

# Graphify Code Wiki

Use this skill when the task is about the Graphify-inspired code graph integration in this repository, not for generic wiki maintenance.

## Integration stance

Keep the current system and absorb only the strongest Graphify ideas into it.

In this repository that means:

- do not replace the existing markdown wiki flow
- do not replace FAISS semantic retrieval
- do not replace the Mem0 change-aware fact layer
- add code-structure extraction, code graph querying, confidence labeling, and incremental cache behavior on top

Treat this as absorb-and-integrate, not replace-and-migrate.

## 1. Confirm the required files

Expect these files before modifying behavior:

- `llm_wiki/code_cache.py`
- `llm_wiki/code_extractors.py`
- `llm_wiki/code_graph.py`
- `llm_wiki/code_analysis.py`
- `llm_wiki/code_query.py`
- `llm_wiki/indexer.py`
- `llm_wiki/cli.py`
- `wiki/system/code_graph.json`
- `wiki/system/code_graph_meta.json`

If the Python modules exist but the generated JSON files do not, rebuild before making judgments.

## 2. Use the repository Python environment

Run everything with the dedicated environment:

```powershell
.\.venv-knowledge\Scripts\python.exe -V
```

Do not mix this workflow with another venv.

## 3. Understand the current architecture

The current repository pattern is:

- markdown wiki graph remains the primary corpus index
- existing retrieval remains `wiki + FAISS + Mem0`
- code graph is a parallel structure layer generated into `wiki/system/code_graph.json`
- `build` regenerates both markdown and code artifacts
- `graph-query`, `graph-neighbors`, `graph-explain`, and `graph-path` operate on the code graph
- `route` and `ask` can include `code_context`, `code_read_plan`, and `code_relation`

Current extractor scope is Python-first. Do not claim JS/TS/PowerShell extraction is complete unless you verify it in code and by running the commands.
Do not claim `tree-sitter` is active unless you verify that the extractor code actually uses it.

## 4. Rebuild artifacts after any code graph change

Run:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root .
```

Healthy output means these files are updated together:

- `wiki/system/page_index.json`
- `wiki/system/link_graph.json`
- `wiki/system/query_cache.json`
- `wiki/system/structure_index.json`
- `wiki/system/community_graph.json`
- `wiki/system/community_summaries.json`
- `wiki/system/semantic_index.faiss`
- `wiki/system/semantic_meta.json`
- `wiki/system/code_graph.json`
- `wiki/system/code_graph_meta.json`
- `wiki/index.md`
- `wiki/graph_report.md`
- `wiki/community_report.md`
- `wiki/log.md`

Respect `AGENTS.md`: do not edit raw markdown sources during indexing and keep `wiki/log.md` append-only.

## 5. Verify the core graph commands

Run a compact verification set after changes:

```powershell
.\.venv-knowledge\Scripts\python.exe -m compileall llm_wiki
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-query "write_outputs build_code_graph" --root . --limit 5
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-neighbors "build_code_graph" --root . --limit 5
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-explain "write_outputs" --root . --limit 6
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli graph-path "build_code_graph" "write_outputs" --root . --max-depth 6
```

Treat the feature as healthy only if:

1. `compileall` passes
2. `graph-query` returns definition nodes for the target symbols
3. `graph-explain` resolves the real function, not only a weak reference
4. `graph-path` returns a meaningful relationship or a clearly explained fallback

## 6. Verify code-aware routing

Use `ask` for the end-to-end check:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli ask "relationship between build_code_graph and write_outputs" --root . --limit 5
```

For code-oriented questions, expect:

- `query_profile.mode` = `code-first`
- `code_context` populated with matching symbols
- `code_read_plan` populated with relevant source files
- `workflow.instruction` telling the agent to read `code_read_plan` first
- `code_relation` present when a structural relationship can be inferred

Do not rely on `selected` markdown pages alone for code questions. In this repository, `code_read_plan` is the authoritative code-first read target.

## 7. Prefer structural evidence over loose graph shortest paths

When explaining relationships between two functions:

1. prefer direct symbol references in the target file
2. prefer function/class/module definitions over `symbol_ref`
3. use shortest-path traversal only as a fallback

If the relationship is inferred from a symbol reference, include the file path and source location.

## 8. Keep changes scoped

If extending this system:

- use `apply_patch` for edits
- avoid changing raw markdown sources
- update generated wiki outputs by rerunning `build`
- append a concise entry to `wiki/log.md` when the work materially changes the system
- keep the answer explicit about what was verified versus what is only implemented

## 9. Known limits

Account for these limits unless you remove them in code and verify them:

- code extraction is still Python-first and currently uses Python `ast`, not verified `tree-sitter`
- code graph communities use lightweight NetworkX community logic, not full Graphify Leiden clustering
- `ask` still returns markdown `selected/read_plan` because the wiki remains document-first overall
- the decisive code result for code questions is `code_read_plan` plus `code_relation`
- confidence labels and incremental cache exist in the current code graph layer, but they are narrower than full Graphify semantics

For adjacent wiki-wide setup or repair work, also read `../wiki-llm-setup/SKILL.md`.
