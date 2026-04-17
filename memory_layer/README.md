# Local Memory Layer

This folder holds the change-aware fact memory stack for this workspace.

## Stack

- `Mem0` for memory extraction and retrieval
- `Ollama` for local LLM and embedding inference
- local Qdrant storage through Mem0's `path` configuration

## Files

- `mem0_config.json`: local Mem0 configuration
- `memory_state.json`: bootstrap status
- `qdrant/`: local vector memory store
- `history.db`: Mem0 history database

## Commands

Check local models:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-check --root .
```

Bootstrap wiki summaries into memory:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-bootstrap --root . --user-id dxax-wiki
```

Add a manual fact:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-add "이번 주에는 Obsidian Smart Connections를 설치했다." --root .
```

Search memory:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-search "Smart Connections 설치 상태" --root .
```

## Intended Use

Keep evolving facts here:

- setup changes
- tool installation state
- conventions that changed over time
- short operational facts that are not best stored as permanent wiki pages

Keep canonical documents in the markdown wiki instead of overloading the memory layer.
