from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from .code_analysis import analyze_code_graph
from .code_cache import load_cached_extraction, save_cached_extraction
from .code_extractors import extract_code_file
from .indexer import IGNORE_FILE_NAME, SKIP_DIR_NAMES, load_ignore_rules, matches_ignore


CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".ps1"}


def iter_code_files(root: Path) -> Iterable[Path]:
    ignore_rules = load_ignore_rules(root)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        relpath = path.relative_to(root).as_posix()
        if matches_ignore(relpath, ignore_rules):
            continue
        yield path


def _build_communities(nodes: List[Dict[str, object]], edges: List[Dict[str, object]]) -> Dict[str, List[str]]:
    try:
        import networkx as nx
    except Exception:
        nx = None  # type: ignore[assignment]

    node_ids = [str(node["id"]) for node in nodes]
    if not node_ids:
        return {}

    if not nx:
        return {"community-001": node_ids}

    graph = nx.Graph()
    graph.add_nodes_from(node_ids)
    for edge in edges:
        if edge["source"] in node_ids and edge["target"] in node_ids:
            graph.add_edge(edge["source"], edge["target"])
    if graph.number_of_edges() == 0:
        return {f"community-{idx:03d}": [node_id] for idx, node_id in enumerate(node_ids, start=1)}
    communities = nx.algorithms.community.greedy_modularity_communities(graph)
    return {f"community-{idx:03d}": sorted(list(group)) for idx, group in enumerate(communities, start=1)}


def build_code_graph(repo_root: Path, system_root: Path) -> Dict[str, object]:
    files = sorted(iter_code_files(repo_root))
    nodes: List[Dict[str, object]] = []
    edges: List[Dict[str, object]] = []
    language_counts: Counter[str] = Counter()
    cache_hits = 0
    extracted_files = 0

    for path in files:
        relpath = path.relative_to(repo_root).as_posix()
        cached = load_cached_extraction(path, repo_root, system_root)
        extraction = cached
        if extraction is None:
            extraction = extract_code_file(path, relpath)
            save_cached_extraction(path, repo_root, system_root, extraction)
            extracted_files += 1
        else:
            cache_hits += 1

        language = str(extraction.get("language", "unknown"))
        language_counts[language] += 1
        nodes.extend(extraction.get("nodes", []))  # type: ignore[arg-type]
        edges.extend(extraction.get("edges", []))  # type: ignore[arg-type]

    dedup_nodes: Dict[str, Dict[str, object]] = {}
    for node in nodes:
        dedup_nodes[str(node["id"])] = node
    valid_node_ids = set(dedup_nodes)
    dedup_edges = []
    seen_edges = set()
    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        if source not in valid_node_ids or target not in valid_node_ids:
            continue
        key = (source, target, str(edge.get("relation", "")), str(edge.get("source_location", "")))
        if key in seen_edges:
            continue
        seen_edges.add(key)
        dedup_edges.append(edge)

    communities = _build_communities(list(dedup_nodes.values()), dedup_edges)
    node_to_community = {
        node_id: community_id
        for community_id, member_ids in communities.items()
        for node_id in member_ids
    }
    for node in dedup_nodes.values():
        node["community_id"] = node_to_community.get(str(node["id"]))

    relation_counts = Counter(str(edge.get("relation", "related")) for edge in dedup_edges)
    confidence_counts = Counter(str(edge.get("confidence", "EXTRACTED")) for edge in dedup_edges)

    analysis = analyze_code_graph(
        {
            "nodes": list(dedup_nodes.values()),
            "edges": dedup_edges,
            "communities": communities,
        }
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(repo_root),
        "ignore_file": IGNORE_FILE_NAME,
        "stats": {
            "files_scanned": len(files),
            "files_extracted": extracted_files,
            "cache_hits": cache_hits,
            "node_count": len(dedup_nodes),
            "edge_count": len(dedup_edges),
            "community_count": len(communities),
        },
        "facets": {
            "languages": language_counts.most_common(),
            "relations": relation_counts.most_common(),
            "confidence": confidence_counts.most_common(),
        },
        "nodes": list(dedup_nodes.values()),
        "edges": dedup_edges,
        "communities": communities,
        "analysis": analysis,
    }
