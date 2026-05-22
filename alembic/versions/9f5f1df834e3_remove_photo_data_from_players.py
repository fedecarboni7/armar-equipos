"""remove photo_data from players

Revision ID: 9f5f1df834e3
Revises: b7e5f2c3d4a6
Create Date: 2026-05-22 15:53:36.563043

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f5f1df834e3"
down_revision: Union[str, Sequence[str], None] = "b7e5f2c3d4a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("players_s10", "photo_data")
    op.drop_column("players_s5", "photo_data")


def downgrade() -> None:
    op.add_column(
        "players_s5",
        sa.Column("photo_data", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "players_s10",
        sa.Column("photo_data", sa.TEXT(), autoincrement=False, nullable=True),
    )
