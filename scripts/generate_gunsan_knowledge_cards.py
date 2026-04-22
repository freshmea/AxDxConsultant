from __future__ import annotations

import re
import subprocess
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from pypdf import PdfReader


REPO_ROOT = Path(r"C:\Users\Administrator\dxAx")
BIND_ROOT = Path(r"D:\bindsoft")
WIKI_RAW_ROOT = REPO_ROOT / "wiki" / "raw" / "bindsoft_gunsan_university"
TEMP_EXTRACT_ROOT = WIKI_RAW_ROOT / "_extract_cache"
KORDOC_PS1 = Path(r"C:\Users\Administrator\AppData\Roaming\npm\kordoc.ps1")

STOPWORDS = {
    "br",
    "and",
    "the",
    "section",
    "chapter",
    "part",
    "education",
    "program",
    "material",
    "document",
    "summary",
    "\uad50\uc721",
    "\uacfc\uc815",
    "\ud504\ub85c\uadf8\ub7a8",
    "\uc790\ub8cc",
    "\ubb38\uc11c",
    "\uc791\uc131",
    "\ud559\uc2b5",
    "\ubaa9\ud45c",
    "\ud6c4\uae30",
    "\ud504\ub85c\uc81d\ud2b8",
    "\uc218\uc5c5",
    "\uac15\uc758",
    "\ucc28\uc2dc",
    "\uad50\uc2dc",
    "\ub0b4\uc6a9",
    "\uc7ac\ub8cc",
    "\ucc38\uc870",
    "\uae30\ubcf8",
    "\uc0ac\uc6a9",
    "\uc124\uba85",
    "\uc9c4\ud589",
    "\uad00\ub828",
    "\uacbd\uc6b0",
    "\uacbd\uc6b0\uc5d0\ub294",
    "\ud55c\ub2e4",
    "\uc788\ub2e4",
    "\uc788\ub294",
    "\ub4f1",
    "\ubc0f",
    "\uc785\ucc30",
    "\uacf5\uace0",
    "\uc81c\uc548",
    "\uc81c\uc548\uc11c",
    "\uad50\uc7ac",
    "\uad70\uc0b0\ub300",
    "\uad70\uc0b0\ub300\ud559\uad50",
    "\ubc14\uc778\ub4dc",
    "\uc18c\ud504\ud2b8",
}

HEADING_HINTS = (
    "section",
    "chapter",
    "part",
    "program",
    "ros2",
    "python",
    "\ubaa9\ucc28",
    "\ucc28\ub840",
    "\uacfc\uc5c5",
    "\uac1c\uc694",
    "\ubaa9\uc801",
    "\uc218\uc5c5",
    "\uac15\uc758",
    "\ud559\uc2b5",
    "\ud6c4\uae30",
    "\ucc38\uc870",
)

XML_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


@dataclass
class DocRecord:
    source_path: Path
    relative_source: str
    title: str
    ext: str
    size_bytes: int
    page_count: int | None
    extraction_method: str
    text: str
    summary: str
    tags: list[str]
    aliases: list[str]
    topics: list[str]
    entities: list[str]
    headings: list[str]
    role: str
    queries: list[str]
    related_titles: list[str]
    output_path: Path | None = None


def find_gunsan_root() -> Path:
    education_root = next(p for p in BIND_ROOT.iterdir() if p.is_dir() and p.name.startswith("2."))
    return next(p for p in education_root.iterdir() if p.is_dir() and p.name.startswith("1."))


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("<br>", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def run_kordoc(source_path: Path) -> Path | None:
    TEMP_EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    output_path = TEMP_EXTRACT_ROOT / f"{source_path.stem}.md"
    if output_path.exists():
        return output_path
    if not KORDOC_PS1.exists():
        return None
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(KORDOC_PS1),
        "--silent",
        "-d",
        str(TEMP_EXTRACT_ROOT),
        str(source_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 or not output_path.exists():
        return None
    return output_path


def read_hwp(source_path: Path) -> tuple[str, str]:
    output_path = run_kordoc(source_path)
    if not output_path:
        return "", "kordoc_failed"
    return clean_text(output_path.read_text(encoding="utf-8", errors="replace")), "kordoc"


def read_docx(source_path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(source_path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", XML_NS):
        runs = [node.text for node in paragraph.findall(".//w:t", XML_NS) if node.text]
        if runs:
            paragraphs.append("".join(runs))
    return clean_text("\n".join(paragraphs)), "docx_xml"


def read_pptx(source_path: Path) -> tuple[str, str]:
    slides: list[str] = []
    with zipfile.ZipFile(source_path) as zf:
        slide_names = sorted(
            name
            for name in zf.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        for slide_name in slide_names:
            root = ET.fromstring(zf.read(slide_name))
            tokens = [node.text for node in root.findall(".//a:t", XML_NS) if node.text]
            if tokens:
                slides.append("\n".join(tokens))
    return clean_text("\n\n--- slide ---\n\n".join(slides)), "pptx_xml"


def read_pdf(source_path: Path) -> tuple[str, str, int | None]:
    reader = PdfReader(str(source_path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return clean_text("\n\n".join(pages)), "pypdf", len(reader.pages)


def read_txt(source_path: Path) -> tuple[str, str]:
    return clean_text(source_path.read_text(encoding="utf-8", errors="replace")), "text"


def extract_text(source_path: Path) -> tuple[str, str, int | None]:
    ext = source_path.suffix.lower()
    if ext == ".hwp":
        text, method = read_hwp(source_path)
        return text, method, None
    if ext == ".docx":
        text, method = read_docx(source_path)
        return text, method, None
    if ext == ".pptx":
        text, method = read_pptx(source_path)
        return text, method, None
    if ext == ".pdf":
        text, method, pages = read_pdf(source_path)
        return text, method, pages
    if ext == ".txt":
        text, method = read_txt(source_path)
        return text, method, None
    return "", "unsupported", None


def infer_role(title: str, ext: str, text: str) -> str:
    lowered = f"{title}\n{text[:2000]}".lower()
    if "\uc785\ucc30\uacf5\uace0" in title:
        return "\uc785\ucc30 \uacf5\uace0 \ubb38\uc11c"
    if "\uc81c\uc548\uc694\uccad\uc11c" in title:
        return "RFP \uc81c\uc548\uc694\uccad \ubb38\uc11c"
    if "\uac15\uc758 \uacc4\ud68d\uc11c" in title:
        return "\uac15\uc758 \uc6b4\uc601 \uacc4\ud68d\uc11c"
    if "\uac1c\uc694\uc11c" in title:
        return "\ucc28\uc2dc\ubcc4 \uc218\uc5c5 \uac1c\uc694\uc11c"
    if "\uad50\uc7ac" in title:
        return "\uad50\uc721 \uad50\uc7ac"
    if "\uacbd\uacfc \uc790\ub8cc" in title:
        return "\uad50\uc721 \uc9c4\ud589 \uacbd\uacfc \uc790\ub8cc"
    if ext == ".txt":
        return "\ucc38\uc870 \ub9c1\ud06c \uba54\ubaa8"
    if "ros2" in lowered:
        return "ROS2 \uad50\uc721 \uc790\ub8cc"
    if "python" in lowered or "\ud30c\uc774\uc36c" in lowered:
        return "Python \uad50\uc721 \uc790\ub8cc"
    return "\uad50\uc721 \uad00\ub828 \ucc38\uace0 \ubb38\uc11c"


def collect_headings(text: str) -> list[str]:
    headings: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" #-\t")
        if not line:
            continue
        lower = line.lower()
        if len(line) <= 80 and (
            re.match(r"^(\d+([.-]\d+)*|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|section|chapter|part)", lower)
            or any(hint in lower for hint in HEADING_HINTS)
        ):
            headings.append(line)
    deduped: list[str] = []
    seen: set[str] = set()
    for heading in headings:
        if heading not in seen:
            deduped.append(heading)
            seen.add(heading)
    return deduped[:30]


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z0-9][가-힣A-Za-z0-9+/_-]{1,30}", text)
    cleaned: list[str] = []
    for token in tokens:
        lowered = token.lower()
        if token in STOPWORDS or lowered in STOPWORDS:
            continue
        if re.fullmatch(r"\d+", token):
            continue
        if len(token) < 2:
            continue
        cleaned.append(token)
    return cleaned


def infer_topics(title: str, text: str) -> list[str]:
    title_tokens = tokenize(title)
    body_counter = Counter(tokenize(text[:25000]))
    ordered: list[str] = []
    for token in title_tokens:
        if token not in ordered:
            ordered.append(token)
    for token, _ in body_counter.most_common(20):
        if token not in ordered:
            ordered.append(token)
    return ordered[:10]


def infer_entities(title: str, text: str) -> list[str]:
    pattern = (
        r"(군산대학교|군산대|바인드\s*소프트|최수길|ROS2|ROS|GitHub|Python|Ubuntu 20\.04|"
        r"X-Optimus|Optimus-X prime|TurtleBot|turtlebot|Nav2|Cartographer)"
    )
    matches = re.findall(pattern, f"{title}\n{text[:15000]}", flags=re.IGNORECASE)
    entities: list[str] = []
    for match in matches:
        token = match.strip()
        if token not in entities:
            entities.append(token)
    return entities[:12]


def infer_tags(title: str, ext: str, role: str, topics: list[str]) -> list[str]:
    tags = ["wiki/raw", "bindsoft", "gunsan-university", "education", ext.lstrip(".")]
    title_lower = title.lower()
    topic_lower = {topic.lower() for topic in topics}
    if "ros2" in title_lower or "ros2" in role.lower() or "ros2" in topic_lower:
        tags.append("ros2")
    if "python" in title_lower or "\ud30c\uc774\uc36c" in title_lower or "python" in topic_lower:
        tags.append("python")
    if "\uac15\uc758" in title or "\uc218\uc5c5" in title:
        tags.append("curriculum")
    if "\uac1c\uc694\uc11c" in title:
        tags.append("lesson-plan")
    if "\uacbd\uacfc" in title:
        tags.append("progress-report")
    if "\uad50\uc7ac" in title:
        tags.append("textbook")
    if "\uc785\ucc30" in title:
        tags.append("procurement")
    if "\uc81c\uc548" in title:
        tags.append("proposal")
    return tags


def build_summary(title: str, role: str, text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    meaningful: list[str] = []
    for line in lines:
        if len(line) <= 8:
            continue
        if re.fullmatch(r"[|:\- ]+", line):
            continue
        if line.startswith("|") and line.endswith("|"):
            continue
        meaningful.append(line)
    if not meaningful:
        return f"{title} \ubb38\uc11c\ub97c \uc815\ub9ac\ud55c {role} \uce74\ub4dc\ub2e4."
    body = " ".join(meaningful[:3])
    return f"{role}\ub85c \ubd84\ub958\ub418\uba70, \ud575\uc2ec \ub0b4\uc6a9\uc740 {body}"


def build_queries(title: str, role: str, headings: list[str]) -> list[str]:
    queries = [
        f"{title} \ubb38\uc11c\uc758 \ud575\uc2ec \ubaa9\uc801\uc740 \ubb34\uc5c7\uc778\uac00?",
        f"{title} \ubb38\uc11c\uc5d0\uc11c \uc694\uad6c\ud558\ub294 \uc8fc\uc694 \uc0b0\ucd9c\ubb3c\uc774\ub098 \uc77c\uc815\uc740 \ubb34\uc5c7\uc778\uac00?",
    ]
    role_lower = role.lower()
    if "ros2" in role_lower or "python" in role_lower or "\uad50\uc7ac" in role:
        queries.append(f"{title} \ubb38\uc11c\uc758 \ucc28\uc2dc\ubcc4 \uad50\uc721 \ub0b4\uc6a9\uacfc \ud559\uc2b5 \ubc94\uc704\ub294 \uc5b4\ub5bb\uac8c \uad6c\uc131\ub418\uc5b4 \uc788\ub294\uac00?")
    if "\uc785\ucc30" in role or "RFP" in role or "\uc81c\uc548" in role:
        queries.append(f"{title} \ubb38\uc11c\uc758 \uc608\uc0b0, \uae30\uac04, \uacc4\uc57d \ubc29\uc2dd, \ud3c9\uac00 \uae30\uc900\uc740 \ubb34\uc5c7\uc778\uac00?")
    if headings:
        queries.append(f"{title} \ubb38\uc11c\uc758 \ubaa9\ucc28 \ub610\ub294 \uc139\uc158 \uad6c\uc870\ub294 \uc5b4\ub5bb\uac8c \ub418\uc5b4 \uc788\ub294\uac00?")
    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        if query not in seen:
            deduped.append(query)
            seen.add(query)
    return deduped[:6]


def make_source_link(path: Path) -> str:
    return "/" + str(path).replace("\\", "/")


def safe_name(name: str) -> str:
    return re.sub(r"[<>:\"/\\\\|?*]+", "_", name).replace(" ", "_")


def relative_to_bindsoft(source_path: Path) -> str:
    return str(source_path.relative_to(BIND_ROOT)).replace("\\", "/")


def full_text_block(text: str) -> str:
    return text if text else "\ucd94\ucd9c \uac00\ub2a5\ud55c \ud14d\uc2a4\ud2b8\ub97c \ud655\ubcf4\ud558\uc9c0 \ubabb\ud588\ub2e4."


def render_card(doc: DocRecord) -> str:
    aliases = ", ".join(f'"{alias}"' for alias in doc.aliases)
    tags = ", ".join(f'"{tag}"' for tag in doc.tags)
    topics = ", ".join(f'"{topic}"' for topic in doc.topics)
    entities = ", ".join(f'"{entity}"' for entity in doc.entities)
    headings = ", ".join(f'"{heading}"' for heading in doc.headings[:20])
    heading_lines = "\n".join(f"- {heading}" for heading in doc.headings) or "- \uad6c\uc870 \ucd94\ucd9c \uc2e4\ud328"
    query_lines = "\n".join(f"- {query}" for query in doc.queries)
    related_lines = "\n".join(f"- [[{title}]]" for title in doc.related_titles) or "- \uc5f0\uacb0 \ud6c4\ubcf4 \uc5c6\uc74c"

    return f"""---
title: "{doc.title}"
source_name: "{doc.source_path.name}"
source_path: "{doc.source_path}"
source_relpath: "{doc.relative_source}"
source_link: "{make_source_link(doc.source_path)}"
doc_type: "{doc.ext.lstrip('.')}"
knowledge_card_type: "document_card"
role: "{doc.role}"
created_at: "{datetime.now().isoformat(timespec='seconds')}"
page_count: {doc.page_count if doc.page_count is not None else 'null'}
file_size_bytes: {doc.size_bytes}
extraction_method: "{doc.extraction_method}"
aliases: [{aliases}]
tags: [{tags}]
topics: [{topics}]
entities: [{entities}]
headings: [{headings}]
summary: "{doc.summary.replace('"', "'")}"
---

# {doc.title}

## 문서 정체
- 원본 파일: [{doc.source_path.name}]({make_source_link(doc.source_path)})
- 원본 상대경로: `{doc.relative_source}`
- 문서 유형: `{doc.ext}`
- 문서 역할: {doc.role}
- 파일 크기: `{doc.size_bytes}` bytes
- 페이지 수: `{doc.page_count}`
- 추출 방식: `{doc.extraction_method}`

## 핵심 요약
{doc.summary}

## 활용 맥락
- 이 카드는 군산대 X-Optimus 교육 관련 원문을 나중에 RAG, 옵시디안 링크, 그래프 탐색에서 바로 찾을 수 있도록 정리한 raw 지식 카드다.
- 원본 파일은 외부 경로에 유지하고, 이 문서는 `dxAx/wiki/raw` 안에서 검색 가능한 텍스트와 메타데이터를 제공한다.
- 문서 성격상 교육 운영, 교안, 입찰/RFP, 수업 회고, 참조 링크를 구분해 질의응답에 재사용할 수 있다.

## 주요 키워드
- 토픽: {", ".join(doc.topics) if doc.topics else "없음"}
- 개체: {", ".join(doc.entities) if doc.entities else "없음"}

## 구조 또는 목차 힌트
{heading_lines}

## RAG 검색 질의 예시
{query_lines}

## 연결 문서
{related_lines}

## 원문 기반 메모
- 제목과 본문 기준으로 군산대, X-Optimus, ROS2, Python, 자율주행, 제안요청, 입찰, 수업개요, 진행경과 같은 검색 축이 유효하다.
- 교육 운영 문서끼리는 일정, 차시, 실습 장비, 학습목표를 중심으로 묶어서 조회하면 검색 성능이 좋아진다.
- 제안/입찰 문서는 과업 목적, 예산, 기간, 계약 방식, 평가기준, 요구 산출물을 기준으로 찾도록 설계했다.

## 추출 텍스트
{full_text_block(doc.text)}
"""


def render_index(docs: list[DocRecord]) -> str:
    rows = []
    for doc in docs:
        rows.append(
            f"| [[{doc.title}]] | {doc.ext} | {doc.role} | "
            f"[{doc.source_path.name}]({make_source_link(doc.source_path)}) | "
            f"{', '.join(doc.tags[:6])} |"
        )
    table = "\n".join(rows)
    return f"""---
title: "군산대 문서 지식카드 인덱스"
tags: ["wiki/raw", "bindsoft", "gunsan-university", "index"]
summary: "군산대 외부 문서를 dxAx/wiki/raw 안에서 링크형 지식카드로 정리한 인덱스"
---

# 군산대 문서 지식카드 인덱스

## 목적
- `D:\\bindsoft\\2. 교육\\1. 군산대` 내부 문서를 `dxAx/wiki/raw` 안에서 링크형 지식 카드로 관리한다.
- 원본 파일은 외부 경로에 그대로 두고, 이 인덱스와 개별 카드에서 절대경로 링크로 연결한다.
- 옵시디안 태그, 위키 링크, RAG 검색 질의 예시를 같이 제공해 이후 인덱싱과 질의응답에 바로 활용한다.

## 카드 목록
| 카드 | 형식 | 역할 | 원본 파일 | 태그 |
| --- | --- | --- | --- | --- |
{table}
"""


def build_record(source_path: Path) -> DocRecord | None:
    text, method, page_count = extract_text(source_path)
    if not text and source_path.suffix.lower() != ".txt":
        return None
    title = source_path.stem
    role = infer_role(title, source_path.suffix.lower(), text)
    headings = collect_headings(text)
    topics = infer_topics(title, text)
    entities = infer_entities(title, text)
    tags = infer_tags(title, source_path.suffix.lower(), role, topics)
    summary = build_summary(title, role, text)
    queries = build_queries(title, role, headings)
    relative_source = relative_to_bindsoft(source_path)
    aliases = [title, source_path.name, relative_source]
    return DocRecord(
        source_path=source_path,
        relative_source=relative_source,
        title=title,
        ext=source_path.suffix.lower(),
        size_bytes=source_path.stat().st_size,
        page_count=page_count,
        extraction_method=method,
        text=text,
        summary=summary,
        tags=tags,
        aliases=aliases,
        topics=topics,
        entities=entities,
        headings=headings,
        role=role,
        queries=queries,
        related_titles=[],
    )


def assign_related_docs(docs: list[DocRecord]) -> None:
    title_tokens = {doc.title: set(tokenize(doc.title)) for doc in docs}
    for doc in docs:
        scored: list[tuple[int, str]] = []
        for other in docs:
            if other.title == doc.title:
                continue
            score = len(title_tokens[doc.title] & title_tokens[other.title])
            score += len(set(doc.topics[:6]) & set(other.topics[:6]))
            if score > 0:
                scored.append((score, other.title))
        scored.sort(reverse=True)
        doc.related_titles = [title for _, title in scored[:5]]


def write_cards(docs: list[DocRecord]) -> None:
    WIKI_RAW_ROOT.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        output_path = WIKI_RAW_ROOT / f"{safe_name(doc.title)}.md"
        output_path.write_text(render_card(doc), encoding="utf-8-sig")
        doc.output_path = output_path
    (WIKI_RAW_ROOT / "README.md").write_text(render_index(docs), encoding="utf-8-sig")


def main() -> None:
    gunsan_root = find_gunsan_root()
    docs: list[DocRecord] = []
    for source_path in sorted(gunsan_root.rglob("*")):
        if not source_path.is_file() or "_kordoc_extract" in source_path.parts:
            continue
        if source_path.suffix.lower() not in {".txt", ".hwp", ".docx", ".pptx", ".pdf"}:
            continue
        record = build_record(source_path)
        if record:
            docs.append(record)
    assign_related_docs(docs)
    write_cards(docs)
    print(f"Generated {len(docs)} cards in {WIKI_RAW_ROOT}")
    for doc in docs:
        print(doc.output_path)


if __name__ == "__main__":
    main()
