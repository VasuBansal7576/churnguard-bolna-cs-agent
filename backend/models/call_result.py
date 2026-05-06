import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base


class CallResult(Base):
    """Structured result from a Bolna voice call."""
    __tablename__ = "call_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False
    )
    bolna_execution_id = Column(String, nullable=False, unique=True)
    transcript = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False)
    health_score = Column(Integer, nullable=True)      # 0-100
    risk_label = Column(String, nullable=True)          # Healthy | Monitor | At-Risk
    key_blocker = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)           # positive | neutral | frustrated
    recommendation = Column(String, nullable=True)      # escalate | monitor | healthy
    recording_url = Column(String, nullable=True)
    answered_by_voicemail = Column(Boolean, default=False)
    raw_webhook_payload = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<CallResult {self.bolna_execution_id} score={self.health_score}>"
