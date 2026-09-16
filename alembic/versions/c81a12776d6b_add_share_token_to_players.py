"""add share_token to players

Revision ID: c81a12776d6b
Revises: e3a1b2c3d4e5
Create Date: 2026-09-16 17:29:57.016081

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c81a12776d6b"
down_revision: Union[str, Sequence[str], None] = "e3a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("players_s10", sa.Column("share_token", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_players_s10_share_token"), "players_s10", ["share_token"], unique=True
    )
    op.add_column("players_s5", sa.Column("share_token", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_players_s5_share_token"), "players_s5", ["share_token"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_players_s5_share_token"), table_name="players_s5")
    op.drop_column("players_s5", "share_token")
    op.drop_index(op.f("ix_players_s10_share_token"), table_name="players_s10")
    op.drop_column("players_s10", "share_token")
