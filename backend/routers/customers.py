"""Customer routes — CRUD + CSV upload."""

import csv
import io
import re
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.customer import Customer
from models.call_result import CallResult
from schemas import CustomerResponse, CallResultResponse, CustomerUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

# E.164 phone validation: + followed by 7-15 digits
E164_PATTERN = re.compile(r"^\+[1-9]\d{6,14}$")


def _verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    """Verify admin API key from header."""
    import os
    if x_api_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _customer_to_response(customer: Customer, call_result: CallResult = None) -> dict:
    """Convert ORM customer to response dict."""
    result = {
        "id": str(customer.id),
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "company": customer.company,
        "product_name": customer.product_name,
        "days_since_signup": customer.days_since_signup,
        "csm_name": customer.csm_name,
        "status": customer.status,
        "bolna_execution_id": customer.bolna_execution_id,
        "created_at": customer.created_at,
        "call_result": None
    }
    if call_result:
        result["call_result"] = {
            "id": str(call_result.id),
            "customer_id": str(call_result.customer_id),
            "bolna_execution_id": call_result.bolna_execution_id,
            "transcript": call_result.transcript,
            "duration_seconds": call_result.duration_seconds,
            "completed": call_result.completed,
            "health_score": call_result.health_score,
            "risk_label": call_result.risk_label,
            "key_blocker": call_result.key_blocker,
            "sentiment": call_result.sentiment,
            "recommendation": call_result.recommendation,
            "recording_url": call_result.recording_url,
            "answered_by_voicemail": call_result.answered_by_voicemail,
            "created_at": call_result.created_at,
        }
    return result


@router.get("/")
async def get_customers(
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(_verify_api_key)
):
    """Get all customers with their call results."""
    result = await db.execute(
        select(Customer).order_by(Customer.created_at.desc())
    )
    customers = result.scalars().all()

    # Fetch call results for all customers
    customer_ids = [c.id for c in customers]
    if customer_ids:
        cr_result = await db.execute(
            select(CallResult).where(CallResult.customer_id.in_(customer_ids))
        )
        call_results = {cr.customer_id: cr for cr in cr_result.scalars().all()}
    else:
        call_results = {}

    return {
        "success": True,
        "data": [
            _customer_to_response(c, call_results.get(c.id))
            for c in customers
        ],
        "error": None
    }


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(_verify_api_key)
):
    """Get a single customer with call result."""
    result = await db.execute(
        select(Customer).where(Customer.id == UUID(customer_id))
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    cr_result = await db.execute(
        select(CallResult).where(CallResult.customer_id == customer.id)
    )
    call_result = cr_result.scalar_one_or_none()

    return {
        "success": True,
        "data": _customer_to_response(customer, call_result),
        "error": None
    }


@router.patch("/{customer_id}")
async def update_customer(
    customer_id: str,
    update: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(_verify_api_key)
):
    """Update customer (CSM assignment, status change)."""
    result = await db.execute(
        select(Customer).where(Customer.id == UUID(customer_id))
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if update.csm_name is not None:
        customer.csm_name = update.csm_name
    if update.status is not None:
        customer.status = update.status

    await db.commit()
    await db.refresh(customer)

    return {
        "success": True,
        "data": _customer_to_response(customer),
        "error": None
    }


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(_verify_api_key)
):
    """Upload CSV of customers. Required columns: name, email, phone."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    decoded = content.decode("utf-8-sig")  # Handle BOM
    reader = csv.DictReader(io.StringIO(decoded))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):  # Row 2 = first data row
        name = row.get("name", "").strip()
        email = row.get("email", "").strip()
        phone = row.get("phone", "").strip()

        # Validate required fields
        if not name or not email or not phone:
            skipped += 1
            errors.append(f"Row {i}: missing required field (name, email, or phone)")
            continue

        # Validate E.164 phone format
        if not E164_PATTERN.match(phone):
            skipped += 1
            errors.append(f"Row {i}: invalid phone format '{phone}' (must be E.164: +919876543210)")
            continue

        # Parse optional fields
        days = row.get("days_since_signup", "").strip()
        days_int = None
        if days:
            try:
                days_int = int(days)
            except ValueError:
                pass

        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            company=row.get("company", "").strip() or None,
            product_name=row.get("product_name", "").strip() or None,
            days_since_signup=days_int,
            csm_name=row.get("csm_name", "").strip() or None,
            status="pending"
        )
        db.add(customer)
        created += 1

    if created > 0:
        await db.commit()

    return {
        "success": True,
        "data": {
            "created": created,
            "skipped": skipped,
            "errors": errors[:10]  # Cap error messages
        },
        "error": None
    }
