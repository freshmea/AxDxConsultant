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


def emit_json(payload: Dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.buffer.write(data.encode("utf-8"))


def load_json(path: Path) -> Dict[str, object] | List[object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_query_cache(repo_root: Path) -> Dict[str, object]:
    cache_path = repo_root / "wiki" / "system" / "query_cache.json"
    return load_json(cache_path)  # type: ignore[return-value]


def score_pages(cache: Dict[str, object], query: str, limit: int) -> Dict[str, object]:
    query_tokens = tokenize(query)
    pages: Dict[str, Dict[str, object]] = cache["pages"]  # type: ignore[assignment]
    scores: List[Dict[str, object]] = []
    total_tokens = sum(int(page["tokens_estimate"]) for page in pages.values())

    for page_id, page in pages.items():
        terms = Counter(page["terms"])  # type: ignore[arg-type]
        direct = sum(terms[token] for token in query_tokens)
        title_hits = sum(4 for token in query_tokens if token in tokenize(str(page["title"])))
        heading_hits = sum(2 for token in query_tokens if token in tokenize(" ".join(page["headings"])))
        tag_hits = sum(3 for token in query_tokens if token in tokenize(" ".join(page["tags"])))
        topic_hits = sum(2 for token in query_tokens if token in tokenize(" ".join(page["topics"])))
        entity_hits = sum(2 for token in query_tokens if token in tokenize(" ".join(page["entities"])))
        semantic_score = direct + title_hits + heading_hits + tag_hits + topic_hits + entity_hits
        if semantic_score <= 0:
            continue
        score = semantic_score + min(int(page["inbound_count"]), 5)
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
        result = score_pages(cache, args.query, args.limit)
        emit_json(result)
        return

    if args.command == "ask":
        cache = load_query_cache(repo_root)
        result = score_pages(cache, args.query, args.limit)
        log_paths = append_query_log(repo_root, result)
        result["workflow"] = {
            "mode": "graph-first",
            "instruction": "Read only the read_plan pages unless more context is still needed.",
            "log_paths": {key: str(value) for key, value in log_paths.items()},
        }
        emit_json(result)
        return


if __name__ == "__main__":
    main()
