from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


ROOT_DIR = Path(__file__).resolve().parents[2]
NOTES_DIR = ROOT_DIR / "wiki" / "notes"
CLASS_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_dxax_class_summary\.md$")

app = FastAPI(title="DXAX Class Promotion API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _clean_text(value: str) -> str:
    return value.replace("\ufeff", "").strip()


def _split_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "intro"
    sections[current] = []

    for raw_line in markdown.splitlines():
        line = _clean_text(raw_line)
        if line.startswith("## "):
            current = line.removeprefix("## ").strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(raw_line)

    return {key: _clean_text("\n".join(lines)) for key, lines in sections.items()}


def _section_lines(section: str) -> list[str]:
    lines: list[str] = []
    for raw_line in section.splitlines():
        line = _clean_text(raw_line)
        if not line:
            continue
        if line.startswith("-"):
            line = line[1:].strip()
        line = re.sub(r"^\d+\.\s*", "", line).strip()
        line = line.replace("**", "").rstrip("  ")
        if line:
            lines.append(line)
    return lines


def _parse_class_file(path: Path) -> dict[str, Any]:
    match = CLASS_FILE_RE.match(path.name)
    if not match:
        raise ValueError(f"Unsupported class summary file: {path.name}")

    markdown = path.read_text(encoding="utf-8-sig")
    lines = markdown.splitlines()
    title = _clean_text(lines[0]).removeprefix("# ").strip() if lines else path.stem
    sections = _split_sections(markdown)
    summary = sections.get("수업 전체 요약", "")
    lessons = _section_lines(sections.get("무엇을 배웠나", ""))
    messages = _section_lines(sections.get("핵심 메시지", ""))
    details = _section_lines(sections.get("기억해야 할 디테일", ""))
    conclusion = sections.get("결론", "")

    return {
        "date": match.group(1),
        "title": title,
        "summary": summary,
        "lessons": lessons,
        "messages": messages,
        "details": details,
        "conclusion": conclusion,
        "source": str(path),
    }


@lru_cache(maxsize=1)
def _load_classes() -> list[dict[str, Any]]:
    if not NOTES_DIR.exists():
        return []

    classes = [
        _parse_class_file(path)
        for path in NOTES_DIR.glob("*_dxax_class_summary.md")
        if CLASS_FILE_RE.match(path.name)
    ]
    return sorted(classes, key=lambda item: item["date"], reverse=True)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "notesDir": str(NOTES_DIR), "classCount": len(_load_classes())}


@app.get("/api/classes")
def classes() -> list[dict[str, Any]]:
    return [
        {
            "date": item["date"],
            "title": item["title"],
            "summary": item["summary"],
            "messages": item["messages"][:4],
            "lessons": item["lessons"][:6],
        }
        for item in _load_classes()
    ]


@app.get("/api/classes/{date}")
def class_detail(date: str) -> dict[str, Any]:
    for item in _load_classes():
        if item["date"] == date:
            return item
    raise HTTPException(status_code=404, detail="Class summary not found")


@app.get("/api/highlights")
def highlights() -> dict[str, Any]:
    classes = _load_classes()
    latest_messages = [message for item in classes[:8] for message in item["messages"][:2]]
    return {
        "headline": "AI를 답변 도구에서 업무 실행 시스템으로 확장하는 DXAX 클래스",
        "topics": [
            "n8n 기반 워크플로우 자동화",
            "JSON 데이터 구조와 AI 라우터 설계",
            "Notion, Slack, MCP를 활용한 협업형 AX",
            "이미지·영상 생성으로 만드는 실무 홍보 자산",
            "LLM 위키와 메모리 기반 지식 재사용",
        ],
        "latestMessages": latest_messages[:8],
        "classCount": len(classes),
    }
