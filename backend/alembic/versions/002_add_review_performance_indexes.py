"""add review performance indexes and version column

Revision ID: 002
Revises: 001
Create Date: 2026-04-01 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add performance indexes on date columns and version column for optimistic locking."""
    # Indexes for review queue and stats queries
    op.create_index("ix_memory_items_created_at", "memory_items", ["created_at"])
    op.create_index("ix_memory_items_last_reviewed_at", "memory_items", ["last_reviewed_at"])
    op.create_index("ix_review_records_reviewed_at", "review_records", ["reviewed_at"])

    # Optimistic locking version column
    op.add_column("memory_items", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    """Remove performance indexes and version column."""
    op.drop_column("memory_items", "version")
    op.drop_index("ix_review_records_reviewed_at", table_name="review_records")
    op.drop_index("ix_memory_items_last_reviewed_at", table_name="memory_items")
    op.drop_index("ix_memory_items_created_at", table_name="memory_items")
