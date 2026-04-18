from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


DEFINITION_KINDS = {"function", "async_function", "class", "module"}


def load_code_graph(repo_root: Path) -> Dict[str, object]:
    graph_path = repo_root / "wiki" / "system" / "code_graph.json"
    return json.loads(graph_path.read_text(encoding="utf-8"))


def _node_map(graph: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    return {str(node["id"]): node for node in graph.get("nodes", [])}  # type: ignore[arg-type]


def _adjacency(graph: Dict[str, object]) -> Dict[str, List[Tuple[str, Dict[str, object]]]]:
    neighbors: Dict[str, List[Tuple[str, Dict[str, object]]]] = {}
    for edge in graph.get("edges", []):  # type: ignore[arg-type]
        source = str(edge["source"])
        target = str(edge["target"])
        neighbors.setdefault(source, []).append((target, edge))
        neighbors.setdefault(target, []).append((source, edge))
    return neighbors


def is_definition_kind(kind: str) -> bool:
    return kind in DEFINITION_KINDS


def _result_priority(item: Dict[str, object]) -> tuple[int, int, str, str]:
    kind = str(item.get("kind", ""))
    path = str(item.get("path", ""))
    definition_rank = 0 if is_definition_kind(kind) else 1
    internal_rank = 0 if path.startswith("llm_wiki/") else 1
    return (definition_rank, internal_rank, kind, str(item.get("label", "")))


def search_nodes(graph: Dict[str, object], query: str, limit: int = 10) -> List[Dict[str, object]]:
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return []
    results = []
    for node in graph.get("nodes", []):  # type: ignore[arg-type]
        label = str(node.get("label", ""))
        path = str(node.get("path", ""))
        kind = str(node.get("kind", ""))
        haystack = " ".join([label, path, kind]).lower()
        score = sum(1 for term in terms if term in haystack)
        if score <= 0:
            continue
        results.append(
            {
                "id": node["id"],
                "label": label,
                "kind": kind,
                "path": path,
                "community_id": node.get("community_id"),
                "score": score,
                "source_location": node.get("source_location"),
            }
        )
    results.sort(key=lambda item: (-int(item["score"]), *_result_priority(item)))
    return results[:limit]


def code_context_for_query(graph: Dict[str, object], query: str, limit: int = 8) -> Dict[str, object]:
    hits = search_nodes(graph, query, limit=max(limit * 2, 8))
    if not hits:
        return {"hits": [], "files": [], "estimated_tokens": 0}

    files: Dict[str, Dict[str, object]] = {}
    definition_hits = [hit for hit in hits if is_definition_kind(str(hit.get("kind", "")))]
    non_definition_hits = [hit for hit in hits if not is_definition_kind(str(hit.get("kind", "")))]
    selected_hits = (definition_hits + non_definition_hits)[:limit]
    for hit in selected_hits:
        path = str(hit.get("path", ""))
        if not path:
            continue
        bucket = files.setdefault(path, {"path": path, "hits": [], "max_score": 0, "definition_hits": 0})
        bucket["hits"].append(
            {
                "id": hit["id"],
                "label": hit["label"],
                "kind": hit["kind"],
                "score": hit["score"],
                "source_location": hit.get("source_location", ""),
            }
        )
        bucket["max_score"] = max(int(bucket["max_score"]), int(hit["score"]))
        if is_definition_kind(str(hit.get("kind", ""))):
            bucket["definition_hits"] = int(bucket["definition_hits"]) + 1
    file_list = sorted(
        files.values(),
        key=lambda item: (-int(item["definition_hits"]), -int(item["max_score"]), str(item["path"])),
    )
    estimated_tokens = 0
    for item in selected_hits:
        estimated_tokens += max(8, len(str(item.get("label", ""))) + len(str(item.get("path", ""))))
    return {
        "hits": selected_hits,
        "definition_hits": definition_hits[:limit],
        "files": file_list[:limit],
        "estimated_tokens": estimated_tokens,
    }


def infer_relationship_between(graph: Dict[str, object], source_ref: str, target_ref: str) -> Dict[str, object] | None:
    nodes = _node_map(graph)
    source_id = resolve_node_ref(graph, source_ref)
    target_id = resolve_node_ref(graph, target_ref)
    if not source_id or not target_id:
        return None

    source = nodes[source_id]
    target = nodes[target_id]
    source_label = str(source.get("label", ""))
    target_label = str(target.get("label", ""))
    source_path = str(source.get("path", ""))
    target_path = str(target.get("path", ""))

    def _find_symbol_ref(label: str, path: str) -> Dict[str, object] | None:
        matches = [
            node
            for node in graph.get("nodes", [])  # type: ignore[arg-type]
            if str(node.get("kind", "")) == "symbol_ref"
            and str(node.get("label", "")) == label
            and str(node.get("path", "")) == path
        ]
        if not matches:
            return None
        matches.sort(key=lambda item: str(item.get("source_location", "")))
        return matches[0]

    target_refers_to_source = _find_symbol_ref(source_label, target_path)
    if target_refers_to_source:
        return {
            "type": "file_reference",
            "summary": f"{target_label} references {source_label} in `{target_path}`.",
            "direction": f"{target_label} -> {source_label}",
            "source_path": source_path,
            "target_path": target_path,
            "evidence": {
                "label": source_label,
                "path": target_path,
                "source_location": target_refers_to_source.get("source_location", ""),
            },
        }

    source_refers_to_target = _find_symbol_ref(target_label, source_path)
    if source_refers_to_target:
        return {
            "type": "file_reference",
            "summary": f"{source_label} references {target_label} in `{source_path}`.",
            "direction": f"{source_label} -> {target_label}",
            "source_path": source_path,
            "target_path": target_path,
            "evidence": {
                "label": target_label,
                "path": source_path,
                "source_location": source_refers_to_target.get("source_location", ""),
            },
        }

    return None


def explain_node(graph: Dict[str, object], node_ref: str, neighbor_limit: int = 12) -> Dict[str, object]:
    nodes = _node_map(graph)
    adjacency = _adjacency(graph)
    target = resolve_node_ref(graph, node_ref)
    if not target:
        return {"error": f"Node not found: {node_ref}"}
    node = nodes[target]
    neighbors = []
    for neighbor_id, edge in adjacency.get(target, []):
        neighbor = nodes.get(neighbor_id, {"label": neighbor_id, "kind": "unknown", "path": ""})
        neighbors.append(
            {
                "id": neighbor_id,
                "label": neighbor.get("label", neighbor_id),
                "kind": neighbor.get("kind", "unknown"),
                "path": neighbor.get("path", ""),
                "relation": edge.get("relation", "related"),
                "confidence": edge.get("confidence", "EXTRACTED"),
                "source_location": edge.get("source_location", ""),
            }
        )
    neighbors.sort(key=lambda item: (str(item["relation"]), str(item["label"])))
    incoming = 0
    outgoing = 0
    for edge in graph.get("edges", []):  # type: ignore[arg-type]
        if str(edge["target"]) == target:
            incoming += 1
        if str(edge["source"]) == target:
            outgoing += 1
    return {
        "id": target,
        "label": node.get("label", target),
        "kind": node.get("kind", "unknown"),
        "path": node.get("path", ""),
        "community_id": node.get("community_id"),
        "source_location": node.get("source_location", ""),
        "incoming_edges": incoming,
        "outgoing_edges": outgoing,
        "neighbors": neighbors[:neighbor_limit],
    }


def neighbors_for_node(graph: Dict[str, object], node_ref: str, limit: int = 20) -> Dict[str, object]:
    explained = explain_node(graph, node_ref, neighbor_limit=limit)
    if "error" in explained:
        return explained
    return {
        "id": explained["id"],
        "label": explained["label"],
        "neighbors": explained["neighbors"],
    }


def resolve_node_ref(graph: Dict[str, object], node_ref: str) -> str | None:
    nodes = _node_map(graph)
    if node_ref in nodes:
        return node_ref
    query = node_ref.lower().strip()
    exact_candidates = []
    fuzzy_candidates = []
    for node_id, node in nodes.items():
        label = str(node.get("label", "")).lower()
        path = str(node.get("path", "")).lower()
        if query == label or query == path:
            exact_candidates.append(node_id)
            continue
        if query in label or query in path:
            fuzzy_candidates.append(node_id)

    def _priority(node_id: str) -> tuple[int, int, str]:
        node = nodes[node_id]
        kind = str(node.get("kind", ""))
        kind_rank = {
            "function": 0,
            "class": 0,
            "async_function": 0,
            "module": 1,
            "import": 2,
            "symbol_ref": 3,
        }.get(kind, 4)
        path = str(node.get("path", ""))
        path_rank = 0 if path.startswith("llm_wiki/") else 1
        return (kind_rank, path_rank, str(node.get("label", "")))

    if exact_candidates:
        exact_candidates.sort(key=_priority)
        return exact_candidates[0]
    if fuzzy_candidates:
        fuzzy_candidates.sort(key=_priority)
        return fuzzy_candidates[0]
    return None


def shortest_path_between(graph: Dict[str, object], source_ref: str, target_ref: str, max_depth: int = 8) -> Dict[str, object]:
    source_id = resolve_node_ref(graph, source_ref)
    target_id = resolve_node_ref(graph, target_ref)
    if not source_id:
        return {"error": f"Source node not found: {source_ref}"}
    if not target_id:
        return {"error": f"Target node not found: {target_ref}"}
    if source_id == target_id:
        return {"source": source_id, "target": target_id, "path": [source_id], "hops": []}

    nodes = _node_map(graph)
    adjacency = _adjacency(graph)
    queue: List[str] = [source_id]
    parents: Dict[str, Tuple[str, Dict[str, object]]] = {}
    visited = {source_id}
    depth = {source_id: 0}
    target_label = str(nodes[target_id].get("label", "")).lower()

    def _neighbor_priority(neighbor_id: str) -> tuple[int, int, int, str]:
        neighbor = nodes.get(neighbor_id, {})
        label = str(neighbor.get("label", "")).lower()
        kind = str(neighbor.get("kind", ""))
        path = str(neighbor.get("path", ""))
        direct_match_rank = 0 if neighbor_id == target_id or label == target_label else 1
        definition_rank = 0 if is_definition_kind(kind) else 1
        internal_rank = 0 if path.startswith("llm_wiki/") else 1
        return (direct_match_rank, definition_rank, internal_rank, label)

    while queue:
        current = queue.pop(0)
        if depth[current] >= max_depth:
            continue
        neighbors = sorted(adjacency.get(current, []), key=lambda item: _neighbor_priority(item[0]))
        for neighbor_id, edge in neighbors:
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            parents[neighbor_id] = (current, edge)
            depth[neighbor_id] = depth[current] + 1
            if neighbor_id == target_id:
                queue.clear()
                break
            queue.append(neighbor_id)

    if target_id not in parents:
        return {
            "error": f"No path found within depth {max_depth}",
            "source": source_id,
            "target": target_id,
        }

    path_nodes = [target_id]
    hops = []
    current = target_id
    while current != source_id:
        parent_id, edge = parents[current]
        hops.append(
            {
                "from": parent_id,
                "from_label": nodes[parent_id].get("label", parent_id),
                "to": current,
                "to_label": nodes[current].get("label", current),
                "relation": edge.get("relation", "related"),
                "confidence": edge.get("confidence", "EXTRACTED"),
                "source_location": edge.get("source_location", ""),
            }
        )
        path_nodes.append(parent_id)
        current = parent_id
    path_nodes.reverse()
    hops.reverse()
    return {
        "source": source_id,
        "target": target_id,
        "path": path_nodes,
        "path_labels": [nodes[node_id].get("label", node_id) for node_id in path_nodes],
        "hops": hops,
    }
