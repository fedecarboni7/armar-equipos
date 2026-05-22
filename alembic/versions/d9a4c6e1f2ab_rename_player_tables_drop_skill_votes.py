"""rename player tables and drop skill votes

Revision ID: d9a4c6e1f2ab
Revises: 4c2f6d9e1b7a
Create Date: 2026-05-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d9a4c6e1f2ab"
down_revision: Union[str, Sequence[str], None] = "4c2f6d9e1b7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table(
        "match_players",
        naming_convention={"fk": "%(table_name)s_%(column_0_name)s_fkey"},
    ) as batch_op:
        batch_op.drop_constraint("match_players_player_v1_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("match_players_player_v2_id_fkey", type_="foreignkey")

    op.rename_table("players", "players_s5")
    op.rename_table("players_v2", "players_s10")

    with op.batch_alter_table(
        "match_players",
        naming_convention={"fk": "%(table_name)s_%(column_0_name)s_fkey"},
    ) as batch_op:
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

    op.drop_table("skill_votes")
    op.drop_table("skill_votes_v2")


def downgrade() -> None:
    with op.batch_alter_table(
        "match_players",
        naming_convention={"fk": "%(table_name)s_%(column_0_name)s_fkey"},
    ) as batch_op:
        batch_op.drop_constraint("match_players_player_v1_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("match_players_player_v2_id_fkey", type_="foreignkey")

    op.rename_table("players_s5", "players")
    op.rename_table("players_s10", "players_v2")

    with op.batch_alter_table(
        "match_players",
        naming_convention={"fk": "%(table_name)s_%(column_0_name)s_fkey"},
    ) as batch_op:
        batch_op.create_foreign_key(
            "match_players_player_v1_id_fkey",
            "players",
            ["player_v1_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "match_players_player_v2_id_fkey",
            "players_v2",
            ["player_v2_id"],
            ["id"],
        )

    op.create_table(
        "skill_votes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.Column("voter_id", sa.Integer(), nullable=True),
        sa.Column("velocidad", sa.Integer(), nullable=True),
        sa.Column("resistencia", sa.Integer(), nullable=True),
        sa.Column("control", sa.Integer(), nullable=True),
        sa.Column("pases", sa.Integer(), nullable=True),
        sa.Column("tiro", sa.Integer(), nullable=True),
        sa.Column("defensa", sa.Integer(), nullable=True),
        sa.Column("habilidad_arquero", sa.Integer(), nullable=True),
        sa.Column("fuerza_cuerpo", sa.Integer(), nullable=True),
        sa.Column("vision", sa.Integer(), nullable=True),
        sa.Column("vote_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["voter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_skill_votes_id"), "skill_votes", ["id"], unique=False)

    op.create_table(
        "skill_votes_v2",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.Column("voter_id", sa.Integer(), nullable=True),
        sa.Column("velocidad", sa.Integer(), nullable=True),
        sa.Column("resistencia", sa.Integer(), nullable=True),
        sa.Column("control", sa.Integer(), nullable=True),
        sa.Column("pases", sa.Integer(), nullable=True),
        sa.Column("tiro", sa.Integer(), nullable=True),
        sa.Column("defensa", sa.Integer(), nullable=True),
        sa.Column("habilidad_arquero", sa.Integer(), nullable=True),
        sa.Column("fuerza_cuerpo", sa.Integer(), nullable=True),
        sa.Column("vision", sa.Integer(), nullable=True),
        sa.Column("vote_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players_v2.id"]),
        sa.ForeignKeyConstraint(["voter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_skill_votes_v2_id"), "skill_votes_v2", ["id"], unique=False
    )
