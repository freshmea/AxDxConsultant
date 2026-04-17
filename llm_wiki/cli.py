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
from .memory_layer import bootstrap_memory, check_ollama_models, memory_add, memory_search
from .semantic import search_semantic


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
    semantic_hits = {item["id"]: item for item in search_semantic(repo_root / "wiki" / "system", query, limit=max(limit * 2, 8))}
    community_scores: Dict[str, int] = {}

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
        semantic_score = direct + title_hits + heading_hits + tag_hits + topic_hits + entity_hits
        total_score = semantic_score + semantic_bonus + community_bonus
        if total_score <= 0:
            continue
        score = total_score + min(int(page["inbound_count"]), 5)
        scores.append(
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
                    "inbound": min(int(page["inbound_count"]), 5),
                },
            }
        )

    scores.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
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
            "tokens_estimate": pages[page_id]["tokens_estimate"],
        }
        for page_id in expanded_ids
    ]
    routed_tokens = sum(int(page["tokens_estimate"]) for page in routed_pages)

    return {
        "query": query,
        "selected": selected,
        "read_plan": routed_pages,
        "token_budget": {
            "full_corpus_estimate": total_tokens,
            "targeted_read_estimate": routed_tokens,
            "saved_estimate": max(total_tokens - routed_tokens, 0),
            "savings_ratio": round(max(total_tokens - routed_tokens, 0) / total_tokens, 4) if total_tokens else 0,
        },
        "semantic_hits": list(semantic_hits.values())[:limit],
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

    memory_bootstrap_parser = subparsers.add_parser("memory-bootstrap", help="Push wiki summaries into Mem0")
    memory_bootstrap_parser.add_argument("--root", default=".", help="Repository root")
    memory_bootstrap_parser.add_argument("--user-id", default="dxax-wiki", help="Mem0 user id namespace")

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
        result["workflow"] = {
            "mode": "graph-first",
            "instruction": "Read only the read_plan pages unless more context is still needed.",
            "log_paths": {key: str(value) for key, value in log_paths.items()},
        }
        emit_json(result)
        return

    if args.command == "memory-bootstrap":
        cache = load_query_cache(repo_root)
        result = bootstrap_memory(repo_root, list(cache["pages"].values()), user_id=args.user_id)  # type: ignore[arg-type]
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
