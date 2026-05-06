# AGENTS.md — Backend (FastAPI)

Read root `AGENTS.md` first. This file governs the `backend/` directory only.

## Setup Commands
```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

## Run Tests
```bash
pytest tests/ -v
```

Fix all failing tests before marking a task done.

---

## FastAPI Patterns

### App structure in main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import customers, campaigns, webhook

app = FastAPI(title="ChurnGuard API")

app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_URL")],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(customers.router, prefix="/api/customers")
app.include_router(campaigns.router, prefix="/api/campaigns")
app.include_router(webhook.router, prefix="/api/webhook")
```

### All routes are async
```python
@router.get("/", response_model=list[CustomerResponse])
async def get_customers(db: AsyncSession = Depends(get_db)):
    ...
```

### API key guard (apply to all non-webhook routes)
```python
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### Standard response shape
Always return: `{ "success": True, "data": ..., "error": None }`  
On error: `{ "success": False, "data": None, "error": "message" }`

---

## Database Patterns

### SQLAlchemy async session (database.py)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(os.getenv("SUPABASE_DB_URL"))
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Never write raw SQL. Always use ORM:
```python
# Correct
result = await db.execute(select(Customer).where(Customer.id == customer_id))
customer = result.scalar_one_or_none()

# Never
await db.execute(text("SELECT * FROM customers WHERE id = :id"), {"id": customer_id})
```

### Alembic migrations
Every schema change requires a new migration:
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Models

### Customer model (models/customer.py)
```python
class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # E.164 format: +919876543210
    company = Column(String)
    product_name = Column(String)
    days_since_signup = Column(Integer)
    csm_name = Column(String)
    status = Column(String, default="pending")  # See status mapping below
    bolna_execution_id = Column(String, nullable=True, unique=True)  # Bolna execution_id
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### CallResult model (models/call_result.py)
```python
class CallResult(Base):
    __tablename__ = "call_results"
    id = Column(UUID, primary_key=True, default=uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    bolna_execution_id = Column(String, nullable=False, unique=True)  # Prevents duplicate webhook processing
    transcript = Column(Text)
    duration_seconds = Column(Integer)
    completed = Column(Boolean, default=False)
    health_score = Column(Integer)  # 0-100 (parsed from Bolna extracted_data string)
    risk_label = Column(String)     # Healthy | Monitor | At-Risk
    key_blocker = Column(String)
    sentiment = Column(String)      # positive | neutral | frustrated
    recommendation = Column(String) # escalate | monitor | healthy
    recording_url = Column(String)  # From telephony_data.recording_url
    answered_by_voicemail = Column(Boolean, default=False)
    raw_webhook_payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Status Mapping (Bolna status → ChurnGuard status)

```python
# Bolna sends many granular statuses. Map them to our simpler model:
BOLNA_STATUS_MAP = {
    # Pre-call
    "scheduled": "scheduled",
    "queued": "scheduled",
    "rescheduled": "scheduled",
    # In-progress
    "initiated": "in_call",
    "ringing": "in_call",
    "in-progress": "in_call",
    "call-disconnected": "failed",
    # Terminal — success
    "completed": "completed",
    # Terminal — failure
    "busy": "failed",
    "no-answer": "failed",
    "canceled": "failed",
    "failed": "failed",
    "stopped": "failed",
    "error": "failed",
    "balance-low": "failed",
}
```

---

## Bolna Service (services/bolna.py)

```python
import httpx

BOLNA_BASE = "https://api.bolna.ai"

async def trigger_call(customer: Customer) -> str:
    """Returns bolna execution_id"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BOLNA_BASE}/call",
            headers={
                "Authorization": f"Bearer {os.getenv('BOLNA_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "agent_id": os.getenv("BOLNA_AGENT_ID"),
                "recipient_phone_number": customer.phone,  # Must be E.164: +919876543210
                "user_data": {
                    "customer_name": customer.name,
                    "company": customer.company or "",
                    "product_name": customer.product_name or "",
                    "days_since_signup": str(customer.days_since_signup or 0),
                    "csm_name": customer.csm_name or ""
                }
            }
        )
        resp.raise_for_status()
        data = resp.json()
        # Response: { "message": "done", "status": "queued", "execution_id": "uuid" }
        return data["execution_id"]
```

---

## Health Score Extraction (services/health_score.py)

### Primary: Use Bolna's native extraction (no LLM call needed)

Bolna's `extracted_data` field in the webhook provides health signals directly. Parse them:

```python
def parse_bolna_extraction(extracted_data: dict | None) -> dict:
    """Parse Bolna's extracted_data into our health score format.
    Values from Bolna extraction are strings — parse health_score to int.
    """
    if not extracted_data:
        return {
            "health_score": None,
            "risk_label": None,
            "key_blocker": None,
            "sentiment": None,
            "recommendation": None
        }
    
    try:
        score = int(extracted_data.get("health_score", 0))
    except (ValueError, TypeError):
        score = None
    
    return {
        "health_score": score,
        "risk_label": extracted_data.get("risk_label"),
        "key_blocker": extracted_data.get("key_blocker"),
        "sentiment": extracted_data.get("sentiment"),
        "recommendation": extracted_data.get("recommendation")
    }
```

### Fallback: LLM-based extraction (if Bolna extraction is empty)

If `extracted_data` is empty or missing, fall back to calling OpenAI with the transcript:

```python
EXTRACTION_PROMPT = """
You are analyzing a customer success call transcript.
Extract the following as JSON only — no other text:

{
  "health_score": <integer 0-100>,
  "risk_label": "<Healthy|Monitor|At-Risk>",
  "key_blocker": "<one sentence or null>",
  "sentiment": "<positive|neutral|frustrated>",
  "recommendation": "<escalate|monitor|healthy>"
}

Scoring:
- 70-100: Customer is adopting the product, no major blockers → Healthy
- 40-69: Some friction but not churning → Monitor
- 0-39: Blockers, frustration, or stated intent to cancel → At-Risk

Transcript:
{transcript}
"""
```

---

## Webhook Route (routers/webhook.py)

```
POST /api/webhook/bolna
- No API key required (Bolna calls this)
- Optionally verify source IP: 13.203.39.153 (Bolna's webhook IP)
- Webhook fires at EVERY status transition — filter for terminal statuses
- Find customer by bolna_execution_id
- If status == "completed": extract health data, write CallResult
- If status is other terminal: update customer status to "failed"  
- Use UNIQUE constraint on bolna_execution_id to prevent duplicate processing
- Return 200 immediately (Bolna retries on non-200)
```

### Webhook Handler Logic

```python
@router.post("/bolna")
async def handle_bolna_webhook(payload: dict, db: AsyncSession = Depends(get_db)):
    execution_id = payload.get("id")  # NOT "call_id" — Bolna uses "id"
    bolna_status = payload.get("status")
    
    # Map Bolna status to our status
    our_status = BOLNA_STATUS_MAP.get(bolna_status, "failed")
    
    # Find customer by execution_id
    customer = await find_customer_by_execution_id(db, execution_id)
    if not customer:
        return {"success": True}  # Still return 200 to avoid retries
    
    # Update customer status
    customer.status = our_status
    
    # Only create CallResult for terminal statuses
    if bolna_status == "completed":
        # Try Bolna extraction first, fall back to LLM
        extracted = payload.get("extracted_data", {})
        health_data = parse_bolna_extraction(extracted)
        
        if health_data["health_score"] is None and payload.get("transcript"):
            health_data = await llm_extract_health(payload["transcript"])
        
        call_result = CallResult(
            customer_id=customer.id,
            bolna_execution_id=execution_id,
            transcript=payload.get("transcript"),
            duration_seconds=payload.get("conversation_time"),
            completed=True,
            recording_url=payload.get("telephony_data", {}).get("recording_url"),
            answered_by_voicemail=payload.get("answered_by_voice_mail", False),
            raw_webhook_payload=payload,
            **health_data
        )
        db.add(call_result)
    
    elif our_status == "failed":
        call_result = CallResult(
            customer_id=customer.id,
            bolna_execution_id=execution_id,
            completed=False,
            raw_webhook_payload=payload
        )
        db.add(call_result)
    
    await db.commit()
    return {"success": True}
```

Always return `200 OK` within 10 seconds. If extraction is slow, write the raw transcript first and process async.

---

## CSV Upload

Accept multipart file upload. Parse with Python `csv.DictReader`.  
Required columns: `name`, `email`, `phone`  
Optional: `company`, `product_name`, `days_since_signup`, `csm_name`  
Skip rows with missing required fields, return count of skipped.

**Phone number validation**: Must be E.164 format (e.g., `+919876543210`, `+10123456789`). Reject rows without valid E.164 phone numbers.

---

## Environment Variables

```
SUPABASE_URL=           # Supabase project URL (for frontend/Realtime)
SUPABASE_ANON_KEY=      # Supabase anonymous key (for frontend/Realtime)
SUPABASE_DB_URL=        # Direct Postgres connection string (for SQLAlchemy)
BOLNA_API_KEY=          # Bearer token from Bolna dashboard → Developers tab
BOLNA_AGENT_ID=         # UUID of your Bolna agent
ADMIN_API_KEY=          # Your own API key for backend auth
FRONTEND_URL=           # For CORS: http://localhost:3000 in dev
OPENAI_API_KEY=         # For fallback LLM extraction (if Bolna extraction is empty)
```
