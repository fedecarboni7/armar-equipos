"""change matches played_at to date

Revision ID: 4c2f6d9e1b7a
Revises: 8b1e2f3a9f7b
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4c2f6d9e1b7a"
down_revision = "8b1e2f3a9f7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("matches") as batch_op:
        batch_op.alter_column(
            "played_at",
            existing_type=sa.DateTime(),
            type_=sa.Date(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("matches") as batch_op:
        batch_op.alter_column(
            "played_at",
            existing_type=sa.Date(),
            type_=sa.DateTime(),
            nullable=False,
        )
