"""add photo_url to players

Revision ID: c980ceef5766
Revises: d94d249f85cc
Create Date: 2026-07-22 17:25:25.642359

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c980ceef5766"
down_revision: Union[str, Sequence[str], None] = "d94d249f85cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("players_s5", sa.Column("photo_url", sa.String(), nullable=True))
    op.add_column("players_s10", sa.Column("photo_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("players_s10", "photo_url")
    op.drop_column("players_s5", "photo_url")
