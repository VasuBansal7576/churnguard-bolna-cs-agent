# Architecture — ChurnGuard

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin Browser                            │
│                    (Next.js Dashboard)                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │ HTTP (REST)              ▲ Supabase Realtime
                   ▼                          │ (live updates)
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                                                                 │
│  POST /api/customers/upload   → parse CSV, create records       │
│  POST /api/campaigns/trigger  → call Bolna API for each         │
│  POST /api/webhook/bolna      → receive call results            │
│  GET  /api/customers          → return all with status          │
│  GET  /api/customers/:id      → single customer + call result   │
│  PATCH /api/customers/:id     → assign CSM, mark resolved       │
└──────┬────────────────────────────────┬───────────────────────┘
       │ Bolna REST API                 │ SQLAlchemy (async)
       ▼                                ▼
┌──────────────┐              ┌─────────────────────┐
│  Bolna AI    │              │  Supabase            │
│  Platform    │              │  (PostgreSQL)        │
│              │              │                      │
│  - Hosts the │              │  - customers table   │
│    voice AI  │              │  - call_results table│
│    agent     │              │                      │
│  - Manages   │              │  Realtime enabled on │
│    calls     │              │  call_results table  │
│  - Fires     │              └─────────────────────┘
│    webhooks  │
│  - Extracts  │
│    health    │
│    data      │
└──────┬───────┘
       │ Webhook (POST) at every status transition
       ▼
┌─────────────────────────────────────────────────────────────────┐
│              POST /api/webhook/bolna                            │
│                                                                 │
│  1. Verify source IP = 13.203.39.153 (Bolna webhook IP)        │
│  2. Check status — only process terminal statuses               │
│  3. If "completed": parse extracted_data from Bolna             │
│     → Fallback: call OpenAI for health extraction               │
│  4. Write call_result row to Supabase                           │
│  5. Update customer status → 'completed' or 'failed'           │
│  6. Supabase Realtime fires → dashboard updates live            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Triggering a Call

```
Admin clicks "Start Campaign"
  → POST /api/campaigns/trigger { customer_ids: [...] }
  → Backend loops customers
  → For each: POST https://api.bolna.ai/call
      headers: { Authorization: "Bearer <BOLNA_API_KEY>" }
      body: {
        agent_id: BOLNA_AGENT_ID,
        recipient_phone_number: customer.phone,   // E.164: +919876543210
        user_data: {                               // NOT "dynamic_variables"
          customer_name: customer.name,
          company: customer.company,
          product_name: customer.product_name,
          days_since_signup: str(customer.days_since_signup),
          csm_name: customer.csm_name
        }
      }
  → Bolna returns: { "message": "done", "status": "queued", "execution_id": "uuid" }
  → Customer status updated to 'scheduled', bolna_execution_id stored
```

---

## Data Flow: Webhook Processing

```
Bolna call progresses through statuses
  → Webhook fires at EVERY status transition (scheduled → queued → initiated → 
     ringing → in-progress → completed)
  → POST /api/webhook/bolna
      body: {
        id: "execution-uuid",        // This is the execution_id
        agent_id: "agent-uuid",
        status: "completed",         // or any other status
        conversation_time: 245,      // seconds
        transcript: "Agent: Hi Sarah...\nCustomer: ...",
        telephony_data: {
          duration: 245,
          recording_url: "https://bolna-call-recordings.s3...",
          to_number: "+919876543210",
          from_number: "+1987654007",
          hangup_by: "Agent",
          hangup_reason: "Normal Hangup"
        },
        extracted_data: {            // From Bolna's native extraction
          health_score: "34",        // String — parse to int
          risk_label: "At-Risk",
          key_blocker: "Cannot integrate with Slack",
          sentiment: "frustrated",
          recommendation: "escalate"
        },
        context_details: {           // user_data passed during trigger
          customer_name: "Sarah",
          company: "Acme Inc.",
          ...
        },
        answered_by_voice_mail: false,
        error_message: null
      }

Backend:
  1. Verify source IP = 13.203.39.153
  2. Find customer by bolna_execution_id
  3. Map Bolna status to our status (see BOLNA_STATUS_MAP)
  4. If status == "completed":
     a. Parse extracted_data from Bolna (primary)
     b. If extracted_data empty → call OpenAI with transcript (fallback)
     c. INSERT into call_results (UNIQUE on bolna_execution_id)
  5. UPDATE customers SET status = mapped_status
  6. Supabase Realtime broadcasts change
  7. Dashboard row updates without page refresh
```

---

## Health Score Extraction

### Primary: Bolna Native Extraction (Zero Cost, Zero Latency)

Set an `extraction_prompt` in the Bolna agent's Analytics tab. Bolna extracts structured data and includes it in the webhook payload under `extracted_data`. Values are strings — parse `health_score` to int.

### Fallback: LLM Extraction (if Bolna extraction is empty)

Call OpenAI GPT-4o-mini with the transcript and a structured extraction prompt. Returns JSON.

Score breakdown:
- Feature adoption signals: 0–40 pts
- Sentiment / frustration level: 0–30 pts
- Stated intent (cancel / continue): 0–30 pts

Risk label mapping:
- 70–100 → `Healthy`
- 40–69 → `Monitor`
- 0–39 → `At-Risk`

---

## Supabase Realtime Setup

1. Enable Realtime on `call_results` table in Supabase dashboard
2. Enable Row Level Security (RLS) on both tables — Realtime requires RLS to be enabled
3. Create a permissive RLS policy for the demo:
```sql
-- Allow all reads for anon key (demo only)
CREATE POLICY "Allow all reads" ON call_results FOR SELECT USING (true);
CREATE POLICY "Allow all reads" ON customers FOR SELECT USING (true);
```

Frontend subscribes:
```typescript
supabase
  .channel('call_results')
  .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'call_results' }, 
    (payload) => updateDashboard(payload.new))
  .subscribe()
```

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Health extraction primary | Bolna native extraction | Zero cost, zero latency, built into webhook |
| Health extraction fallback | GPT-4o-mini | Cheap, fast, reliable JSON output |
| Webhook processing | Synchronous | Low volume, no queue needed |
| Webhook security | IP whitelist (13.203.39.153) | Bolna's documented approach |
| Realtime mechanism | Supabase Realtime | No extra infra, works with existing DB |
| No auth | API key header | Reduces complexity for real build |
| ORM | SQLAlchemy async | Consistent with FastAPI async patterns |
| Idempotency | UNIQUE on bolna_execution_id | Prevents duplicate call_results from webhook retries |
| Phone format | E.164 | Required by Bolna API |

---

## Backend File Structure

```
backend/
├── main.py                    # FastAPI app init, CORS, router mounting
├── database.py                # Supabase + SQLAlchemy async engine setup
├── models/
│   ├── customer.py            # Customer ORM model
│   └── call_result.py         # CallResult ORM model
├── schemas/
│   ├── customer.py            # Pydantic request/response schemas
│   └── call_result.py
├── routers/
│   ├── customers.py           # /api/customers routes
│   ├── campaigns.py           # /api/campaigns/trigger route
│   └── webhook.py             # /api/webhook/bolna route
├── services/
│   ├── bolna.py               # Bolna API client
│   └── health_score.py        # Extraction parsing + LLM fallback
├── alembic/                   # DB migrations
└── requirements.txt
```

## Frontend File Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx               # Dashboard (main view)
│   └── api/                   # Next.js route handlers if needed
├── components/
│   ├── CustomerTable.tsx       # Real-time customer list
│   ├── UploadCSV.tsx           # Drag-drop CSV uploader
│   ├── CallStatusBadge.tsx     # Status indicator component
│   ├── HealthScoreBadge.tsx    # Color-coded score display
│   └── TranscriptModal.tsx     # Expandable transcript viewer
├── lib/
│   ├── supabase.ts             # Supabase client (singleton)
│   └── api.ts                  # Backend API calls
└── types/
    └── index.ts                # Shared TypeScript types
```