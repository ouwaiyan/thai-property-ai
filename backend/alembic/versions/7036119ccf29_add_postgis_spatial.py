"""add postgis spatial support

Revision ID: 7036119ccf29
Revises: c69121a8668d
Create Date: 2026-05-15 02:15:30.836532
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision: str = '7036119ccf29'
down_revision: Union[str, Sequence[str], None] = 'c69121a8668d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # 2. Add geography column (nullable initially, no auto-index)
    op.add_column(
        "properties",
        sa.Column(
            "location_geo",
            Geography("POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
    )

    # 3. Backfill from existing latitude/longitude columns
    #    PostGIS uses (longitude, latitude) order for ST_MakePoint
    op.execute("""
        UPDATE properties
        SET location_geo = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND location_geo IS NULL
    """)

    # 4. Create GiST index for spatial queries
    op.create_index(
        "ix_properties_location_geo",
        "properties",
        ["location_geo"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("ix_properties_location_geo", table_name="properties")
    op.drop_column("properties", "location_geo")
    # PostGIS extension is shared infrastructure — not dropped here
