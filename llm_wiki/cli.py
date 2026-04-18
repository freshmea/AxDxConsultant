from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .indexer import build_index, tokenize, write_outputs
from .code_query import (
    code_context_for_query,
    explain_node,
    infer_relationship_between,
    load_code_graph,
    neighbors_for_node,
    search_nodes,
    shortest_path_between,
)
from .memory_layer import bootstrap_memory, check_ollama_models, memory_add, memory_search
from .semantic import search_semantic


CODE_QUERY_MARKERS = {
    "function",
    "class",
    "module",
    "import",
    "call",
    "caller",
    "callee",
    "path",
    "code",
    "graph",
    "api",
    "함수",
    "클래스",
    "모듈",
    "코드",
    "호출",
    "관계",
    "연결",
    "경로",
    "역할",
}
TECHNICAL_PAGE_PREFIXES = ("llm_wiki/", "memory_layer/", "skills/")


def _definition_hits(code_context: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        hit
        for hit in code_context.get("hits", [])  # type: ignore[union-attr]
        if str(hit.get("kind", "")) in {"function", "async_function", "class", "module"}
    ]


def classify_query(query: str, code_context: Dict[str, object]) -> Dict[str, object]:
    lowered = query.lower()
    reasons: List[str] = []
    score = 0
    definition_hits = _definition_hits(code_context)

    if definition_hits:
        score += 2
        reasons.append("matched code definitions")
    if len(definition_hits) >= 2:
        score += 1
        reasons.append("matched multiple code definitions")
    if any(marker in lowered for marker in CODE_QUERY_MARKERS):
        score += 1
        reasons.append("contains code-oriented markers")
    if any(marker in query for marker in ("_", ".py", "::", "/")):
        score += 1
        reasons.append("contains code-like identifiers")

    return {
        "mode": "code-first" if score >= 2 else "document-first",
        "is_code_query": score >= 2,
        "score": score,
        "reasons": reasons,
    }


def is_technical_page(page_path: str) -> bool:
    if page_path == "AGENTS.md":
        return True
    return any(page_path.startswith(prefix) for prefix in TECHNICAL_PAGE_PREFIXES)


def emit_json(payload: Dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.buffer.write(data.encode("utf-8"))


def load_json(path: Path) -> Dict[str, object] | List[object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_query_cache(repo_root: Path) -> Dict[str, object]:
    cache_path = repo_root / "wiki" / "system" / "query_cache.json"
    return load_json(cache_path)  # type: ignore[return-value]


def score_pages(repo_root: Path, cache: Dict[str, object], query: str, limit: int) -> Dict[str, object]:
    query_tokens = tokenize(query)
    pages: Dict[str, Dict[str, object]] = cache["pages"]  # type: ignore[assignment]
    communities: Dict[str, Dict[str, object]] = cache.get("communities", {})  # type: ignore[assignment]
    scores: List[Dict[str, object]] = []
    total_tokens = sum(int(page["tokens_estimate"]) for page in pages.values())
    code_graph: Dict[str, object] | None = None
    try:
        code_graph = load_code_graph(repo_root)
        code_context = code_context_for_query(code_graph, query, limit=max(limit, 5))
    except Exception:
        code_context = {"hits": [], "files": [], "estimated_tokens": 0}
    query_profile = classify_query(query, code_context)
    semantic_limit = max(limit, 5) if query_profile["is_code_query"] else max(limit * 2, 8)
    semantic_hits = {
        item["id"]: item for item in search_semantic(repo_root / "wiki" / "system", query, limit=semantic_limit)
    }
    community_scores: Dict[str, int] = {}
    provisional: List[Dict[str, object]] = []
    code_path_bonus: Dict[str, float] = {}

    for hit in code_context.get("hits", []):  # type: ignore[union-attr]
        hit_path = str(hit.get("path", ""))
        if not hit_path:
            continue
        top_dir = hit_path.split("/", 1)[0]
        code_path_bonus[top_dir] = max(code_path_bonus.get(top_dir, 0.0), float(hit.get("score", 0)) * 0.5)
        code_path_bonus[hit_path] = max(code_path_bonus.get(hit_path, 0.0), float(hit.get("score", 0)) * 0.75)

    for community_id, community in communities.items():
        community_text = " ".join(
            [
                str(community.get("summary", "")),
                " ".join(topic for topic, _ in community.get("top_topics", [])),
                " ".join(entity for entity, _ in community.get("top_entities", [])),
                " ".join(tag for tag, _ in community.get("top_tags", [])),
            ]
        )
        community_terms = Counter(tokenize(community_text))
        community_score = sum(community_terms[token] for token in query_tokens)
        if community_score > 0:
            community_scores[community_id] = community_score

    for page_id, page in pages.items():
        terms = Counter(page["terms"])  # type: ignore[arg-type]
        direct = sum(terms[token] for token in query_tokens)
        title_hits = sum(4 for token in query_tokens if token in tokenize(str(page["title"])))
        heading_hits = sum(2 for token in query_tokens if token in tokenize(" ".join(page["headings"])))
        tag_hits = sum(3 for token in query_tokens if token in tokenize(" ".join(page["tags"])))
        topic_hits = sum(2 for token in query_tokens if token in tokenize(" ".join(page["topics"])))
        entity_hits = sum(2 for token in query_tokens if token in tokenize(" ".join(page["entities"])))
        semantic_hit = semantic_hits.get(page_id)
        semantic_bonus = round(float(semantic_hit["semantic_score"]) * 12, 4) if semantic_hit else 0.0
        community_bonus = sum(community_scores.get(community_id, 0) for community_id in page.get("community_ids", []))
        page_path = str(page.get("path", ""))
        path_bonus = code_path_bonus.get(page_path, 0.0) + code_path_bonus.get(page_path.split("/", 1)[0], 0.0)
        semantic_score = direct + title_hits + heading_hits + tag_hits + topic_hits + entity_hits
        if query_profile["is_code_query"]:
            technical_page = is_technical_page(page_path)
            if not technical_page:
                continue
            path_bonus += 3.0
            semantic_bonus = round(semantic_bonus * 0.35, 4)
        total_score = semantic_score + semantic_bonus + community_bonus + path_bonus
        if total_score <= 0:
            continue
        inbound_bonus = min(int(page["inbound_count"]), 5)
        score = total_score + inbound_bonus
        provisional.append(
            {
                "id": page_id,
                "title": page["title"],
                "path": page["path"],
                "summary": page["summary"],
                "score": score,
                "tokens_estimate": page["tokens_estimate"],
                "neighbors": page["neighbors"],
                "tags": page["tags"],
                "topics": page["topics"],
                "entities": page["entities"],
                "community_ids": page.get("community_ids", []),
                "score_breakdown": {
                    "lexical": semantic_score,
                    "semantic": semantic_bonus,
                    "community": community_bonus,
                    "code": path_bonus,
                    "obsidian": 0.0,
                    "inbound": inbound_bonus,
                },
            }
        )

    provisional.sort(key=lambda item: (-float(item["score"]), str(item["path"])))
    seed_ids = [item["id"] for item in provisional[: max(limit, 5)]]
    obsidian_bonus_map: Dict[str, float] = {}
    for seed_id in seed_ids:
        seed_page = pages.get(seed_id, {})
        for relation in seed_page.get("obsidian_related", []):
            if not isinstance(relation, dict):
                continue
            related_id = relation.get("id")
            related_score = relation.get("score", 0.0)
            if not related_id or related_id == seed_id:
                continue
            try:
                scale = 0.5 if query_profile["is_code_query"] else 4.0
                bonus = round(float(related_score) * scale, 4)
            except (TypeError, ValueError):
                continue
            if bonus <= 0:
                continue
            related_path = str(pages.get(str(related_id), {}).get("path", ""))
            if query_profile["is_code_query"] and not is_technical_page(related_path):
                continue
            obsidian_bonus_map[str(related_id)] = obsidian_bonus_map.get(str(related_id), 0.0) + bonus

    for item in provisional:
        obsidian_bonus = obsidian_bonus_map.get(str(item["id"]), 0.0)
        item["score"] = round(float(item["score"]) + obsidian_bonus, 4)
        item["score_breakdown"]["obsidian"] = obsidian_bonus  # type: ignore[index]
        scores.append(item)

    scores.sort(key=lambda item: (-float(item["score"]), str(item["path"])))
    selected = scores[:limit]

    expanded_ids = []
    seen = set()
    for item in selected:
        for candidate in [item["id"], *list(item["neighbors"])[:3]]:
            if candidate in pages and candidate not in seen:
                expanded_ids.append(candidate)
                seen.add(candidate)

    routed_pages = [
        {
            "id": page_id,
            "title": pages[page_id]["title"],
            "path": pages[page_id]["path"],
            "summary": pages[page_id]["summary"],
            "tags": pages[page_id]["tags"],
            "topics": pages[page_id]["topics"],
            "entities": pages[page_id]["entities"],
                "community_ids": pages[page_id].get("community_ids", []),
                "obsidian_related": pages[page_id].get("obsidian_related", [])[:5],
                "tokens_estimate": pages[page_id]["tokens_estimate"],
            }
        for page_id in expanded_ids
    ]
    routed_tokens = sum(int(page["tokens_estimate"]) for page in routed_pages)
    code_read_plan = list(code_context.get("files", []))[: max(limit, 5)]  # type: ignore[arg-type]
    code_relation = None
    definition_hits = _definition_hits(code_context)
    if code_graph and len(definition_hits) >= 2:
        code_relation = infer_relationship_between(
            code_graph,
            str(definition_hits[0]["id"]),
            str(definition_hits[1]["id"]),
        )
        if not code_relation:
            code_relation = shortest_path_between(
                code_graph,
                str(definition_hits[0]["id"]),
                str(definition_hits[1]["id"]),
                max_depth=6,
            )

    return {
        "query": query,
        "query_profile": query_profile,
        "selected": selected,
        "read_plan": routed_pages,
        "code_read_plan": code_read_plan,
        "code_relation": code_relation,
        "token_budget": {
            "full_corpus_estimate": total_tokens,
            "targeted_read_estimate": routed_tokens,
            "code_context_estimate": int(code_context.get("estimated_tokens", 0)),
            "saved_estimate": max(total_tokens - routed_tokens, 0),
            "savings_ratio": round(max(total_tokens - routed_tokens, 0) / total_tokens, 4) if total_tokens else 0,
        },
        "semantic_hits": [
            hit
            for hit in list(semantic_hits.values())
            if not query_profile["is_code_query"] or is_technical_page(str(hit.get("path", "")))
        ][:semantic_limit],
        "code_context": code_context,
    }


def append_query_log(repo_root: Path, result: Dict[str, object]) -> Dict[str, Path]:
    system_root = repo_root / "wiki" / "system"
    wiki_root = repo_root / "wiki"
    json_path = system_root / "query_log.json"
    md_path = wiki_root / "query_log.md"

    logs = load_json(json_path) if json_path.exists() else []
    if not isinstance(logs, list):
        logs = []
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "query": result["query"],
        "selected_paths": [item["path"] for item in result["selected"]],  # type: ignore[index]
        "read_plan_paths": [item["path"] for item in result["read_plan"]],  # type: ignore[index]
        "token_budget": result["token_budget"],
    }
    logs.append(entry)
    json_path.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"## {timestamp}",
        f"- Query: {result['query']}",
        f"- Selected: {', '.join(item['path'] for item in result['selected']) or '(none)'}",  # type: ignore[index]
        f"- Read plan: {', '.join(item['path'] for item in result['read_plan']) or '(none)'}",  # type: ignore[index]
        (
            f"- Tokens: full={result['token_budget']['full_corpus_estimate']} "  # type: ignore[index]
            f"targeted={result['token_budget']['targeted_read_estimate']} "  # type: ignore[index]
            f"saved={result['token_budget']['saved_estimate']} "  # type: ignore[index]
            f"ratio={result['token_budget']['savings_ratio']}"  # type: ignore[index]
        ),
        "",
    ]
    if md_path.exists():
        previous = md_path.read_text(encoding="utf-8", errors="ignore").rstrip()
        md_path.write_text(f"{previous}\n\n" + "\n".join(md_lines), encoding="utf-8")
    else:
        md_path.write_text("# Query Log\n\n" + "\n".join(md_lines), encoding="utf-8")

    return {"query_log_json_path": json_path, "query_log_md_path": md_path}


def render_graph(cache_path: Path) -> Path:
    from graphviz import Digraph

    graphviz_bin = Path("C:/Program Files/Graphviz/bin")
    if graphviz_bin.exists() and not shutil.which("dot"):
        os.environ["PATH"] = f"{graphviz_bin}{os.pathsep}{os.environ.get('PATH', '')}"

    data = load_json(cache_path)
    output_path = cache_path.with_name("link_graph")
    dot = Digraph("llm_wiki", format="svg")
    dot.attr(rankdir="LR", bgcolor="white")

    for node in data["nodes"]:  # type: ignore[index]
        topic_line = ", ".join(node.get("topics", [])[:3])  # type: ignore[union-attr]
        label = f"{node['title']}\\n{node['path']}\\n{topic_line}"  # type: ignore[index]
        dot.node(node["id"], label=label, shape="box", style="rounded")  # type: ignore[index]
    for edge in data["edges"]:  # type: ignore[index]
        dot.edge(edge["source"], edge["target"])  # type: ignore[index]

    svg_path = output_path.with_suffix(".svg")
    dot.render(outfile=str(svg_path), cleanup=True)
    return svg_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Local LLM wiki indexer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Scan markdown files and build wiki metadata")
    build_parser.add_argument("--root", default=".", help="Repository root")
    build_parser.add_argument("--render-graph", action="store_true", help="Render SVG graph with graphviz")

    route_parser = subparsers.add_parser("route", help="Select a small set of pages for a query")
    route_parser.add_argument("query", help="Natural-language question")
    route_parser.add_argument("--root", default=".", help="Repository root")
    route_parser.add_argument("--limit", type=int, default=5, help="Primary result count")

    ask_parser = subparsers.add_parser("ask", help="Graph-first query routing with token savings log")
    ask_parser.add_argument("query", help="Natural-language question")
    ask_parser.add_argument("--root", default=".", help="Repository root")
    ask_parser.add_argument("--limit", type=int, default=5, help="Primary result count")

    graph_query_parser = subparsers.add_parser("graph-query", help="Search nodes in the code graph")
    graph_query_parser.add_argument("query", help="Node search query")
    graph_query_parser.add_argument("--root", default=".", help="Repository root")
    graph_query_parser.add_argument("--limit", type=int, default=10, help="Result count")

    graph_neighbors_parser = subparsers.add_parser("graph-neighbors", help="Show neighbors for a code graph node")
    graph_neighbors_parser.add_argument("node", help="Node id, label, or path fragment")
    graph_neighbors_parser.add_argument("--root", default=".", help="Repository root")
    graph_neighbors_parser.add_argument("--limit", type=int, default=20, help="Neighbor count")

    graph_explain_parser = subparsers.add_parser("graph-explain", help="Explain a code graph node")
    graph_explain_parser.add_argument("node", help="Node id, label, or path fragment")
    graph_explain_parser.add_argument("--root", default=".", help="Repository root")
    graph_explain_parser.add_argument("--limit", type=int, default=12, help="Neighbor count")

    graph_path_parser = subparsers.add_parser("graph-path", help="Find a path between two code graph nodes")
    graph_path_parser.add_argument("source", help="Source node id, label, or path fragment")
    graph_path_parser.add_argument("target", help="Target node id, label, or path fragment")
    graph_path_parser.add_argument("--root", default=".", help="Repository root")
    graph_path_parser.add_argument("--max-depth", type=int, default=8, help="Maximum BFS depth")

    memory_bootstrap_parser = subparsers.add_parser("memory-bootstrap", help="Push wiki summaries into Mem0")
    memory_bootstrap_parser.add_argument("--root", default=".", help="Repository root")
    memory_bootstrap_parser.add_argument("--user-id", default="dxax-wiki", help="Mem0 user id namespace")
    memory_bootstrap_parser.add_argument("--mode", choices=["pages", "communities"], default="communities", help="Bootstrap source")
    memory_bootstrap_parser.add_argument("--offset", type=int, default=0, help="Start offset for resumable batching")
    memory_bootstrap_parser.add_argument("--limit", type=int, default=0, help="Optional item limit")

    memory_add_parser = subparsers.add_parser("memory-add", help="Add a fact into Mem0")
    memory_add_parser.add_argument("text", help="Fact text")
    memory_add_parser.add_argument("--root", default=".", help="Repository root")
    memory_add_parser.add_argument("--user-id", default="dxax-wiki", help="Mem0 user id namespace")
    memory_add_parser.add_argument("--source", default="manual", help="Metadata source label")

    memory_search_parser = subparsers.add_parser("memory-search", help="Search Mem0 facts")
    memory_search_parser.add_argument("query", help="Search query")
    memory_search_parser.add_argument("--root", default=".", help="Repository root")
    memory_search_parser.add_argument("--user-id", default="dxax-wiki", help="Mem0 user id namespace")
    memory_search_parser.add_argument("--top-k", type=int, default=5, help="Result count")

    memory_check_parser = subparsers.add_parser("memory-check", help="Check local Ollama models for Mem0")
    memory_check_parser.add_argument("--root", default=".", help="Repository root")

    args = parser.parse_args()
    repo_root = Path(args.root).resolve()

    if args.command == "build":
        build = build_index(repo_root)
        paths = write_outputs(repo_root, build)
        result = {
            "written": {key: str(value) for key, value in paths.items()},
            "stats": build["graph"]["stats"],
            "facets": build["graph"]["facets"],
        }
        if args.render_graph:
            result["graph_svg"] = str(render_graph(paths["graph_path"]))
        emit_json(result)
        return

    if args.command == "route":
        cache = load_query_cache(repo_root)
        result = score_pages(repo_root, cache, args.query, args.limit)
        emit_json(result)
        return

    if args.command == "ask":
        cache = load_query_cache(repo_root)
        result = score_pages(repo_root, cache, args.query, args.limit)
        log_paths = append_query_log(repo_root, result)
        instruction = "Read only the read_plan pages unless more context is still needed."
        if bool(result.get("query_profile", {}).get("is_code_query")):
            instruction = "Read code_read_plan first, then consult read_plan markdown only if broader context is still needed."
        result["workflow"] = {
            "mode": "graph-first",
            "instruction": instruction,
            "log_paths": {key: str(value) for key, value in log_paths.items()},
        }
        emit_json(result)
        return

    if args.command == "graph-query":
        graph = load_code_graph(repo_root)
        emit_json(
            {
                "query": args.query,
                "results": search_nodes(graph, args.query, limit=args.limit),
                "stats": graph.get("stats", {}),
            }
        )
        return

    if args.command == "graph-neighbors":
        graph = load_code_graph(repo_root)
        emit_json(neighbors_for_node(graph, args.node, limit=args.limit))
        return

    if args.command == "graph-explain":
        graph = load_code_graph(repo_root)
        emit_json(explain_node(graph, args.node, neighbor_limit=args.limit))
        return

    if args.command == "graph-path":
        graph = load_code_graph(repo_root)
        emit_json(shortest_path_between(graph, args.source, args.target, max_depth=args.max_depth))
        return

    if args.command == "memory-bootstrap":
        cache = load_query_cache(repo_root)
        if args.mode == "pages":
            items = list(cache["pages"].values())  # type: ignore[arg-type]
        else:
            items = []
            for community_id, community in cache.get("communities", {}).items():  # type: ignore[assignment]
                items.append(
                    {
                        "id": community_id,
                        "title": community_id,
                        "path": ", ".join(community.get("paths", [])[:5]),
                        "summary": community.get("summary", ""),
                        "tags": [tag for tag, _ in community.get("top_tags", [])],
                        "topics": [topic for topic, _ in community.get("top_topics", [])],
                        "entities": [entity for entity, _ in community.get("top_entities", [])],
                    }
                )
        result = bootstrap_memory(repo_root, items, user_id=args.user_id, offset=args.offset, limit=args.limit)
        emit_json(result)
        return

    if args.command == "memory-add":
        result = memory_add(
            repo_root,
            args.text,
            user_id=args.user_id,
            metadata={"source": args.source},
        )
        emit_json(result)
        return

    if args.command == "memory-search":
        result = memory_search(repo_root, args.query, user_id=args.user_id, top_k=args.top_k)
        emit_json(result)
        return

    if args.command == "memory-check":
        result = check_ollama_models()
        emit_json(result)
        return


if __name__ == "__main__":
    main()
