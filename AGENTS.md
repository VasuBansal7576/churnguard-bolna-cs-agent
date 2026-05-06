# AGENTS.md — ChurnGuard (Bolna CS Check-in Agent)

## What This Project Is
A Voice AI customer success platform. A Bolna agent calls SaaS customers at Day 7 and Day 30 post-signup, asks structured health-check questions, extracts risk signals, and routes at-risk accounts to CSMs via a real-time dashboard.

## Stack
- **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python 3.12) + SQLAlchemy (async) + Alembic
- **Database**: Supabase (PostgreSQL + Realtime)
- **Voice Agent**: Bolna AI (REST API + webhooks)
- **Deploy**: Vercel (frontend) + Railway (backend)

## Repo Structure
```
bolna-cs-agent/
├── AGENTS.md
├── README.md
├── docs/
│   ├── PRD.md
│   └── ARCHITECTURE.md
├── frontend/          # Next.js app
│   ├── AGENTS.md
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/           # FastAPI app
│   ├── AGENTS.md
│   ├── main.py
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   └── services/
└── agent/             # Bolna agent config + prompts
    ├── AGENTS.md
    └── prompts/
```

## Shared Conventions
- All secrets in `.env` files. Never hardcode API keys, tokens, or passwords.
- All dates/times stored as UTC ISO 8601 strings.
- Supabase client initialized once and reused — never re-initialized per request.
- All API responses follow: `{ success: bool, data: any, error: str | null }`.
- Use `snake_case` for Python, `camelCase` for TypeScript.
- Never generate mock data that gets committed — use `.env.example` instead.

## Never Do
- Do not use `--full-auto` permission profile.
- Do not install packages not in the stack above without noting it in a comment.
- Do not create any file in the `agent/` folder without reading `agent/AGENTS.md` first.
- Do not write raw SQL — use SQLAlchemy ORM.
- Do not add auth/login UI — a hardcoded `ADMIN_API_KEY` env var gates the backend.

## Running the Project
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install
npm run dev

# DB migrations
cd backend && alembic upgrade head
```

## Environment Variables (see .env.example)
```
SUPABASE_URL=              # Supabase project URL (for frontend/Realtime)
SUPABASE_ANON_KEY=         # Supabase anonymous key (for frontend/Realtime)
SUPABASE_DB_URL=           # Direct Postgres connection string (for SQLAlchemy)
BOLNA_API_KEY=             # Bearer token from Bolna dashboard → Developers tab
BOLNA_AGENT_ID=            # UUID of your Bolna agent
ADMIN_API_KEY=             # Your own API key for backend auth
FRONTEND_URL=              # For CORS: http://localhost:3000 in dev
OPENAI_API_KEY=            # For fallback LLM extraction
```