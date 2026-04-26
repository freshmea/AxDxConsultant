from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable


CACHE_DIR_NAME = "code_cache"


def cache_dir(system_root: Path) -> Path:
    path = system_root / CACHE_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_hash(path: Path, root: Path) -> str:
    payload = path.read_bytes()
    digest = hashlib.sha256()
    digest.update(payload)
    digest.update(b"\x00")
    digest.update(path.resolve().relative_to(root.resolve()).as_posix().encode("utf-8", errors="ignore"))
    return digest.hexdigest()


def load_cached_extraction(path: Path, root: Path, system_root: Path) -> Dict[str, object] | None:
    digest = file_hash(path, root)
    cache_path = cache_dir(system_root) / f"{digest}.json"
    if not cache_path.exists():
        return None
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_cached_extraction(path: Path, root: Path, system_root: Path, extraction: Dict[str, object]) -> Path:
    digest = file_hash(path, root)
    cache_path = cache_dir(system_root) / f"{digest}.json"
    cache_path.write_text(json.dumps(extraction, ensure_ascii=False, indent=2), encoding="utf-8")
    return cache_path


def prune_stale_cache(system_root: Path, active_relpaths: Iterable[str]) -> int:
    active = set(active_relpaths)
    removed = 0
    for cache_path in cache_dir(system_root).glob("*.json"):
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cache_path.unlink(missing_ok=True)
            removed += 1
            continue
        relpath = payload.get("path")
        if not isinstance(relpath, str) or relpath not in active:
            cache_path.unlink(missing_ok=True)
            removed += 1
    return removed
