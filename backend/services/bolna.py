"""Bolna API client — triggers outbound voice calls."""

import os
import httpx
from models.customer import Customer

BOLNA_BASE = "https://api.bolna.ai"


async def trigger_call(customer: Customer) -> str:
    """
    Trigger a Bolna outbound call for the given customer.
    Returns the execution_id from Bolna.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BOLNA_BASE}/call",
            headers={
                "Authorization": f"Bearer {os.getenv('BOLNA_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "agent_id": os.getenv("BOLNA_AGENT_ID"),
                "recipient_phone_number": customer.phone,
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
