# PRD — ChurnGuard

## Problem Statement

Early-stage and growth-stage SaaS companies churn 5–7% of their customer base monthly. The primary reason is not product quality — it is silent failure during onboarding. New customers hit adoption blockers in the first 30 days, get no outreach, and cancel. By the time the CS team notices, the decision has already been made.

Manual check-in calls don't scale. A CS team of 3 cannot meaningfully call 500 new customers per month. The result: high-value accounts go untouched, churn is discovered reactively, and retention suffers.

**Target customer**: SaaS companies with 100–5,000 customers, 1–5 CS staff, MRR between $50k–$2M.

---

## Outcome Metric

**Primary**: Promise-to-retain rate — % of flagged at-risk customers who remain active 30 days post-CSM intervention.

**Secondary**:
- Call completion rate (target: >65%)
- Health score distribution across customer base
- Median time from call completion → CSM action taken
- % of Day 7 at-risk customers who recover by Day 30

---

## User Roles

| Role | Description |
|------|-------------|
| Admin | Uploads customer lists, triggers campaigns, views full dashboard |
| CSM | Views their assigned at-risk accounts, sees call transcripts, marks resolved |

(For this demo: single admin view. No multi-user auth.)

---

## Core Workflow

### Step 1 — Customer Ingestion
Admin uploads a CSV with columns: `name`, `email`, `phone`, `company`, `product_name`, `days_since_signup`, `csm_name`.

System validates CSV, creates customer records in DB with status `pending`.

### Step 2 — Call Triggering
Admin clicks "Start Campaign". Backend calls Bolna REST API for each customer, passing dynamic variables (name, company, product, csm_name, days_since_signup).

Customer status updates to `call_scheduled`.

### Step 3 — Voice Call (Bolna Agent)
Bolna agent calls the customer. The call runs the structured CS health-check script (see `agent/AGENTS.md`). Duration: 3–5 minutes.

### Step 4 — Webhook Processing
On call end, Bolna fires `POST /api/webhook/bolna` with:
- Call transcript (full text)
- Call duration, completion status
- Dynamic variable values used

Backend processes webhook:
1. Parses transcript
2. Extracts health score (0–100), risk label, key blockers, sentiment, recommended action
3. Stores structured result in Supabase
4. Triggers Supabase Realtime event → dashboard updates live

### Step 5 — Dashboard
Real-time table showing all customers with:
- Call status (pending / scheduled / completed / failed)
- Health score (color-coded: green ≥70, yellow 40–69, red <40)
- Risk label: `Healthy` / `Monitor` / `At-Risk`
- Key blocker (one-line summary)
- Transcript (expandable)
- Action button: "Assign to CSM" / "Mark Resolved"

### Step 6 — CSM Routing
At-risk accounts (health score <40) are auto-flagged. Admin can assign to CSM with one click. (For demo: marks in DB, no email integration needed.)

---

## Features In Scope (Demo)

- CSV upload + customer creation
- Bolna call triggering via REST API
- Webhook receiver + transcript parsing
- Health score extraction
- Real-time dashboard (Supabase Realtime)
- Transcript viewer
- Risk flagging + CSM assignment

## Out of Scope (Demo)

- Email/Slack notifications to CSMs
- Auth/login beyond API key
- Day 7 vs Day 30 auto-scheduling (manual trigger only)
- Multi-tenant (single workspace)
- Call recording playback

---

## Data Model (High Level)

**customers**
- id, name, email, phone, company, product_name, days_since_signup, csm_name
- status: `pending | scheduled | in_call | completed | failed`
- created_at

**call_results**
- id, customer_id, bolna_call_id
- transcript (text), duration_seconds, completed (bool)
- health_score (int 0–100), risk_label, key_blocker, sentiment, recommendation
- raw_webhook_payload (jsonb)
- created_at

---

## Success Criteria for Demo

The evaluator should be able to:
1. Upload a CSV of 3 test customers
2. Trigger calls and see status update to `scheduled`
3. Simulate a webhook POST (or take a live call) and see the dashboard update in real time
4. See a health score, risk label, and transcript for at least one completed call
5. Flag an at-risk customer and assign to CSM