"""Webhook route — receives Bolna call completion data."""

import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_db
from models.customer import Customer
from models.call_result import CallResult
from services.health_score import (
    parse_bolna_extraction,
    llm_extract_health,
    map_bolna_status,
    is_terminal_status
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/bolna")
async def handle_bolna_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive webhook from Bolna on call status transitions.
    
    No API key required — Bolna calls this directly.
    Webhook fires at every status transition; we only process terminal statuses.
    Returns 200 immediately to prevent Bolna retries.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.error("Failed to parse webhook payload")
        return {"success": True}  # Still return 200

    execution_id = payload.get("id")
    bolna_status = payload.get("status")

    if not execution_id or not bolna_status:
        logger.warning(f"Webhook missing id or status: {payload.keys()}")
        return {"success": True}

    logger.info(f"Webhook received: execution={execution_id} status={bolna_status}")

    # Only process terminal statuses
    if not is_terminal_status(bolna_status):
        # Update customer status for intermediate states (ringing, in-progress, etc.)
        our_status = map_bolna_status(bolna_status)
        result = await db.execute(
            select(Customer).where(Customer.bolna_execution_id == execution_id)
        )
        customer = result.scalar_one_or_none()
        if customer:
            customer.status = our_status
            await db.commit()
        return {"success": True}

    # --- Terminal status processing ---

    # Find customer
    result = await db.execute(
        select(Customer).where(Customer.bolna_execution_id == execution_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        logger.warning(f"No customer found for execution_id={execution_id}")
        return {"success": True}

    # Map status
    our_status = map_bolna_status(bolna_status)
    customer.status = our_status

    has_transcript = bool(payload.get("transcript"))

    # Bolna can send "call-disconnected" after a valid answered call. If a
    # transcript exists, treat it as analyzable completion for CS health scoring.
    if bolna_status == "call-disconnected" and has_transcript:
        customer.status = "completed"

    # Build call result
    if bolna_status == "completed" or (bolna_status == "call-disconnected" and has_transcript):
        # Extract health data — try Bolna extraction first
        extracted = payload.get("extracted_data")
        health_data = parse_bolna_extraction(extracted)

        # Fallback to LLM if Bolna extraction is empty
        if health_data["health_score"] is None and payload.get("transcript"):
            logger.info(f"Bolna extraction empty for {execution_id}, falling back to LLM")
            health_data = await llm_extract_health(payload["transcript"])

        telephony = payload.get("telephony_data", {})

        call_result = CallResult(
            customer_id=customer.id,
            bolna_execution_id=execution_id,
            transcript=payload.get("transcript"),
            duration_seconds=payload.get("conversation_time"),
            completed=True,
            health_score=health_data["health_score"],
            risk_label=health_data["risk_label"],
            key_blocker=health_data["key_blocker"],
            sentiment=health_data["sentiment"],
            recommendation=health_data["recommendation"],
            recording_url=telephony.get("recording_url"),
            answered_by_voicemail=payload.get("answered_by_voice_mail", False),
            raw_webhook_payload=payload
        )
    else:
        # Failed call — store minimal result
        call_result = CallResult(
            customer_id=customer.id,
            bolna_execution_id=execution_id,
            completed=False,
            raw_webhook_payload=payload
        )

    try:
        db.add(call_result)
        await db.commit()
        logger.info(f"Call result saved for {execution_id}: score={call_result.health_score}")
    except IntegrityError:
        # Duplicate execution_id — webhook retry, already processed
        await db.rollback()
        logger.info(f"Duplicate webhook for {execution_id}, skipping")

    return {"success": True}
