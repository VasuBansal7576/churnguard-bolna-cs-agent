"""Campaign routes — trigger Bolna calls for selected customers."""

import os
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.customer import Customer
from services.bolna import trigger_call
from schemas import CampaignTriggerRequest

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    """Verify admin API key from header."""
    if x_api_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/trigger")
async def trigger_campaign(
    request: CampaignTriggerRequest,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(_verify_api_key)
):
    """
    Trigger Bolna calls for a list of customer IDs.
    Updates each customer's status to 'scheduled' and stores the execution_id.
    """
    if not request.customer_ids:
        raise HTTPException(status_code=400, detail="No customer IDs provided")

    triggered = 0
    failed = 0
    errors = []

    for cid in request.customer_ids:
        try:
            result = await db.execute(
                select(Customer).where(Customer.id == UUID(cid))
            )
            customer = result.scalar_one_or_none()

            if not customer:
                errors.append(f"Customer {cid} not found")
                failed += 1
                continue

            if customer.status not in ("pending", "failed"):
                errors.append(f"Customer {cid} already in status '{customer.status}'")
                failed += 1
                continue

            # Call Bolna API
            execution_id = await trigger_call(customer)

            # Update customer
            customer.bolna_execution_id = execution_id
            customer.status = "scheduled"
            triggered += 1

        except Exception as e:
            logger.error(f"Failed to trigger call for {cid}: {e}")
            errors.append(f"Customer {cid}: {str(e)}")
            failed += 1

    await db.commit()

    return {
        "success": True,
        "data": {
            "triggered": triggered,
            "failed": failed,
            "errors": errors[:10]
        },
        "error": None
    }
