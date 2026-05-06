"""ChurnGuard API — Voice AI Customer Success Platform."""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import customers, campaigns, webhook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

app = FastAPI(
    title="ChurnGuard API",
    description="Voice AI customer success platform — Bolna integration",
    version="1.0.0"
)

# CORS — allow frontend origins. FRONTEND_URL can be a comma-separated list
# so local dev and deployed frontend can both call the backend.
frontend_urls = [
    origin.strip()
    for origin in os.getenv("FRONTEND_URL", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([*frontend_urls, "http://localhost:3000"])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhook"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"success": True, "data": "ChurnGuard API is running", "error": None}


@app.get("/health")
async def health():
    """Health check for deployment monitoring."""
    return {"status": "ok"}
