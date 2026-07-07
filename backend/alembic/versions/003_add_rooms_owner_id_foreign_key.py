"""add foreign key constraint on rooms.owner_id

Revision ID: 003
Revises: 002
Create Date: 2026-07-07 00:00:00.000000

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str = "002"
branch_labels: str | None = None
depends_on: str | None = None

_FK_NAME = "fk_rooms_owner_id_users"


def upgrade() -> None:
    """Add a SET NULL foreign key from rooms.owner_id to users.id.

    owner_id is nullable, so SET NULL detaches a room from its owner when the
    user is deleted rather than deleting the room. Any pre-existing owner_id
    values that do not reference a real user are first reset to NULL so the
    constraint can be applied cleanly.

    batch_alter_table is used so the migration works on both PostgreSQL and
    SQLite; SQLite cannot ALTER a table to add a constraint in place and instead
    recreates the table under the hood.
    """
    op.execute("UPDATE rooms SET owner_id = NULL WHERE owner_id IS NOT NULL AND owner_id NOT IN (SELECT id FROM users)")
    with op.batch_alter_table("rooms", schema=None) as batch_op:
        batch_op.create_foreign_key(
            _FK_NAME,
            "users",
            ["owner_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Drop the foreign key constraint on rooms.owner_id."""
    with op.batch_alter_table("rooms", schema=None) as batch_op:
        batch_op.drop_constraint(_FK_NAME, type_="foreignkey")
