# AGENTS.md — Bolna Voice Agent

Read root `AGENTS.md` first. This file governs the `agent/` directory only.

## What This Agent Does

A voice AI customer success agent that conducts structured 3–5 minute check-in calls with SaaS customers at Day 7 and Day 30 post-signup. The agent's job is to surface adoption blockers and churn signals — not to sell or pitch.

---

## Agent Configuration (Bolna Platform)

Set these in platform.bolna.ai when creating the agent:

| Field | Value |
|-------|-------|
| Agent Name | Aria (CS Agent) |
| Voice | Professional, warm female voice |
| Max call duration | 6 minutes |
| Webhook URL | `https://your-backend.railway.app/api/webhook/bolna` |
| Webhook trigger | Push all execution data to webhook (Analytics tab) |
| Language | English |

### Webhook Setup (Analytics Tab)
1. Open your agent → Analytics tab
2. Enter your backend webhook URL in "Push all execution data to webhook"
3. Click "Save agent"
4. IP to whitelist on your server: `13.203.39.153`

---

## Dynamic Variables (Context Variables)

These are injected by the backend when triggering each call via the `user_data` field in the `/call` API.

Bolna uses `{variable_name}` syntax in prompts (single curly braces).

| Variable | Example Value | Used In |
|----------|--------------|---------| 
| `customer_name` | "Sarah" | Greeting, throughout |
| `company` | "Acme Inc." | Personalization |
| `product_name` | "Notion" | Questions |
| `days_since_signup` | "7" | Opening line |
| `csm_name` | "James" | Closing handoff |

### Default Variables (auto-injected by Bolna — no need to pass)
- `agent_id` — UUID of the agent
- `execution_id` — UUID of this specific call execution
- `call_sid` — telephony call SID
- `from_number` — caller number
- `to_number` — recipient number
- `current_date` — e.g. "Wednesday, March 18, 2026"
- `current_time` — e.g. "02:30:15 PM"

---

## System Prompt

```
You are Aria, a customer success assistant at {product_name}. You are calling {customer_name} from {company} for a quick check-in. They signed up {days_since_signup} days ago.

Your goal is to understand how {customer_name} is getting on with {product_name}, identify any blockers, and make sure they're getting value. You are NOT selling anything. You are NOT pitching features. You are listening.

RULES:
- Keep the call under 5 minutes.
- Ask one question at a time. Wait for the full answer before asking the next.
- Sound natural and warm — not scripted. Vary your phrasing.
- If the customer sounds frustrated, acknowledge it before asking the next question.
- If the customer says they want to cancel or are unhappy, do not argue. Acknowledge, tell them {csm_name} will personally reach out today, and end warmly.
- Never make promises about features, refunds, or pricing.
- End every call by thanking them and confirming that {csm_name} is their dedicated CS contact.

SCRIPT FLOW (flexible — adapt to conversation):

1. OPENING
   "Hi, is this {customer_name}? Great — this is Aria calling from {product_name}. I'm on the customer success team, and we make it a point to check in with our customers around day {days_since_signup}. Is now an okay time for a quick 3-minute call?"
   
   If no: "No problem at all — when would be a better time? I'll make a note and we'll follow up." → End call gracefully.

2. ADOPTION CHECK
   "So first — have you had a chance to actually log in and use {product_name} since signing up?"
   
   If no: probe why (too busy, couldn't figure it out, forgot)
   If yes: continue

3. VALUE CHECK
   "What's been the most useful part so far? And have you hit any moments where you weren't sure what to do?"

4. BLOCKER PROBE
   "Is there anything specific that's gotten in the way of using it more? Anything that felt confusing or missing?"
   
   Listen carefully. This is the most important part of the call.

5. OUTCOME INTENT
   "Based on where things are right now — are you feeling good about continuing with {product_name}, or are there any doubts?"
   
   Do not push back on doubts. Just acknowledge and note.

6. CLOSING
   "Thanks so much for your time, {customer_name}. I'm going to pass your feedback directly to {csm_name}, who's your dedicated point of contact. They'll follow up if there's anything that needs attention. Have a great day!"
```

---

## Extraction Prompt (Bolna Platform — Analytics Tab)

Set this in the agent's Analytics tab under "Extraction". Bolna will auto-extract this data and include it in the webhook payload under `extracted_data`.

```
health_score: Rate the customer's health from 0-100. 70-100 means engaged and happy. 40-69 means some friction. 0-39 means at-risk of churning.
risk_label: Yield "Healthy" if health_score >= 70, "Monitor" if 40-69, "At-Risk" if < 40.
key_blocker: Yield the main problem or blocker mentioned, or "none" if no blockers.
sentiment: Yield "positive", "neutral", or "frustrated" based on the customer's tone.
recommendation: Yield "healthy" if no issues, "monitor" if some friction, "escalate" if at-risk.
```

This eliminates the need for a separate LLM call in the backend. The `extracted_data` field in the webhook will contain:
```json
{
  "health_score": "28",
  "risk_label": "At-Risk",
  "key_blocker": "Cannot integrate with their Slack workspace due to permission issues",
  "sentiment": "frustrated",
  "recommendation": "escalate"
}
```

> **Note**: Values from Bolna extraction are strings. Parse `health_score` to int in the backend.

---

## Webhook Payload (what Bolna actually sends to your backend)

The webhook payload mirrors the [Get Execution API](https://www.bolna.ai/docs/api-reference/executions/get_execution) response:

```json
{
  "id": "4c06b4d1-4096-4561-919a-4f94539c8d4a",
  "agent_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
  "batch_id": null,
  "conversation_time": 215,
  "total_cost": 123,
  "status": "completed",
  "error_message": null,
  "answered_by_voice_mail": false,
  "transcript": "Agent: Hi, is this Sarah?...\nCustomer: Yes, hi...",
  "created_at": "2024-01-23T01:14:37Z",
  "updated_at": "2024-01-29T18:31:22Z",
  "telephony_data": {
    "duration": 215,
    "to_number": "+919876543210",
    "from_number": "+1987654007",
    "recording_url": "https://bolna-call-recordings.s3.us-east-1.amazonaws.com/...",
    "hosted_telephony": true,
    "provider_call_id": "CA42fb13614bfcfeccd94cf33befe14s2f",
    "call_type": "outbound",
    "provider": "twilio",
    "hangup_by": "Caller",
    "hangup_reason": "Normal Hangup",
    "ring_duration": 17
  },
  "extracted_data": {
    "health_score": "28",
    "risk_label": "At-Risk",
    "key_blocker": "Cannot integrate with Slack workspace",
    "sentiment": "frustrated",
    "recommendation": "escalate"
  },
  "context_details": {
    "customer_name": "Sarah",
    "company": "Acme Inc.",
    "product_name": "Notion",
    "days_since_signup": "7",
    "csm_name": "James"
  }
}
```

### Key Fields for Backend Processing

| Field | Type | Notes |
|-------|------|-------|
| `id` | string (UUID) | This is the `execution_id` — use this as your unique call identifier |
| `status` | string | See Call Statuses below |
| `transcript` | string | Full conversation text |
| `conversation_time` | int | Duration in seconds |
| `telephony_data.recording_url` | string | S3 URL to call recording |
| `telephony_data.duration` | int | Telephony duration in seconds |
| `extracted_data` | object | Structured data from extraction prompt (health_score, etc.) |
| `context_details` | object | The `user_data` variables you passed when triggering the call |
| `answered_by_voice_mail` | bool | Whether voicemail picked up |
| `error_message` | string/null | Error details if status is error/failed |

### Call Statuses (actual Bolna values)

| Status | Category | Description |
|--------|----------|-------------|
| `scheduled` | Pre-call | Call scheduled for future time |
| `queued` | Pre-call | Call queued for processing |
| `rescheduled` | Pre-call | Rescheduled due to guardrails |
| `initiated` | In-progress | Call initiated with telephony provider |
| `ringing` | In-progress | Phone is ringing |
| `in-progress` | In-progress | Call connected, conversation happening |
| `call-disconnected` | In-progress | Call disconnected mid-conversation |
| `completed` | Terminal ✅ | Call completed successfully |
| `busy` | Terminal ❌ | Recipient was busy |
| `no-answer` | Terminal ❌ | No one answered |
| `canceled` | Terminal ❌ | Call was canceled |
| `failed` | Terminal ❌ | Call failed |
| `stopped` | Terminal ❌ | Call stopped by system |
| `error` | Terminal ❌ | System error |
| `balance-low` | Terminal ❌ | Insufficient Bolna balance |

**Webhook fires at every status transition.** Your backend should check `status` and only process `completed` calls for health scoring. Store other terminal statuses as failed.

---

## Webhook Security

Bolna does **NOT** use signature-based webhook verification. Instead, use IP whitelisting:

```
Webhook requests originate from: 13.203.39.153
```

In your backend middleware, verify the source IP matches. For Railway/cloud deployment, you may also want to check `X-Forwarded-For` headers.

---

## Testing Without Live Calls

Use this curl to simulate a webhook during development. Note the payload matches the **actual Bolna webhook format**:

```bash
curl -X POST http://localhost:8000/api/webhook/bolna \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-execution-001",
    "agent_id": "test-agent-id",
    "batch_id": null,
    "conversation_time": 215,
    "total_cost": 50,
    "status": "completed",
    "error_message": null,
    "answered_by_voice_mail": false,
    "transcript": "Agent: Hi, is this Sarah?\nCustomer: Yes, hi.\nAgent: This is Aria from Notion. I am on the customer success team and we make it a point to check in around day 7. Is now an okay time for a quick call?\nCustomer: Sure, go ahead.\nAgent: Great. So first, have you had a chance to actually log in and use Notion since signing up?\nCustomer: Oh yes, I have been meaning to use it but honestly I tried to set up the Slack integration and it just did not work. I gave up after 30 minutes.\nAgent: I am really sorry to hear that. Is that the main thing that has been blocking you?\nCustomer: Yeah, I mean the core app is fine but without Slack integration it is hard to use daily. I am kind of thinking of just cancelling.\nAgent: I completely understand. I will make sure James reaches out to you today personally to help resolve the Slack issue.\nCustomer: Okay, that would be good.\nAgent: Thank you so much for your time, Sarah. Have a great day.",
    "telephony_data": {
      "duration": 215,
      "to_number": "+919876543210",
      "from_number": "+1987654007",
      "recording_url": "https://example.com/recording.mp3",
      "hosted_telephony": true,
      "call_type": "outbound",
      "provider": "twilio",
      "hangup_by": "Agent",
      "hangup_reason": "Normal Hangup"
    },
    "extracted_data": {
      "health_score": "25",
      "risk_label": "At-Risk",
      "key_blocker": "Slack integration failure - gave up after 30 minutes",
      "sentiment": "frustrated",
      "recommendation": "escalate"
    },
    "context_details": {
      "customer_name": "Sarah",
      "company": "Acme Inc.",
      "product_name": "Notion",
      "days_since_signup": "7",
      "csm_name": "James"
    }
  }'
```

This call should produce: `health_score: 25`, `risk_label: At-Risk`, `key_blocker: Slack integration failure`.