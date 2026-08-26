"""merge heads

Revision ID: 512ebbf039ac
Revises: d94d249f85cc, e3a1b2c3d4e5
Create Date: 2026-05-25 13:11:17.661587

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "512ebbf039ac"
down_revision: Union[str, Sequence[str], None] = ("d94d249f85cc", "e3a1b2c3d4e5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
