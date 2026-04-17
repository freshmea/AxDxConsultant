from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SMART_ENV_ROOT = Path(".smart-env")
SMART_ENV_SETTINGS = "smart_env.json"
SMART_ENV_MODELS = Path("embedding_models") / "embedding_models.ajson"
SMART_ENV_MULTI = Path("multi")
OBSIDIAN_CACHE_FILE = "obsidian_semantic_cache.json"


def obsidian_cache_path(system_root: Path) -> Path:
    return system_root / OBSIDIAN_CACHE_FILE


def _load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_ajson(path: Path) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return {}
    if text.startswith("{"):
        return json.loads(text)
    wrapped = "{\n" + text.rstrip(",\n\r ") + "\n}"
    return json.loads(wrapped)


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = 0.0
    mag_a = 0.0
    mag_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        mag_a += a * a
        mag_b += b * b
    if mag_a <= 0.0 or mag_b <= 0.0:
        return 0.0
    return dot / ((mag_a ** 0.5) * (mag_b ** 0.5))


def _active_model(repo_root: Path) -> Dict[str, object]:
    settings_path = repo_root / SMART_ENV_ROOT / SMART_ENV_SETTINGS
    models_path = repo_root / SMART_ENV_ROOT / SMART_ENV_MODELS
    if not settings_path.exists() or not models_path.exists():
        return {}
    settings = _load_json(settings_path)
    models = _load_ajson(models_path)
    default_key = (
        settings.get("embedding_models", {}) if isinstance(settings.get("embedding_models"), dict) else {}
    ).get("default_model_key")
    if not default_key:
        return {}
    model_record = models.get(f"embedding_models:{default_key}", {})
    if not isinstance(model_record, dict):
        return {}
    return {
        "default_model_key": default_key,
        "provider_key": model_record.get("provider_key"),
        "model_key": model_record.get("model_key"),
        "dims": model_record.get("dims"),
    }


def _iter_source_records(repo_root: Path) -> Iterable[Tuple[str, Dict[str, object]]]:
    multi_root = repo_root / SMART_ENV_ROOT / SMART_ENV_MULTI
    if not multi_root.exists():
        return []
    for path in multi_root.glob("*.ajson"):
        try:
            payload = _load_ajson(path)
        except Exception:
            continue
        for key, value in payload.items():
            if not key.startswith("smart_sources:") or not isinstance(value, dict):
                continue
            yield key, value


def build_obsidian_semantic_cache(repo_root: Path, pages: Iterable[object], top_k: int = 12) -> Dict[str, object]:
    page_map = {page.relpath: page for page in pages}
    model = _active_model(repo_root)
    model_name = str(model.get("model_key", "")).strip()
    source_vectors: List[Dict[str, object]] = []

    for _, record in _iter_source_records(repo_root):
        relpath = str(record.get("path", "")).replace("\\", "/")
        if relpath not in page_map:
            continue
        embeddings = record.get("embeddings", {})
        if not isinstance(embeddings, dict) or not embeddings:
            continue

        active_embedding = embeddings.get(model_name) if model_name else None
        if not isinstance(active_embedding, dict):
            active_embedding = next((item for item in embeddings.values() if isinstance(item, dict) and item.get("vec")), None)
        if not isinstance(active_embedding, dict):
            continue

        vector = active_embedding.get("vec", [])
        if not isinstance(vector, list) or not vector:
            continue

        page = page_map[relpath]
        source_vectors.append(
            {
                "id": page.page_id,
                "path": page.relpath,
                "title": page.title,
                "vec": vector,
                "last_embed_at": (record.get("last_embed", {}) if isinstance(record.get("last_embed"), dict) else {}).get("at"),
            }
        )

    if not source_vectors:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "enabled": False,
            "reason": "smart connections source embeddings not found",
            "model": model,
            "pages": {},
            "stats": {"embedded_pages": 0, "related_edges": 0},
        }

    related_edges = 0
    pages_payload: Dict[str, Dict[str, object]] = {}
    for source in source_vectors:
        scored: List[Dict[str, object]] = []
        for candidate in source_vectors:
            if candidate["id"] == source["id"]:
                continue
            score = _cosine_similarity(source["vec"], candidate["vec"])
            if score <= 0:
                continue
            scored.append(
                {
                    "id": candidate["id"],
                    "path": candidate["path"],
                    "title": candidate["title"],
                    "score": round(score, 6),
                }
            )
        scored.sort(key=lambda item: (-float(item["score"]), str(item["path"])))
        related = scored[:top_k]
        related_edges += len(related)
        pages_payload[str(source["id"])] = {
            "path": source["path"],
            "title": source["title"],
            "last_embed_at": source["last_embed_at"],
            "related": related,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "source": "obsidian-smart-connections",
        "smart_env_root": str((repo_root / SMART_ENV_ROOT).resolve()),
        "model": model,
        "pages": pages_payload,
        "stats": {
            "embedded_pages": len(source_vectors),
            "related_edges": related_edges,
        },
    }
