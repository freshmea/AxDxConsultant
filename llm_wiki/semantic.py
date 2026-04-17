from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SEMANTIC_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SEMANTIC_INDEX_FILE = "semantic_index.faiss"
SEMANTIC_META_FILE = "semantic_meta.json"


def semantic_artifact_paths(system_root: Path) -> Dict[str, Path]:
    return {
        "index_path": system_root / SEMANTIC_INDEX_FILE,
        "meta_path": system_root / SEMANTIC_META_FILE,
    }


def semantic_text_from_page(page: Dict[str, object]) -> str:
    parts = [
        str(page.get("title", "")),
        str(page.get("summary", "")),
        " ".join(page.get("headings", [])[:8]),  # type: ignore[arg-type]
        " ".join(page.get("tags", [])),  # type: ignore[arg-type]
        " ".join(page.get("topics", [])),  # type: ignore[arg-type]
        " ".join(page.get("entities", [])),  # type: ignore[arg-type]
        str(page.get("path", "")),
    ]
    return "\n".join(part for part in parts if part.strip())


def build_semantic_index(system_root: Path, pages: List[Dict[str, object]], model_name: str = SEMANTIC_MODEL_NAME) -> Dict[str, object]:
    try:
        import faiss  # type: ignore[import-not-found]
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        return {"enabled": False, "reason": f"semantic dependencies unavailable: {exc}"}

    if not pages:
        return {"enabled": False, "reason": "no pages to embed"}

    artifacts = semantic_artifact_paths(system_root)
    model = SentenceTransformer(model_name)
    texts = [semantic_text_from_page(page) for page in pages]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    vectors = np.asarray(embeddings, dtype="float32")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(artifacts["index_path"]))

    meta = {
        "enabled": True,
        "model_name": model_name,
        "dimension": int(vectors.shape[1]),
        "pages": [
            {
                "id": page["id"],
                "title": page["title"],
                "path": page["path"],
                "summary": page["summary"],
                "tags": page.get("tags", []),
                "topics": page.get("topics", []),
                "entities": page.get("entities", []),
            }
            for page in pages
        ],
    }
    artifacts["meta_path"].write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    meta["index_path"] = str(artifacts["index_path"])
    meta["meta_path"] = str(artifacts["meta_path"])
    return meta


def load_semantic_index(system_root: Path) -> Tuple[object, Dict[str, object]] | Tuple[None, None]:
    try:
        import faiss  # type: ignore[import-not-found]
    except Exception:
        return None, None

    artifacts = semantic_artifact_paths(system_root)
    if not artifacts["index_path"].exists() or not artifacts["meta_path"].exists():
        return None, None

    index = faiss.read_index(str(artifacts["index_path"]))
    meta = json.loads(artifacts["meta_path"].read_text(encoding="utf-8"))
    return index, meta


def search_semantic(system_root: Path, query: str, limit: int = 8) -> List[Dict[str, object]]:
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception:
        return []

    loaded = load_semantic_index(system_root)
    if loaded == (None, None):
        return []
    index, meta = loaded  # type: ignore[assignment]
    if not index or not meta:
        return []

    model = SentenceTransformer(str(meta.get("model_name", SEMANTIC_MODEL_NAME)))
    query_vector = model.encode([query], normalize_embeddings=True, show_progress_bar=False)
    distances, indices = index.search(np.asarray(query_vector, dtype="float32"), limit)

    pages = meta.get("pages", [])
    results: List[Dict[str, object]] = []
    for score, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(pages):
            continue
        page = pages[idx]
        results.append(
            {
                "id": page["id"],
                "path": page["path"],
                "title": page["title"],
                "summary": page.get("summary", ""),
                "semantic_score": round(float(score), 6),
            }
        )
    return results
