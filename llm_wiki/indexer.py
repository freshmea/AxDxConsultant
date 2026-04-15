from __future__ import annotations

import json
import math
import fnmatch
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
WORD_RE = re.compile(r"[0-9A-Za-z가-힣_]+")
FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
DELETED_PATH_RE = re.compile(r"`?(?:tmp/)?kuBig2026/[^\s`]+`?", re.IGNORECASE)
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "wiki",
    "output",
}
READ_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")
IGNORE_FILE_NAME = ".llmwikiignore"


@dataclass
class PageRecord:
    page_id: str
    title: str
    relpath: str
    summary: str
    headings: List[str]
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
    return summary[:240]


def extract_headings(content: str) -> List[str]:
    headings: List[str] = []
    for line in content.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            headings.append(strip_deleted_path_mentions(match.group(2).strip()))
    return headings[:12]


def resolve_markdown_target(current_path: Path, href: str, root: Path, known_pages: Dict[str, str]) -> Tuple[str | None, str | None]:
    raw_target = href.strip()
    if not raw_target or raw_target.startswith(("http://", "https://", "mailto:", "#")):
        return None, None
    target = raw_target.split("#", 1)[0].split("?", 1)[0].strip()
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

    for path in files:
        relpath = path.relative_to(repo_root).as_posix()
        page_id = normalize_page_id(relpath)
        content = raw_contents[path]
        title = extract_title(content, path.stem)
        headings = extract_headings(content)
        summary = extract_summary(content)
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

        combined_terms = tokenize(" ".join([title, summary, " ".join(headings), relpath]))
        query_terms[page_id].update(combined_terms)

        pages.append(
            PageRecord(
                page_id=page_id,
                title=title,
                relpath=relpath,
                summary=summary,
                headings=headings,
                tokens_estimate=tokens_estimate,
                word_count=word_count,
                outbound_links=sorted(set(outbound)),
                unresolved_links=sorted(set(unresolved)),
            )
        )

    pages.sort(key=lambda page: page.relpath.lower())
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
                "tokens_estimate": page.tokens_estimate,
                "word_count": page.word_count,
                "outbound_links": page.outbound_links,
                "unresolved_links": page.unresolved_links,
                "inbound_count": inbound_counts.get(page.page_id, 0),
            }
            for page in pages
        ],
        "edges": edges,
        "stats": {
            "markdown_pages": len(pages),
            "resolved_edges": len(edges),
            "unresolved_links": sum(len(page.unresolved_links) for page in pages),
            "total_tokens_estimate": sum(page.tokens_estimate for page in pages),
        },
    }

    query_cache = {
        "generated_at": graph["generated_at"],
        "pages": {
            page.page_id: {
                "title": page.title,
                "path": page.relpath,
                "summary": page.summary,
                "headings": page.headings,
                "terms": dict(query_terms[page.page_id]),
                "neighbors": page.outbound_links,
                "inbound_count": inbound_counts.get(page.page_id, 0),
                "tokens_estimate": page.tokens_estimate,
            }
            for page in pages
        },
    }

    return {
        "graph": graph,
        "query_cache": query_cache,
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
    index_md_path = wiki_root / "index.md"
    log_path = wiki_root / "log.md"

    graph = build["graph"]
    pages: List[PageRecord] = build["pages"]  # type: ignore[assignment]
    unresolved_counts: Counter[str] = build["unresolved_counts"]  # type: ignore[assignment]

    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
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
                        "tokens_estimate": page.tokens_estimate,
                        "outbound_links": page.outbound_links,
                        "unresolved_links": page.unresolved_links,
                    }
                    for page in pages
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    cache_path.write_text(json.dumps(build["query_cache"], ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Wiki Index",
        "",
        f"- Generated: {graph['generated_at']}",
        f"- Markdown pages: {graph['stats']['markdown_pages']}",
        f"- Resolved edges: {graph['stats']['resolved_edges']}",
        f"- Estimated full-read tokens: {graph['stats']['total_tokens_estimate']}",
        f"- Ignore file: `{IGNORE_FILE_NAME}`",
        "",
        "## Pages",
        "",
    ]
    for page in pages:
        lines.append(f"- [{page.title}](../{page.relpath})")
        lines.append(f"  - Path: `{page.relpath}`")
        lines.append(f"  - Summary: {page.summary or '(summary unavailable)'}")
        lines.append(f"  - Links: {len(page.outbound_links)} outbound / {len(page.unresolved_links)} unresolved")
    if unresolved_counts:
        lines.extend(["", "## Unresolved Links", ""])
        for target, count in unresolved_counts.most_common(20):
            lines.append(f"- `{target}` x {count}")
    index_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"## [{timestamp}] build | markdown graph refresh\n"
        f"- pages: {graph['stats']['markdown_pages']}\n"
        f"- edges: {graph['stats']['resolved_edges']}\n"
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
        "index_md_path": index_md_path,
        "log_path": log_path,
    }
