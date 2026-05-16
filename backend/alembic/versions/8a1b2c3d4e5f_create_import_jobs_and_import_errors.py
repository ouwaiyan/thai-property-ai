"""create import_jobs and import_errors tables

Revision ID: 8a1b2c3d4e5f
Revises: 260c610162a0
Create Date: 2026-05-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '260c610162a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('import_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('original_filename', sa.String(length=500), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('total_rows', sa.Integer(), nullable=True),
    sa.Column('success_rows', sa.Integer(), nullable=True),
    sa.Column('error_rows', sa.Integer(), nullable=True),
    sa.Column('column_mapping', postgresql.JSONB(), nullable=True),
    sa.Column('file_path', sa.String(length=1000), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_jobs_status'), 'import_jobs', ['status'], unique=False)

    op.create_table('import_errors',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('import_job_id', sa.UUID(), nullable=False),
    sa.Column('row_number', sa.Integer(), nullable=False),
    sa.Column('raw_data', postgresql.JSONB(), nullable=True),
    sa.Column('error_messages', postgresql.JSONB(), nullable=False),
    sa.Column('field_name', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['import_job_id'], ['import_jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_errors_import_job_id'), 'import_errors', ['import_job_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_import_errors_import_job_id'), table_name='import_errors')
    op.drop_table('import_errors')
    op.drop_index(op.f('ix_import_jobs_status'), table_name='import_jobs')
    op.drop_table('import_jobs')
