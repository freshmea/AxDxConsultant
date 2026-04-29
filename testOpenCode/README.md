# DXAX Class Promotion Site

Next.js와 Tailwind CSS로 만든 수업 홍보 페이지와 FastAPI 기반 동적 수업 노트 API입니다.

## 구조

- `backend/`: FastAPI API 서버
- `frontend/`: Next.js App Router 프론트엔드
- `../wiki/notes/`: 수업 요약 Markdown 원본, 읽기 전용으로 참조

## Backend 실행

```powershell
cd C:\Users\Administrator\dxAx\testOpenCode\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API 확인:

- `http://localhost:8000/api/health`
- `http://localhost:8000/api/classes`
- `http://localhost:8000/api/highlights`

## Frontend 실행

```powershell
cd C:\Users\Administrator\dxAx\testOpenCode\frontend
npm install
npm run dev
```

페이지 확인:

- `http://localhost:3000`

## 환경 변수

FastAPI 주소를 바꾸려면 `frontend/.env.local`에 다음 값을 지정합니다.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 동작 방식

FastAPI는 `C:\Users\Administrator\dxAx\wiki\notes` 안의 `*_dxax_class_summary.md` 파일을 읽어 날짜, 제목, 수업 요약, 핵심 메시지, 기억해야 할 디테일을 JSON으로 제공합니다. Next.js 페이지는 이 API를 호출해 최신 수업 내용을 홍보 페이지에 동적으로 표시합니다.
