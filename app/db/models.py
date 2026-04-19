from datetime import datetime
from enum import Enum
from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, Text
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
    password = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)  # Nullable para usuarios existentes
    email_confirmed = Column(Integer, default=0, nullable=False)  # 0=nuevo sin confirmar, -1=legacy sin confirmar, 1=confirmado
    email_confirmation_token = Column(String, nullable=True)
    email_confirmation_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_argentina_now)

    players = relationship("Player", foreign_keys="[Player.user_id]", back_populates="user")
    players_v2 = relationship("PlayerV2", foreign_keys="[PlayerV2.user_id]")
    skill_votes = relationship("SkillVote", back_populates="voter")
    skill_votes_v2 = relationship("SkillVoteV2")
    club_users = relationship("ClubUser", back_populates="user")
    
    def set_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def verify_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)
    
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


class Player(Base):
    __tablename__ = "players"

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
    photo_data = Column(Text, nullable=True)  # Base64 encoded image data
    user_id = Column(Integer, ForeignKey("users.id"))
    club_id = Column(Integer, ForeignKey("clubs.id"))
    updated_at = Column(DateTime, default=get_argentina_now, onupdate=get_argentina_now)
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="players")
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
    club = relationship("Club", back_populates="players")
    skill_votes = relationship("SkillVote", back_populates="player")

class PlayerV2(Base):
    __tablename__ = "players_v2"

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
    photo_data = Column(Text, nullable=True)  # Base64 encoded image data
    user_id = Column(Integer, ForeignKey("users.id"))
    club_id = Column(Integer, ForeignKey("clubs.id"))
    updated_at = Column(DateTime, default=get_argentina_now, onupdate=get_argentina_now)
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="players_v2")
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
    club = relationship("Club", back_populates="players_v2")
    skill_votes_v2 = relationship("SkillVoteV2", back_populates="player")

class SkillVote(Base):
    __tablename__ = "skill_votes"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    voter_id = Column(Integer, ForeignKey("users.id"))
    velocidad = Column(Integer)
    resistencia = Column(Integer)
    control = Column(Integer)
    pases = Column(Integer)
    tiro = Column(Integer)
    defensa = Column(Integer)
    habilidad_arquero = Column(Integer)
    fuerza_cuerpo = Column(Integer)
    vision = Column(Integer)
    vote_date = Column(DateTime, default=get_argentina_now)

    player = relationship("Player", back_populates="skill_votes")
    voter = relationship("User", back_populates="skill_votes")

class SkillVoteV2(Base):
    __tablename__ = "skill_votes_v2"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players_v2.id"))
    voter_id = Column(Integer, ForeignKey("users.id"))
    velocidad = Column(Integer)
    resistencia = Column(Integer)
    control = Column(Integer)
    pases = Column(Integer)
    tiro = Column(Integer)
    defensa = Column(Integer)
    habilidad_arquero = Column(Integer)
    fuerza_cuerpo = Column(Integer)
    vision = Column(Integer)
    vote_date = Column(DateTime, default=get_argentina_now)

    player = relationship("PlayerV2", back_populates="skill_votes_v2")
    voter = relationship("User", back_populates="skill_votes_v2")

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    creation_date = Column(DateTime, default=get_argentina_now)

    members = relationship("ClubUser", back_populates="club")
    players = relationship("Player", back_populates="club")
    players_v2 = relationship("PlayerV2", back_populates="club")

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
