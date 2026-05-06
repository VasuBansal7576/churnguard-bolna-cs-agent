"""Initial ChurnGuard schema.

Revision ID: 20260506_0001
Revises:
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260506_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("product_name", sa.String(), nullable=True),
        sa.Column("days_since_signup", sa.Integer(), nullable=True),
        sa.Column("csm_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("bolna_execution_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bolna_execution_id"),
    )
    op.create_table(
        "call_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bolna_execution_id", sa.String(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("health_score", sa.Integer(), nullable=True),
        sa.Column("risk_label", sa.String(), nullable=True),
        sa.Column("key_blocker", sa.String(), nullable=True),
        sa.Column("sentiment", sa.String(), nullable=True),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("recording_url", sa.String(), nullable=True),
        sa.Column("answered_by_voicemail", sa.Boolean(), nullable=True),
        sa.Column("raw_webhook_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bolna_execution_id"),
    )


def downgrade() -> None:
    op.drop_table("call_results")
    op.drop_table("customers")
