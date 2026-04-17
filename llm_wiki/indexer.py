from __future__ import annotations

import fnmatch
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import unquote

from .community import build_communities
from .obsidian_bridge import build_obsidian_semantic_cache
from .semantic import build_semantic_index


WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TAG_BLOCK_RE = re.compile(r"^tags:\s*\[(.*?)\]\s*$", re.MULTILINE)
INLINE_TAG_RE = re.compile(r"(?:^|\s)#([0-9A-Za-z가-힣_\-]+)")
WORD_RE = re.compile(r"[0-9A-Za-z가-힣_]+")
FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
DELETED_PATH_RE = re.compile(r"`?(?:tmp/)?kuBig2026/[^\s`]+`?", re.IGNORECASE)
IGNORE_FILE_NAME = ".llmwikiignore"
READ_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "wiki",
    "output",
}
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "tags",
    "index",
    "문서",
    "개요",
    "관련",
    "내용",
    "정리",
    "보고서",
    "요약",
    "프로젝트",
    "실습결과물",
}


@dataclass
class PageRecord:
    page_id: str
    title: str
    relpath: str
    summary: str
    headings: List[str]
    tags: List[str]
    topics: List[str]
    entities: List[str]
    tokens_estimate: int
    word_count: int
    outbound_links: List[str]
    unresolved_links: List[str]


@dataclass
class IgnoreRules:
    patterns: List[str]


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in WORD_RE.findall(text)]


def read_markdown(path: Path) -> str:
    for encoding in READ_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def strip_deleted_path_mentions(text: str) -> str:
    cleaned = DELETED_PATH_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" -,:;")


def normalize_page_id(relpath: str) -> str:
    return Path(relpath).with_suffix("").as_posix()


def extract_title(content: str, fallback: str) -> str:
    normalized = content.lstrip("\ufeff")
    for line in normalized.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def strip_frontmatter(content: str) -> str:
    content = content.lstrip("\ufeff")
    if content.startswith("---\n"):
        return FRONTMATTER_RE.sub("", content, count=1)
    return content


def extract_summary(content: str) -> str:
    body = strip_frontmatter(content)
    paragraphs: List[str] = []
    current: List[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith("#"):
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    summary = strip_deleted_path_mentions(paragraphs[0] if paragraphs else "")
    return summary[:280]


def extract_headings(content: str) -> List[str]:
    headings: List[str] = []
    for line in content.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            headings.append(strip_deleted_path_mentions(match.group(2).strip()))
    return headings[:16]


def extract_tags(content: str) -> List[str]:
    tags: List[str] = []
    for match in TAG_BLOCK_RE.findall(content):
        for raw in match.split(","):
            cleaned = raw.strip().strip("'\"")
            if cleaned:
                tags.append(cleaned)
    for tag in INLINE_TAG_RE.findall(content):
        cleaned = tag.strip()
        if cleaned:
            tags.append(cleaned)
    return sorted(dict.fromkeys(tags))


def top_terms(texts: List[str], limit: int = 8) -> List[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        for token in tokenize(text):
            if len(token) < 2 or token in STOPWORDS:
                continue
            counts[token] += 1
    return [token for token, _ in counts.most_common(limit)]


def extract_topics(title: str, headings: List[str], summary: str, tags: List[str]) -> List[str]:
    terms = top_terms([title, summary, *headings], limit=8)
    return sorted(dict.fromkeys([*tags[:4], *terms]))[:10]


def extract_entities(title: str, headings: List[str], summary: str, tags: List[str]) -> List[str]:
    candidates = []
    candidates.extend(tags)
    candidates.extend(top_terms([title, *headings], limit=10))
    summary_terms = [token for token in top_terms([summary], limit=8) if token not in candidates]
    candidates.extend(summary_terms[:4])
    return sorted(dict.fromkeys(candidates))[:12]


def resolve_markdown_target(current_path: Path, href: str, root: Path, known_pages: Dict[str, str]) -> Tuple[str | None, str | None]:
    raw_target = href.strip()
    if not raw_target or raw_target.startswith(("http://", "https://", "mailto:", "#")):
        return None, None
    target = unquote(raw_target.split("#", 1)[0].split("?", 1)[0].strip())
    if not target:
        return None, None
    if target.endswith(".md"):
        candidate = (current_path.parent / target).resolve()
        try:
            relpath = candidate.relative_to(root).as_posix()
        except ValueError:
            return None, target
        page_id = normalize_page_id(relpath)
        if page_id in known_pages:
            return page_id, None
        return None, target
    return None, None


def resolve_wiki_target(label: str, known_titles: Dict[str, str], known_pages: Dict[str, str]) -> Tuple[str | None, str | None]:
    cleaned = label.strip()
    if not cleaned:
        return None, None
    if cleaned in known_titles:
        return known_titles[cleaned], None
    candidate_id = cleaned.replace("\\", "/").strip("/")
    if candidate_id in known_pages:
        return candidate_id, None
    if f"{candidate_id}.md" in known_pages.values():
        return normalize_page_id(f"{candidate_id}.md"), None
    return None, cleaned


def load_ignore_rules(root: Path) -> IgnoreRules:
    ignore_path = root / IGNORE_FILE_NAME
    patterns: List[str] = []
    if ignore_path.exists():
        for line in ignore_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            patterns.append(stripped.replace("\\", "/"))
    return IgnoreRules(patterns=patterns)


def matches_ignore(relpath: str, rules: IgnoreRules) -> bool:
    normalized = relpath.replace("\\", "/")
    for pattern in rules.patterns:
        if pattern.endswith("/"):
            base = pattern.rstrip("/")
            if normalized == base or normalized.startswith(f"{base}/"):
                return True
            continue
        if any(char in pattern for char in "*?[]"):
            if fnmatch.fnmatch(normalized, pattern):
                return True
            continue
        if normalized == pattern or normalized.startswith(f"{pattern}/"):
            return True
        if fnmatch.fnmatch(normalized, f"**/{pattern}"):
            return True
    return False


def iter_markdown_files(root: Path, ignore_rules: IgnoreRules) -> Iterable[Path]:
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        relpath = path.relative_to(root).as_posix()
        if matches_ignore(relpath, ignore_rules):
            continue
        yield path


def build_index(repo_root: Path) -> Dict[str, object]:
    ignore_rules = load_ignore_rules(repo_root)
    files = sorted(iter_markdown_files(repo_root, ignore_rules))
    known_pages: Dict[str, str] = {}
    title_lookup: Dict[str, str] = {}
    raw_contents: Dict[Path, str] = {}

    for path in files:
        relpath = path.relative_to(repo_root).as_posix()
        page_id = normalize_page_id(relpath)
        content = read_markdown(path)
        raw_contents[path] = content
        known_pages[page_id] = relpath
        title_lookup[extract_title(content, path.stem)] = page_id

    pages: List[PageRecord] = []
    edges: List[Dict[str, str]] = []
    inbound_counts: Counter[str] = Counter()
    unresolved_counts: Counter[str] = Counter()
    query_terms: Dict[str, Counter[str]] = defaultdict(Counter)
    tag_counts: Counter[str] = Counter()
    entity_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()

    for path in files:
        relpath = path.relative_to(repo_root).as_posix()
        page_id = normalize_page_id(relpath)
        content = raw_contents[path]
        title = extract_title(content, path.stem)
        headings = extract_headings(content)
        summary = extract_summary(content)
        tags = extract_tags(content)
        topics = extract_topics(title, headings, summary, tags)
        entities = extract_entities(title, headings, summary, tags)
        word_count = len(tokenize(content))
        tokens_estimate = estimate_tokens(content)
        outbound: List[str] = []
        unresolved: List[str] = []

        for match in WIKI_LINK_RE.findall(content):
            target_id, unresolved_target = resolve_wiki_target(match, title_lookup, known_pages)
            if target_id:
                outbound.append(target_id)
                edges.append({"source": page_id, "target": target_id, "kind": "wikilink"})
                inbound_counts[target_id] += 1
            elif unresolved_target:
                unresolved.append(unresolved_target)
                unresolved_counts[unresolved_target] += 1

        for href in MD_LINK_RE.findall(content):
            target_id, unresolved_target = resolve_markdown_target(path, href, repo_root, known_pages)
            if target_id:
                outbound.append(target_id)
                edges.append({"source": page_id, "target": target_id, "kind": "markdown"})
                inbound_counts[target_id] += 1
            elif unresolved_target:
                unresolved.append(unresolved_target)
                unresolved_counts[unresolved_target] += 1

        combined_terms = tokenize(" ".join([title, summary, " ".join(headings), relpath, " ".join(tags), " ".join(topics), " ".join(entities)]))
        query_terms[page_id].update(combined_terms)
        tag_counts.update(tags)
        entity_counts.update(entities)
        topic_counts.update(topics)

        pages.append(
            PageRecord(
                page_id=page_id,
                title=title,
                relpath=relpath,
                summary=summary,
                headings=headings,
                tags=tags,
                topics=topics,
                entities=entities,
                tokens_estimate=tokens_estimate,
                word_count=word_count,
                outbound_links=sorted(set(outbound)),
                unresolved_links=sorted(set(unresolved)),
            )
        )

    pages.sort(key=lambda page: page.relpath.lower())
    community_graph, community_summaries, page_to_communities = build_communities(pages, edges, inbound_counts)
    obsidian_cache = build_obsidian_semantic_cache(repo_root, pages)
    graph = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "nodes": [
            {
                "id": page.page_id,
                "title": page.title,
                "path": page.relpath,
                "summary": page.summary,
                "headings": page.headings,
                "tags": page.tags,
                "topics": page.topics,
                "entities": page.entities,
                "tokens_estimate": page.tokens_estimate,
                "word_count": page.word_count,
                "outbound_links": page.outbound_links,
                "unresolved_links": page.unresolved_links,
                "inbound_count": inbound_counts.get(page.page_id, 0),
                "community_ids": page_to_communities.get(page.page_id, []),
                "obsidian_related_count": len(obsidian_cache.get("pages", {}).get(page.page_id, {}).get("related", [])),
            }
            for page in pages
        ],
        "edges": edges,
        "communities": community_summaries["communities"],
        "stats": {
            "markdown_pages": len(pages),
            "resolved_edges": len(edges),
            "unresolved_links": sum(len(page.unresolved_links) for page in pages),
            "total_tokens_estimate": sum(page.tokens_estimate for page in pages),
            "community_count": community_summaries["stats"]["community_count"],
        },
        "facets": {
            "top_tags": tag_counts.most_common(15),
            "top_topics": topic_counts.most_common(15),
            "top_entities": entity_counts.most_common(15),
        },
    }

    structure_index = {
        "generated_at": graph["generated_at"],
        "pages": [
            {
                "id": page.page_id,
                "title": page.title,
                "path": page.relpath,
                "tags": page.tags,
                "topics": page.topics,
                "entities": page.entities,
                "summary": page.summary,
                "neighbors": page.outbound_links,
                "inbound_count": inbound_counts.get(page.page_id, 0),
                "tokens_estimate": page.tokens_estimate,
                "community_ids": page_to_communities.get(page.page_id, []),
                "obsidian_related": obsidian_cache.get("pages", {}).get(page.page_id, {}).get("related", []),
            }
            for page in pages
        ],
        "communities": community_summaries["communities"],
    }

    query_cache = {
        "generated_at": graph["generated_at"],
        "pages": {
            page.page_id: {
                "title": page.title,
                "path": page.relpath,
                "summary": page.summary,
                "headings": page.headings,
                "tags": page.tags,
                "topics": page.topics,
                "entities": page.entities,
                "terms": dict(query_terms[page.page_id]),
                "neighbors": page.outbound_links,
                "inbound_count": inbound_counts.get(page.page_id, 0),
                "tokens_estimate": page.tokens_estimate,
                "community_ids": page_to_communities.get(page.page_id, []),
                "obsidian_related": obsidian_cache.get("pages", {}).get(page.page_id, {}).get("related", []),
            }
            for page in pages
        },
        "communities": {
            community["id"]: {
                "summary": community["summary"],
                "top_tags": community["top_tags"],
                "top_topics": community["top_topics"],
                "top_entities": community["top_entities"],
                "page_ids": community["page_ids"],
                "paths": community["paths"],
            }
            for community in community_summaries["communities"]
        },
        "obsidian": {
            "enabled": bool(obsidian_cache.get("enabled")),
            "model": obsidian_cache.get("model", {}),
        },
    }

    return {
        "graph": graph,
        "structure_index": structure_index,
        "query_cache": query_cache,
        "community_graph": community_graph,
        "community_summaries": community_summaries,
        "obsidian_cache": obsidian_cache,
        "pages": pages,
        "unresolved_counts": unresolved_counts,
        "ignore_patterns": ignore_rules.patterns,
    }


def write_outputs(repo_root: Path, build: Dict[str, object]) -> Dict[str, Path]:
    wiki_root = repo_root / "wiki"
    system_root = wiki_root / "system"
    notes_root = wiki_root / "notes"
    system_root.mkdir(parents=True, exist_ok=True)
    notes_root.mkdir(parents=True, exist_ok=True)

    graph_path = system_root / "link_graph.json"
    index_json_path = system_root / "page_index.json"
    cache_path = system_root / "query_cache.json"
    structure_path = system_root / "structure_index.json"
    community_graph_path = system_root / "community_graph.json"
    community_summaries_path = system_root / "community_summaries.json"
    obsidian_cache_path = system_root / "obsidian_semantic_cache.json"
    report_path = wiki_root / "graph_report.md"
    community_report_path = wiki_root / "community_report.md"
    query_log_json_path = system_root / "query_log.json"
    query_log_md_path = wiki_root / "query_log.md"
    index_md_path = wiki_root / "index.md"
    log_path = wiki_root / "log.md"

    graph = build["graph"]
    structure_index = build["structure_index"]
    community_graph = build["community_graph"]
    community_summaries = build["community_summaries"]
    obsidian_cache = build["obsidian_cache"]
    pages: List[PageRecord] = build["pages"]  # type: ignore[assignment]
    unresolved_counts: Counter[str] = build["unresolved_counts"]  # type: ignore[assignment]

    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    structure_path.write_text(json.dumps(structure_index, ensure_ascii=False, indent=2), encoding="utf-8")
    community_graph_path.write_text(json.dumps(community_graph, ensure_ascii=False, indent=2), encoding="utf-8")
    community_summaries_path.write_text(json.dumps(community_summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    obsidian_cache_path.write_text(json.dumps(obsidian_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    index_json_path.write_text(
        json.dumps(
            {
                "generated_at": graph["generated_at"],
                "pages": [
                    {
                        "id": page.page_id,
                        "title": page.title,
                        "path": page.relpath,
                        "summary": page.summary,
                        "tags": page.tags,
                        "topics": page.topics,
                        "entities": page.entities,
                        "tokens_estimate": page.tokens_estimate,
                        "outbound_links": page.outbound_links,
                        "unresolved_links": page.unresolved_links,
                        "community_ids": structure_index["pages"][idx]["community_ids"],
                        "obsidian_related": structure_index["pages"][idx]["obsidian_related"],
                    }
                    for idx, page in enumerate(pages)
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    cache_path.write_text(json.dumps(build["query_cache"], ensure_ascii=False, indent=2), encoding="utf-8")
    semantic_meta = build_semantic_index(
        system_root,
        [
            {
                "id": page.page_id,
                "title": page.title,
                "path": page.relpath,
                "summary": page.summary,
                "headings": page.headings,
                "tags": page.tags,
                "topics": page.topics,
                "entities": page.entities,
            }
            for page in pages
        ],
    )

    if not query_log_json_path.exists():
        query_log_json_path.write_text("[]\n", encoding="utf-8")
    if not query_log_md_path.exists():
        query_log_md_path.write_text("# Query Log\n\n", encoding="utf-8")

    lines = [
        "# Wiki Index",
        "",
        f"- Generated: {graph['generated_at']}",
        f"- Markdown pages: {graph['stats']['markdown_pages']}",
        f"- Resolved edges: {graph['stats']['resolved_edges']}",
        f"- Communities: {graph['stats']['community_count']}",
        f"- Estimated full-read tokens: {graph['stats']['total_tokens_estimate']}",
        f"- Ignore file: `{IGNORE_FILE_NAME}`",
        f"- Semantic search: {'enabled' if semantic_meta.get('enabled') else 'disabled'}",
        f"- Smart Connections bridge: {'enabled' if obsidian_cache.get('enabled') else 'disabled'}",
        "",
        "## Pages",
        "",
    ]
    for page in pages:
        lines.append(f"- [{page.title}](../{page.relpath})")
        lines.append(f"  - Path: `{page.relpath}`")
        lines.append(f"  - Summary: {page.summary or '(summary unavailable)'}")
        lines.append(f"  - Tags: {', '.join(page.tags) if page.tags else '(none)'}")
        lines.append(f"  - Topics: {', '.join(page.topics[:5]) if page.topics else '(none)'}")
        lines.append(f"  - Links: {len(page.outbound_links)} outbound / {len(page.unresolved_links)} unresolved")
        lines.append(f"  - Smart Connections neighbors: {len(obsidian_cache.get('pages', {}).get(page.page_id, {}).get('related', []))}")
    if unresolved_counts:
        lines.extend(["", "## Unresolved Links", ""])
        for target, count in unresolved_counts.most_common(20):
            lines.append(f"- `{target}` x {count}")
    index_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    connected = sorted(pages, key=lambda page: (-len(page.outbound_links), page.relpath))[:10]
    inbound_sorted = sorted(pages, key=lambda page: (-next((node["inbound_count"] for node in graph["nodes"] if node["id"] == page.page_id), 0), page.relpath))[:10]
    orphan_pages = [page for page in pages if not page.outbound_links]
    report_lines = [
        "# Graph Report",
        "",
        f"- Generated: {graph['generated_at']}",
        f"- Pages: {graph['stats']['markdown_pages']}",
        f"- Edges: {graph['stats']['resolved_edges']}",
        f"- Estimated full corpus tokens: {graph['stats']['total_tokens_estimate']}",
        f"- Smart Connections bridge: {'enabled' if obsidian_cache.get('enabled') else 'disabled'}",
        "",
        "## Top Tags",
        "",
    ]
    for tag, count in graph["facets"]["top_tags"]:
        report_lines.append(f"- `{tag}` x {count}")
    report_lines.extend(["", "## Top Topics", ""])
    for topic, count in graph["facets"]["top_topics"]:
        report_lines.append(f"- `{topic}` x {count}")
    report_lines.extend(["", "## Top Entities", ""])
    for entity, count in graph["facets"]["top_entities"]:
        report_lines.append(f"- `{entity}` x {count}")
    report_lines.extend(["", "## Communities", ""])
    for community in community_summaries["communities"][:12]:
        report_lines.append(
            f"- `{community['id']}` | size={community['size']} | representative=[{community['representative_title']}](../{community['representative_path']})"
        )
    report_lines.extend(["", "## Most Connected Pages", ""])
    for page in connected:
        report_lines.append(f"- [{page.title}](../{page.relpath}) | outbound={len(page.outbound_links)}")
    report_lines.extend(["", "## Most Referenced Pages", ""])
    for page in inbound_sorted:
        inbound_count = next((node["inbound_count"] for node in graph["nodes"] if node["id"] == page.page_id), 0)
        report_lines.append(f"- [{page.title}](../{page.relpath}) | inbound={inbound_count}")
    report_lines.extend(["", "## Orphan Candidates", ""])
    for page in orphan_pages[:20]:
        report_lines.append(f"- [{page.title}](../{page.relpath})")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    community_lines = [
        "# Community Report",
        "",
        f"- Generated: {graph['generated_at']}",
        f"- Community count: {community_summaries['stats']['community_count']}",
        "",
    ]
    for community in community_summaries["communities"]:
        community_lines.append(f"## {community['id']}")
        community_lines.append("")
        community_lines.append(f"- Representative: [{community['representative_title']}](../{community['representative_path']})")
        community_lines.append(f"- Size: {community['size']}")
        community_lines.append(f"- Summary: {community['summary']}")
        community_lines.append(f"- Topics: {', '.join(topic for topic, _ in community['top_topics']) or '(none)'}")
        community_lines.append(f"- Entities: {', '.join(entity for entity, _ in community['top_entities']) or '(none)'}")
        community_lines.append(f"- Pages: {', '.join(community['paths'])}")
        community_lines.append("")
    community_report_path.write_text("\n".join(community_lines), encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"## [{timestamp}] build | markdown graph refresh\n"
        f"- pages: {graph['stats']['markdown_pages']}\n"
        f"- edges: {graph['stats']['resolved_edges']}\n"
        f"- communities: {graph['stats']['community_count']}\n"
        f"- estimated tokens: {graph['stats']['total_tokens_estimate']}\n"
    )
    if log_path.exists():
        previous = log_path.read_text(encoding="utf-8", errors="ignore").rstrip()
        log_path.write_text(f"{previous}\n\n{entry}\n", encoding="utf-8")
    else:
        log_path.write_text(f"# Wiki Log\n\n{entry}\n", encoding="utf-8")

    return {
        "graph_path": graph_path,
        "index_json_path": index_json_path,
        "cache_path": cache_path,
        "structure_path": structure_path,
        "community_graph_path": community_graph_path,
        "community_summaries_path": community_summaries_path,
        "obsidian_cache_path": obsidian_cache_path,
        "report_path": report_path,
        "community_report_path": community_report_path,
        "semantic_index_path": system_root / "semantic_index.faiss",
        "semantic_meta_path": system_root / "semantic_meta.json",
        "query_log_json_path": query_log_json_path,
        "query_log_md_path": query_log_md_path,
        "index_md_path": index_md_path,
        "log_path": log_path,
    }
