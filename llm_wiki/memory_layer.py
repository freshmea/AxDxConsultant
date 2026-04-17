from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List


MEMORY_ROOT = Path("memory_layer")
MEM0_CONFIG_FILE = "mem0_config.json"
MEM0_STATE_FILE = "memory_state.json"


def memory_paths(repo_root: Path) -> Dict[str, Path]:
    root = repo_root / MEMORY_ROOT
    return {
        "root": root,
        "config_path": root / MEM0_CONFIG_FILE,
        "state_path": root / MEM0_STATE_FILE,
        "qdrant_path": root / "qdrant",
        "history_path": root / "history.db",
    }


def default_mem0_config(repo_root: Path) -> Dict[str, object]:
    paths = memory_paths(repo_root)
    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "dxax_mem0",
                "path": str(paths["qdrant_path"]),
                "on_disk": True,
                "embedding_model_dims": 768,
            },
        },
        "llm": {
            "provider": "ollama",
            "config": {
                "model": "qwen2.5:1.5b",
                "ollama_base_url": "http://127.0.0.1:11434",
                "temperature": 0.0,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",
                "ollama_base_url": "http://127.0.0.1:11434",
            },
        },
        "history_db_path": str(paths["history_path"]),
        "version": "v1.1",
    }


def ensure_mem0_config(repo_root: Path) -> Path:
    paths = memory_paths(repo_root)
    paths["root"].mkdir(parents=True, exist_ok=True)
    if not paths["config_path"].exists():
        config = default_mem0_config(repo_root)
        paths["config_path"].write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return paths["config_path"]


def load_mem0(repo_root: Path):
    try:
        from mem0 import Memory
    except Exception as exc:
        raise RuntimeError(f"mem0 is not installed in the active environment: {exc}") from exc

    config_path = ensure_mem0_config(repo_root)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return Memory.from_config(config)


def check_ollama_models(base_url: str = "http://127.0.0.1:11434") -> Dict[str, object]:
    import requests

    response = requests.get(f"{base_url}/api/tags", timeout=15)
    response.raise_for_status()
    payload = response.json()
    models = [item.get("name") for item in payload.get("models", [])]
    return {"base_url": base_url, "models": models}


def memory_add(repo_root: Path, text: str, user_id: str, metadata: Dict[str, object] | None = None) -> Dict[str, object]:
    memory = load_mem0(repo_root)
    result = memory.add(
        [{"role": "user", "content": text}],
        user_id=user_id,
        metadata=metadata or {},
        infer=True,
    )
    return {"status": "ok", "result": result}


def memory_search(repo_root: Path, query: str, user_id: str, top_k: int = 5) -> Dict[str, object]:
    memory = load_mem0(repo_root)
    result = memory.search(query, top_k=top_k, filters={"user_id": user_id})
    return {"status": "ok", "result": result}


def bootstrap_memory(
    repo_root: Path,
    pages: Iterable[Dict[str, object]],
    user_id: str = "dxax-wiki",
    *,
    offset: int = 0,
    limit: int = 0,
) -> Dict[str, object]:
    memory = load_mem0(repo_root)
    items = list(pages)
    if offset > 0:
        items = items[offset:]
    if limit > 0:
        items = items[:limit]
    ingested = 0
    paths = memory_paths(repo_root)
    for index, page in enumerate(items, start=offset):
        text = (
            f"문서 제목: {page['title']}\n"
            f"경로: {page['path']}\n"
            f"요약: {page['summary']}\n"
            f"태그: {', '.join(page.get('tags', []))}\n"
            f"주제: {', '.join(page.get('topics', []))}\n"
            f"엔터티: {', '.join(page.get('entities', []))}"
        )
        metadata = {
            "source": "wiki-page",
            "path": page["path"],
            "page_id": page["id"],
        }
        memory.add([{"role": "user", "content": text}], user_id=user_id, metadata=metadata, infer=True)
        ingested += 1
        paths["state_path"].write_text(
            json.dumps(
                {
                    "status": "running",
                    "bootstrapped_pages": ingested,
                    "user_id": user_id,
                    "last_index": index,
                    "next_offset": index + 1,
                    "last_page_id": page["id"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    state = {
        "status": "completed",
        "bootstrapped_pages": ingested,
        "user_id": user_id,
        "start_offset": offset,
        "next_offset": offset + ingested,
        "last_page_id": items[-1]["id"] if items else None,
    }
    paths["state_path"].write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok", **state, "state_path": str(paths["state_path"])}
