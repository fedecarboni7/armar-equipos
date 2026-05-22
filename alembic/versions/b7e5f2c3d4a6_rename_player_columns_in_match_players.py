"""rename player columns in match_players

Revision ID: b7e5f2c3d4a6
Revises: d9a4c6e1f2ab
Create Date: 2026-05-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7e5f2c3d4a6"
down_revision: Union[str, Sequence[str], None] = "d9a4c6e1f2ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("match_players") as batch_op:
        batch_op.drop_constraint("match_players_player_v1_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("match_players_player_v2_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("ck_match_players_one_player", type_="check")

    with op.batch_alter_table("match_players") as batch_op:
        batch_op.alter_column("player_v1_id", new_column_name="player_s5_id")
        batch_op.alter_column("player_v2_id", new_column_name="player_s10_id")

    with op.batch_alter_table("match_players") as batch_op:
        batch_op.create_check_constraint(
            "ck_match_players_one_player",
            "(player_s5_id IS NOT NULL AND player_s10_id IS NULL) OR "
            "(player_s5_id IS NULL AND player_s10_id IS NOT NULL)",
        )
        batch_op.create_foreign_key(
            "match_players_player_s5_id_fkey",
            "players_s5",
            ["player_s5_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "match_players_player_s10_id_fkey",
            "players_s10",
            ["player_s10_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("match_players") as batch_op:
        batch_op.drop_constraint("match_players_player_s5_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("match_players_player_s10_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("ck_match_players_one_player", type_="check")

    with op.batch_alter_table("match_players") as batch_op:
        batch_op.alter_column("player_s5_id", new_column_name="player_v1_id")
        batch_op.alter_column("player_s10_id", new_column_name="player_v2_id")

    with op.batch_alter_table("match_players") as batch_op:
        batch_op.create_check_constraint(
            "ck_match_players_one_player",
            "(player_v1_id IS NOT NULL AND player_v2_id IS NULL) OR "
            "(player_v1_id IS NULL AND player_v2_id IS NOT NULL)",
        )
        batch_op.create_foreign_key(
            "match_players_player_v1_id_fkey",
            "players_s5",
            ["player_v1_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "match_players_player_v2_id_fkey",
            "players_s10",
            ["player_v2_id"],
            ["id"],
        )
