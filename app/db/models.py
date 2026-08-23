from datetime import datetime
from enum import Enum
from passlib.hash import pbkdf2_sha256
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Boolean,
    Text,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy import Date
from sqlalchemy.orm import DeclarativeBase, relationship

from app.config.settings import Settings


# Función helper para obtener datetime con timezone argentino
def get_argentina_now():
    """Obtiene la fecha y hora actual en timezone de Argentina"""
    settings = Settings()
    return datetime.now(settings.arg_timezone)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)
    email = Column(
        String, unique=True, index=True, nullable=True
    )  # Nullable para usuarios existentes
    google_id = Column(String, unique=True, nullable=True, index=True)
    email_confirmed = Column(
        Integer, default=0, nullable=False
    )  # 0=nuevo sin confirmar, -1=legacy sin confirmar, 1=confirmado
    email_confirmation_token = Column(String, nullable=True)
    email_confirmation_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_argentina_now)

    players_s5 = relationship(
        "PlayerScale5",
        foreign_keys="[PlayerScale5.user_id]",
        back_populates="user",
    )
    players_s10 = relationship(
        "PlayerScale10",
        foreign_keys="[PlayerScale10.user_id]",
        back_populates="user",
    )
    club_users = relationship("ClubUser", back_populates="user")
    matches_created = relationship("Match", back_populates="creator")
    skill_votes = relationship("SkillVote", back_populates="voter")

    def set_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def verify_password(self, password):
        if self.password is None:
            return False
        return pbkdf2_sha256.verify(password, self.password)

    def has_password(self) -> bool:
        return self.password is not None

    def is_new_user(self):
        """Check if this is a new user (requires email confirmation to login)"""
        return self.email_confirmed == 0

    def is_legacy_user_with_unconfirmed_email(self):
        """Check if this is a legacy user with unconfirmed email (can login without confirmation)"""
        return self.email_confirmed == -1

    def is_email_confirmed(self):
        """Check if email is confirmed"""
        return self.email_confirmed == 1

    def has_unconfirmed_email(self):
        """Check if user has an unconfirmed email (new or legacy)"""
        return self.email_confirmed in [0, -1]


class PlayerScale5(Base):
    __tablename__ = "players_s5"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    velocidad = Column(Integer)
    resistencia = Column(Integer)
    control = Column(Integer)
    pases = Column(Integer)
    tiro = Column(Integer)
    defensa = Column(Integer)
    habilidad_arquero = Column(Integer)
    fuerza_cuerpo = Column(Integer)
    vision = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    club_id = Column(Integer, ForeignKey("clubs.id"))
    updated_at = Column(DateTime, default=get_argentina_now, onupdate=get_argentina_now)
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="players_s5")
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
    club = relationship("Club", back_populates="players_s5")
    match_players = relationship("MatchPlayer", back_populates="player_s5")
    skill_votes = relationship("SkillVote", back_populates="player_s5")


class PlayerScale10(Base):
    __tablename__ = "players_s10"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    velocidad = Column(Integer)
    resistencia = Column(Integer)
    control = Column(Integer)
    pases = Column(Integer)
    tiro = Column(Integer)
    defensa = Column(Integer)
    habilidad_arquero = Column(Integer)
    fuerza_cuerpo = Column(Integer)
    vision = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    club_id = Column(Integer, ForeignKey("clubs.id"))
    updated_at = Column(DateTime, default=get_argentina_now, onupdate=get_argentina_now)
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="players_s10")
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
    club = relationship("Club", back_populates="players_s10")
    match_players_s10 = relationship("MatchPlayer", back_populates="player_s10")
    skill_votes = relationship("SkillVote", back_populates="player_s10")


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    creation_date = Column(DateTime, default=get_argentina_now)

    members = relationship("ClubUser", back_populates="club")
    players_s5 = relationship("PlayerScale5", back_populates="club")
    players_s10 = relationship("PlayerScale10", back_populates="club")
    matches = relationship("Match", back_populates="club")
    skill_votes = relationship("SkillVote", back_populates="club")


class SkillVote(Base):
    __tablename__ = "skill_votes"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    voter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_s5_id = Column(Integer, ForeignKey("players_s5.id"), nullable=True)
    player_s10_id = Column(Integer, ForeignKey("players_s10.id"), nullable=True)
    velocidad = Column(Integer, nullable=False)
    resistencia = Column(Integer, nullable=False)
    control = Column(Integer, nullable=False)
    pases = Column(Integer, nullable=False)
    tiro = Column(Integer, nullable=False)
    defensa = Column(Integer, nullable=False)
    habilidad_arquero = Column(Integer, nullable=False)
    fuerza_cuerpo = Column(Integer, nullable=False)
    vision = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=get_argentina_now, onupdate=get_argentina_now)

    __table_args__ = (
        CheckConstraint(
            "(player_s5_id IS NOT NULL AND player_s10_id IS NULL) OR "
            "(player_s5_id IS NULL AND player_s10_id IS NOT NULL)",
            name="ck_skill_votes_one_player",
        ),
        UniqueConstraint("voter_id", "player_s5_id", name="uq_skill_votes_voter_s5"),
        UniqueConstraint("voter_id", "player_s10_id", name="uq_skill_votes_voter_s10"),
    )

    club = relationship("Club", back_populates="skill_votes")
    voter = relationship("User", back_populates="skill_votes")
    player_s5 = relationship("PlayerScale5", back_populates="skill_votes")
    player_s10 = relationship("PlayerScale10", back_populates="skill_votes")


class ClubUser(Base):
    __tablename__ = "club_users"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)

    club = relationship("Club", back_populates="members")
    user = relationship("User", back_populates="club_users")


class InvitationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ClubInvitation(Base):
    __tablename__ = "club_invitations"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    invited_user_id = Column(Integer, ForeignKey("users.id"))
    inviter_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default=InvitationStatus.PENDING.value)
    creation_date = Column(DateTime, default=get_argentina_now)
    expiration_date = Column(DateTime)

    club = relationship("Club", backref="invitations")
    invited_user = relationship("User", foreign_keys=[invited_user_id])
    inviter = relationship("User", foreign_keys=[inviter_id])


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=get_argentina_now)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

    user = relationship("User", backref="password_reset_tokens")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    played_at = Column(Date, nullable=False)
    team_a_score = Column(Integer, nullable=False)
    team_b_score = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_argentina_now)

    club = relationship("Club", back_populates="matches")
    creator = relationship("User", back_populates="matches_created")
    match_players = relationship(
        "MatchPlayer", back_populates="match", cascade="all, delete-orphan"
    )


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_s5_id = Column(Integer, ForeignKey("players_s5.id"), nullable=True)
    player_s10_id = Column(Integer, ForeignKey("players_s10.id"), nullable=True)
    team = Column(String, nullable=False)
    result = Column(String, nullable=False)
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint(
            "(player_s5_id IS NOT NULL AND player_s10_id IS NULL) OR "
            "(player_s5_id IS NULL AND player_s10_id IS NOT NULL)",
            name="ck_match_players_one_player",
        ),
    )

    match = relationship("Match", back_populates="match_players")
    player_s5 = relationship("PlayerScale5", back_populates="match_players")
    player_s10 = relationship("PlayerScale10", back_populates="match_players_s10")
