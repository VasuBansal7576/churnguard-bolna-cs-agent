# ChurnGuard - Bolna Voice AI Customer Success Platform

> Catch churn before it happens. Bolna-powered voice AI calls your customers, surfaces risk signals, and updates a real-time dashboard.

## Assignment Fit

ChurnGuard was built for the Bolna Full Stack Engineer assignment. It demonstrates a real enterprise workflow:

`User -> Web app -> Bolna voice agent -> FastAPI webhook/backend logic -> Supabase output -> live dashboard`

## Use Case

SaaS teams often discover onboarding friction too late. A customer signs up, gets stuck during setup, and churn risk appears before the customer success team has enough context to intervene.

ChurnGuard runs automated Day 7 / Day 30 customer success check-ins through a Bolna voice agent. The call is not a generic chatbot conversation: it follows a structured CS workflow, extracts risk signals, and turns the transcript into an operational dashboard for CSM follow-up.

## Outcome Metrics

- Reduce Day 30 churn risk by detecting blockers earlier.
- Shorten time-to-CSM follow-up for at-risk accounts.
- Increase percentage of onboarding blockers captured from real customer conversations.

## What It Does

1. **Upload** a CSV of SaaS customers
2. **Trigger** AI check-in calls via Bolna at Day 7 / Day 30
3. **Aria** (voice agent) asks structured health-check questions
4. **Webhook** receives the call transcript/status from Bolna
5. **Backend logic** maps transcript signals into health_score, risk_label, blocker, sentiment, and recommendation
6. **Dashboard** updates with the operational output for CSM action

```
User → Dashboard → FastAPI → Bolna (voice call) → Webhook → Supabase → Dashboard (live)
```

## Demo

- Loom walkthrough: https://www.loom.com/share/6cea95fc47c541ef9a325a68f07c15ad
- Backend deployment: https://churnguard-api-production.up.railway.app
- Bolna webhook endpoint: `https://churnguard-api-production.up.railway.app/api/webhook/bolna`

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui |
| Backend | FastAPI + SQLAlchemy (async) + Alembic |
| Database | Supabase (PostgreSQL + Realtime) |
| Voice AI | Bolna AI (REST API + webhooks) |
| Deploy | Railway backend, local/optional Vercel frontend |

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Fill in your Supabase and Bolna credentials in .env
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local
# Fill in Supabase URL/key and backend URL
npm install
npm run dev
```

### 3. Bolna Agent Setup

1. Go to [platform.bolna.ai](https://platform.bolna.ai)
2. Create a new agent named "Aria (CS Agent)"
3. **Agent tab**: Paste the system prompt from `agent/prompts/system_prompt.txt`
4. **Analytics tab**:
   - Add the extraction fields from `agent/prompts/extraction_prompt.txt`
   - Set webhook URL to `https://your-backend.railway.app/api/webhook/bolna`
5. Note down the `Agent ID` and `API Key` from the Developers tab

### 4. Test the flow

```bash
# Upload sample customers
curl -X POST http://localhost:8000/api/customers/upload \
  -H "x-api-key: your-admin-key" \
  -F "file=@sample_customers.csv"

# Simulate a webhook (without making a real call)
curl -X POST http://localhost:8000/api/webhook/bolna \
  -H "Content-Type: application/json" \
  -d @agent/test_webhook_payload.json
```

## Environment Variables

### Backend (`backend/.env`)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres
BOLNA_API_KEY=sa-your-bolna-api-key
BOLNA_AGENT_ID=your-agent-uuid
ADMIN_API_KEY=your-admin-api-key
FRONTEND_URL=http://localhost:3000
OPENAI_API_KEY=sk-your-openai-key # optional fallback extraction
```

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_ADMIN_API_KEY=your-admin-api-key
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/customers/` | API Key | List all customers + call results |
| GET | `/api/customers/:id` | API Key | Single customer detail |
| PATCH | `/api/customers/:id` | API Key | Update customer (CSM, status) |
| POST | `/api/customers/upload` | API Key | Upload CSV of customers |
| POST | `/api/campaigns/trigger` | API Key | Trigger Bolna calls |
| POST | `/api/webhook/bolna` | None | Bolna webhook receiver |

## Production Extensions

- WhatsApp fallback if a customer rejects or misses the voice call.
- Retry windows and call scheduling logic.
- CRM task creation for HubSpot/Salesforce when `risk_label = At-Risk`.
- CSM routing by account owner, ARR, region, or SLA.

## Architecture

See [docs/Architecture.md](docs/Architecture.md) for the full system design.

## License

MIT
