"""add skill votes

Revision ID: e3a1b2c3d4e5
Revises: 4c2f6d9e1b7a
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3a1b2c3d4e5"
down_revision = "d9a4c6e1f2ab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_votes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("voter_id", sa.Integer(), nullable=False),
        sa.Column("player_s5_id", sa.Integer(), nullable=True),
        sa.Column("player_s10_id", sa.Integer(), nullable=True),
        sa.Column("velocidad", sa.Integer(), nullable=False),
        sa.Column("resistencia", sa.Integer(), nullable=False),
        sa.Column("control", sa.Integer(), nullable=False),
        sa.Column("pases", sa.Integer(), nullable=False),
        sa.Column("tiro", sa.Integer(), nullable=False),
        sa.Column("defensa", sa.Integer(), nullable=False),
        sa.Column("habilidad_arquero", sa.Integer(), nullable=False),
        sa.Column("fuerza_cuerpo", sa.Integer(), nullable=False),
        sa.Column("vision", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "(player_s5_id IS NOT NULL AND player_s10_id IS NULL) OR "
            "(player_s5_id IS NULL AND player_s10_id IS NOT NULL)",
            name="ck_skill_votes_one_player",
        ),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["voter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["player_s5_id"], ["players_s5.id"]),
        sa.ForeignKeyConstraint(["player_s10_id"], ["players_s10.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voter_id", "player_s5_id", name="uq_skill_votes_voter_s5"),
        sa.UniqueConstraint(
            "voter_id", "player_s10_id", name="uq_skill_votes_voter_s10"
        ),
    )
    op.create_index(op.f("ix_skill_votes_id"), "skill_votes", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_skill_votes_id"), table_name="skill_votes")
    op.drop_table("skill_votes")
