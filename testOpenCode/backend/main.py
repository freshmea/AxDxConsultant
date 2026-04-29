from __future__ import annotations

import json
import re
import secrets
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
NOTES_DIR = ROOT_DIR / "wiki" / "notes"
DATA_FILE = Path(__file__).resolve().parent / "data_store.json"
CLASS_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_dxax_class_summary\.md$")

DEFAULT_DATA = {
    "users": [
        {
            "username": "admin",
            "password": "admin1234",
            "name": "DXAX Admin",
            "role": "admin",
        },
        {
            "username": "guest",
            "password": "guest1234",
            "name": "DXAX Guest",
            "role": "member",
        },
    ],
    "board_posts": [
        {
            "id": 1,
            "title": "DXAX 클래스 커뮤니티 오픈",
            "content": "매주 수업 노트와 자동화 실습 사례를 이 게시판에서 공유합니다.",
            "author": "DXAX Admin",
            "username": "admin",
            "createdAt": "2026-04-29T13:00:00",
        }
    ],
    "qna_posts": [
        {
            "id": 1,
            "title": "수업 자료는 어디서 확인하나요?",
            "content": "홈 화면 클래스 카드와 위키 노트에서 최신 요약을 확인할 수 있습니다.",
            "author": "DXAX Admin",
            "username": "admin",
            "createdAt": "2026-04-29T13:10:00",
            "answer": "홈 화면 카드와 backend API의 /api/classes 응답이 연결되어 있습니다.",
        }
    ],
}

SESSIONS: dict[str, dict[str, str]] = {}

app = FastAPI(title="DXAX Class Promotion API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginPayload(BaseModel):
    username: str = Field(min_length=2, max_length=30)
    password: str = Field(min_length=4, max_length=60)


class WritePayload(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    content: str = Field(min_length=5, max_length=5000)


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


def _ensure_data_file() -> None:
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT_DATA, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_data() -> dict[str, Any]:
    _ensure_data_file()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _save_data(data: dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_class_file(path: Path) -> dict[str, Any]:
    match = CLASS_FILE_RE.match(path.name)
    if not match:
        raise ValueError(f"Unsupported class summary file: {path.name}")

    markdown = path.read_text(encoding="utf-8-sig")
    lines = markdown.splitlines()
    title = _clean_text(lines[0]).removeprefix("# ").strip() if lines else path.stem
    sections = _split_sections(markdown)
    summary = sections.get("수업 전체 요약", "") or sections.get("?섏뾽 ?꾩껜 ?붿빟", "")
    lessons = _section_lines(sections.get("무엇을 배웠나", "") or sections.get("臾댁뾿??諛곗썱??", ""))
    messages = _section_lines(sections.get("전달 메시지", "") or sections.get("?듭떖 硫붿떆吏", ""))
    details = _section_lines(sections.get("기억해야 할 디테일", "") or sections.get("湲곗뼲?댁빞 ???뷀뀒??", ""))
    conclusion = sections.get("결론", "") or sections.get("寃곕줎", "")
    cover_name = f"{match.group(1)}_dxax_class_summary_cover.png"
    cover_path = NOTES_DIR / cover_name

    return {
        "date": match.group(1),
        "title": title,
        "summary": summary,
        "lessons": lessons,
        "messages": messages,
        "details": details,
        "conclusion": conclusion,
        "sections": sections,
        "coverImage": f"/api/covers/{quote(cover_name)}" if cover_path.exists() else None,
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


def _public_user(user: dict[str, Any]) -> dict[str, str]:
    return {"username": user["username"], "name": user["name"], "role": user["role"]}


def _current_user(authorization: Optional[str]) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.removeprefix("Bearer ").strip()
    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    data = _load_data()
    for user in data["users"]:
        if user["username"] == session["username"]:
            return user

    raise HTTPException(status_code=401, detail="User not found")


def _next_id(items: list[dict[str, Any]]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def _make_post(payload: WritePayload, user: dict[str, Any], post_id: int) -> dict[str, Any]:
    return {
        "id": post_id,
        "title": payload.title.strip(),
        "content": payload.content.strip(),
        "author": user["name"],
        "username": user["username"],
        "createdAt": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    data = _load_data()
    return {
        "status": "ok",
        "notesDir": str(NOTES_DIR),
        "classCount": len(_load_classes()),
        "boardCount": len(data["board_posts"]),
        "qnaCount": len(data["qna_posts"]),
    }


@app.post("/api/login")
def login(payload: LoginPayload) -> dict[str, Any]:
    data = _load_data()
    user = next(
        (
            item
            for item in data["users"]
            if item["username"] == payload.username and item["password"] == payload.password
        ),
        None,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(24)
    SESSIONS[token] = {"username": user["username"]}
    return {"token": token, "user": _public_user(user)}


@app.get("/api/me")
def me(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = _current_user(authorization)
    return {"user": _public_user(user)}


@app.get("/api/classes")
def classes() -> list[dict[str, Any]]:
    return [
        {
            "date": item["date"],
            "title": item["title"],
            "summary": item["summary"],
            "messages": item["messages"][:4],
            "lessons": item["lessons"][:6],
            "allMessages": item["messages"],
            "allLessons": item["lessons"],
            "details": item["details"],
            "conclusion": item["conclusion"],
            "sections": item["sections"],
            "coverImage": item["coverImage"],
        }
        for item in _load_classes()
    ]


@app.get("/api/classes/{date}")
def class_detail(date: str) -> dict[str, Any]:
    for item in _load_classes():
        if item["date"] == date:
            return item
    raise HTTPException(status_code=404, detail="Class summary not found")


@app.get("/api/covers/{filename}")
def cover_image(filename: str) -> FileResponse:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}_dxax_class_summary_cover\.png", filename):
        raise HTTPException(status_code=404, detail="Cover image not found")

    path = NOTES_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Cover image not found")

    return FileResponse(path, media_type="image/png")


@app.get("/api/highlights")
def highlights() -> dict[str, Any]:
    classes = _load_classes()
    latest_messages = [message for item in classes[:8] for message in item["messages"][:2]]
    return {
        "headline": "DXAX는 AI 도구를 연결해 실제 업무 자동화와 운영 시스템으로 확장하는 방법을 다룹니다.",
        "topics": [
            "n8n 기반 워크플로 자동화",
            "JSON 데이터 구조와 AI 연동 설계",
            "Notion, Slack, MCP를 활용한 작업 AX",
            "이미지와 영상 생성으로 만드는 실무 홍보 자산",
            "LLM 위키와 메모리 기반 지식 운영",
        ],
        "latestMessages": latest_messages[:8],
        "classCount": len(classes),
    }


@app.get("/api/board/posts")
def board_posts() -> list[dict[str, Any]]:
    data = _load_data()
    return sorted(data["board_posts"], key=lambda item: item["createdAt"], reverse=True)


@app.post("/api/board/posts")
def create_board_post(payload: WritePayload, authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = _current_user(authorization)
    data = _load_data()
    post = _make_post(payload, user, _next_id(data["board_posts"]))
    data["board_posts"].append(post)
    _save_data(data)
    return post


@app.get("/api/qna/posts")
def qna_posts() -> list[dict[str, Any]]:
    data = _load_data()
    return sorted(data["qna_posts"], key=lambda item: item["createdAt"], reverse=True)


@app.post("/api/qna/posts")
def create_qna_post(payload: WritePayload, authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = _current_user(authorization)
    data = _load_data()
    post = _make_post(payload, user, _next_id(data["qna_posts"]))
    post["answer"] = ""
    data["qna_posts"].append(post)
    _save_data(data)
    return post
