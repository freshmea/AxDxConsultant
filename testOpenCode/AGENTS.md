# testOpenCode Agent Guide

This project is a small full-stack DXAX class promotion site.

## Project Structure

- `backend/` contains the FastAPI API server.
- `backend/main.py` parses class summary Markdown files from `C:\Users\Administrator\dxAx\wiki\notes` and exposes JSON APIs.
- `backend/requirements.txt` pins Python runtime dependencies.
- `frontend/` contains the Next.js App Router frontend.
- `frontend/src/app/page.tsx` renders the landing page and fetches data from FastAPI.
- `frontend/src/app/globals.css` contains global Tailwind setup and base styles.
- `frontend/tailwind.config.ts` defines Tailwind content paths and theme extensions.
- `README.md` documents local execution.
- `src/` is currently unused.

## Data Source Rules

- Treat `C:\Users\Administrator\dxAx\wiki\notes` as a read-only source for this project.
- Do not edit, move, or delete files under `wiki/notes` while working on this app.
- Backend parsing should target only `*_dxax_class_summary.md` unless the user explicitly asks to support more note types.
- Korean Markdown should be read with UTF-8 or UTF-8 with BOM handling. In Python, prefer `encoding="utf-8-sig"` for these notes.
- Do not rely on PowerShell console rendering to judge Korean text correctness if mojibake appears.

## Backend Rules

- Keep the backend minimal and synchronous unless there is a clear need for async I/O.
- API routes currently expected by the frontend are:
  - `GET /api/health`
  - `GET /api/classes`
  - `GET /api/classes/{date}`
  - `GET /api/highlights`
  - `GET /api/covers/{filename}`
- If changing response shapes, update `frontend/src/app/page.tsx` TypeScript types at the same time.
- Preserve CORS access for `http://localhost:3000` and `http://127.0.0.1:3000` during local development.
- The class list is cached with `lru_cache`; clear or adjust caching if live file refresh becomes a requirement.

## Frontend Rules

- This app uses Next.js, not Vite.
- Use the App Router under `frontend/src/app`.
- Keep the landing page server-rendered unless client-side interactivity is required.
- `NEXT_PUBLIC_API_BASE_URL` controls the FastAPI base URL and defaults to `http://localhost:8000`.
- Preserve the current bright, image-forward promotional visual language unless the user asks for a redesign.
- Keep Tailwind utility styling local and direct for small components; avoid adding a component library unless needed.
- Maintain fallback content so the page still builds and renders when the FastAPI server is offline.

## Generated And Dependency Folders

- Do not manually edit `frontend/node_modules/`, `frontend/.next/`, `backend/__pycache__/`, or lock/cache output.
- `frontend/package-lock.json` should be updated only through npm commands.
- Keep Python virtual environments out of versioned source; use `backend/.venv/` only as a local environment if needed.

## Common Commands

Backend install and run:

```powershell
cd C:\Users\Administrator\dxAx\testOpenCode\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend quick validation:

```powershell
cd C:\Users\Administrator\dxAx\testOpenCode\backend
python -m py_compile main.py
python -c "from main import classes, health; print(health()); print(len(classes()))"
```

Frontend install and run:

```powershell
cd C:\Users\Administrator\dxAx\testOpenCode\frontend
npm install
npm run dev
```

Frontend production validation:

```powershell
cd C:\Users\Administrator\dxAx\testOpenCode\frontend
npm run build
```

## Verification Expectations

- For backend changes, run `python -m py_compile main.py` and the quick data loading validation when feasible.
- For frontend changes, run `npm run build` when feasible.
- If dependency installation or validation is skipped, state the reason clearly in the final response.

## Editing Guidelines

- Prefer small, direct changes over broad refactors.
- Keep backend parser behavior predictable and easy to inspect.
- Keep frontend data types near the fetch/rendering code unless they become reused across files.
- Avoid introducing new frameworks, state managers, or build tools without a concrete requirement.
- Preserve Korean user-facing copy quality; avoid machine-translated awkward phrasing in landing page sections.
