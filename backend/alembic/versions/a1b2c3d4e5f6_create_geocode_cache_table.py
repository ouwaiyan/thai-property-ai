"""create geocode_cache table

Revision ID: a1b2c3d4e5f6
Revises: bfa8d4c2983a
Create Date: 2026-05-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "bfa8d4c2983a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geocode_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query_text", sa.String(500), nullable=False, index=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("display_name", sa.String(500), nullable=True),
        sa.Column("provider", sa.String(20), nullable=False, server_default="nominatim"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("geocode_cache")
