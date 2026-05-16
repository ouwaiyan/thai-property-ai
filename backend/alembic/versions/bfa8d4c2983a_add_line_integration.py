"""add LINE integration tables and Lead fields

Revision ID: bfa8d4c2983a
Revises: 7036119ccf29
Create Date: 2026-05-15 03:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = 'bfa8d4c2983a'
down_revision: Union[str, Sequence[str], None] = '7036119ccf29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add LINE fields to leads table
    op.add_column("leads", sa.Column("source", sa.String(20), nullable=False, server_default="web"))
    op.add_column("leads", sa.Column("line_user_id", sa.String(64), nullable=True))
    op.create_index("ix_leads_line_user_id", "leads", ["line_user_id"])

    # 2. Create line_messages table
    op.create_table(
        "line_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("line_user_id", sa.String(64), nullable=False, index=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False, server_default="incoming"),
        sa.Column("message_type", sa.String(16), nullable=False, server_default="text"),
        sa.Column("reply_token", sa.String(255), nullable=True),
        sa.Column("source_type", sa.String(16), nullable=False, server_default="user"),
        sa.Column("reply_status", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("line_messages")
    op.drop_index("ix_leads_line_user_id", table_name="leads")
    op.drop_column("leads", "line_user_id")
    op.drop_column("leads", "source")
