from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CustomerCreate(BaseModel):
    """Schema for creating a customer from CSV row."""
    name: str
    email: str
    phone: str  # E.164 format
    company: Optional[str] = None
    product_name: Optional[str] = None
    days_since_signup: Optional[int] = None
    csm_name: Optional[str] = None


class CustomerResponse(BaseModel):
    """Schema for returning customer data to frontend."""
    id: str
    name: str
    email: str
    phone: str
    company: Optional[str] = None
    product_name: Optional[str] = None
    days_since_signup: Optional[int] = None
    csm_name: Optional[str] = None
    status: str
    bolna_execution_id: Optional[str] = None
    created_at: datetime
    call_result: Optional["CallResultResponse"] = None

    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    """Schema for updating customer (e.g., CSM assignment)."""
    csm_name: Optional[str] = None
    status: Optional[str] = None


class CallResultResponse(BaseModel):
    """Schema for returning call result data."""
    id: str
    customer_id: str
    bolna_execution_id: str
    transcript: Optional[str] = None
    duration_seconds: Optional[int] = None
    completed: bool = False
    health_score: Optional[int] = None
    risk_label: Optional[str] = None
    key_blocker: Optional[str] = None
    sentiment: Optional[str] = None
    recommendation: Optional[str] = None
    recording_url: Optional[str] = None
    answered_by_voicemail: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Schema for CSV upload result."""
    created: int
    skipped: int
    errors: list[str] = []


class CampaignTriggerRequest(BaseModel):
    """Schema for triggering a calling campaign."""
    customer_ids: list[str]


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[dict | list | str] = None
    error: Optional[str] = None


# Update forward reference
CustomerResponse.model_rebuild()
