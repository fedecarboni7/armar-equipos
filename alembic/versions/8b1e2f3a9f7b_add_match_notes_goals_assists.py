"""add match notes, goals, assists

Revision ID: 8b1e2f3a9f7b
Revises: c6a9f1b0c2d3
Create Date: 2026-05-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b1e2f3a9f7b"
down_revision = "c6a9f1b0c2d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "match_players",
        sa.Column("goals", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "match_players",
        sa.Column("assists", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("match_players", "assists")
    op.drop_column("match_players", "goals")
    op.drop_column("matches", "notes")
