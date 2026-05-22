"""rename player indexes to match model

Revision ID: d94d249f85cc
Revises: 9f5f1df834e3
Create Date: 2026-05-22 16:02:03.962660

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d94d249f85cc"
down_revision: Union[str, Sequence[str], None] = "9f5f1df834e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER INDEX ix_players_id RENAME TO ix_players_s5_id")
    op.execute("ALTER INDEX ix_players_name RENAME TO ix_players_s5_name")
    op.execute("ALTER INDEX ix_players_v2_id RENAME TO ix_players_s10_id")
    op.execute("ALTER INDEX ix_players_v2_name RENAME TO ix_players_s10_name")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER INDEX ix_players_s10_name RENAME TO ix_players_v2_name")
    op.execute("ALTER INDEX ix_players_s10_id RENAME TO ix_players_v2_id")
    op.execute("ALTER INDEX ix_players_s5_name RENAME TO ix_players_name")
    op.execute("ALTER INDEX ix_players_s5_id RENAME TO ix_players_id")
