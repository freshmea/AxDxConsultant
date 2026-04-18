from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple


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


def _interesting_node(node: Dict[str, object]) -> bool:
    kind = str(node.get("kind", ""))
    return kind in {"function", "class", "async_function", "module"}


def god_nodes(graph: Dict[str, object], top_n: int = 10) -> List[Dict[str, object]]:
    nodes = _node_map(graph)
    adjacency = _adjacency(graph)
    ranked = []
    for node_id, node in nodes.items():
        if not _interesting_node(node):
            continue
        degree = len(adjacency.get(node_id, []))
        ranked.append(
            {
                "id": node_id,
                "label": node.get("label", node_id),
                "kind": node.get("kind", "unknown"),
                "path": node.get("path", ""),
                "community_id": node.get("community_id"),
                "degree": degree,
            }
        )
    ranked.sort(key=lambda item: (-int(item["degree"]), str(item["path"]), str(item["label"])))
    return ranked[:top_n]


def surprising_connections(graph: Dict[str, object], top_n: int = 8) -> List[Dict[str, object]]:
    nodes = _node_map(graph)
    seen = []
    for edge in graph.get("edges", []):  # type: ignore[arg-type]
        relation = str(edge.get("relation", "related"))
        if relation == "defines":
            continue
        source = nodes.get(str(edge["source"]))
        target = nodes.get(str(edge["target"]))
        if not source or not target:
            continue
        if str(source.get("kind", "")) == "symbol_ref" or str(target.get("kind", "")) == "symbol_ref":
            continue
        if bool(source.get("external")) or bool(target.get("external")):
            continue
        source_path = str(source.get("path", ""))
        target_path = str(target.get("path", ""))
        if source_path == target_path:
            continue
        source_community = source.get("community_id")
        target_community = target.get("community_id")
        score = 0
        reasons = []
        if source_community != target_community:
            score += 2
            reasons.append("cross-community")
        if relation in {"calls", "inherits"}:
            score += 2
            reasons.append(relation)
        if source_path.split("/", 1)[0] != target_path.split("/", 1)[0]:
            score += 1
            reasons.append("cross-directory")
        confidence = str(edge.get("confidence", "EXTRACTED"))
        if confidence != "EXTRACTED":
            score += 1
            reasons.append(confidence.lower())
        if score <= 0:
            continue
        seen.append(
            {
                "source": source.get("label", edge["source"]),
                "source_path": source_path,
                "target": target.get("label", edge["target"]),
                "target_path": target_path,
                "relation": relation,
                "confidence": confidence,
                "source_location": edge.get("source_location", ""),
                "why": ", ".join(reasons),
                "_score": score,
            }
        )
    seen.sort(key=lambda item: (-int(item["_score"]), str(item["source_path"]), str(item["target_path"])))
    for item in seen:
        item.pop("_score", None)
    return seen[:top_n]


def suggested_questions(graph: Dict[str, object], top_n: int = 8) -> List[str]:
    gods = god_nodes(graph, top_n=max(top_n, 5))
    relation_counts = Counter(str(edge.get("relation", "related")) for edge in graph.get("edges", []))  # type: ignore[arg-type]
    questions: List[str] = []
    if gods:
        questions.append(f"Which modules and functions depend most on `{gods[0]['label']}`?")
    if len(gods) >= 2:
        questions.append(f"How is `{gods[0]['label']}` connected to `{gods[1]['label']}`?")
    if relation_counts.get("calls"):
        questions.append("Which cross-file call paths are most central in this codebase?")
    if relation_counts.get("imports"):
        questions.append("Which import relationships create the strongest coupling across modules?")
    if relation_counts.get("inherits"):
        questions.append("Where does inheritance appear, and what architectural role does it play?")
    communities = graph.get("communities", {})
    if isinstance(communities, dict) and len(communities) > 1:
        questions.append("Which communities interact the most, and are those boundaries intentional?")
    questions.append("Which nodes look like good entry points for onboarding into this repository?")
    questions.append("Which symbol references point to missing or external definitions that deserve review?")
    deduped = []
    seen = set()
    for question in questions:
        if question in seen:
            continue
        seen.add(question)
        deduped.append(question)
    return deduped[:top_n]


def analyze_code_graph(graph: Dict[str, object]) -> Dict[str, object]:
    return {
        "god_nodes": god_nodes(graph),
        "surprising_connections": surprising_connections(graph),
        "suggested_questions": suggested_questions(graph),
    }
