import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class Customer(Base):
    """Customer record — one row per uploaded customer."""
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # E.164 format: +919876543210
    company = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    days_since_signup = Column(Integer, nullable=True)
    csm_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    # pending | scheduled | in_call | completed | failed
    bolna_execution_id = Column(String, nullable=True, unique=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<Customer {self.name} ({self.status})>"
