from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# User schemas
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None


# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class PlayerCreate(BaseModel):
    id: Optional[int] = None
    name: str
    velocidad: int
    resistencia: int
    control: int
    pases: int
    tiro: int
    defensa: int
    habilidad_arquero: int
    fuerza_cuerpo: int
    vision: int
    photo_data: Optional[str] = None  # Base64 encoded image data
    club_id: Optional[int] = None


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    velocidad: int
    resistencia: int
    control: int
    pases: int
    tiro: int
    defensa: int
    habilidad_arquero: int
    fuerza_cuerpo: int
    vision: int
    photo_data: Optional[str] = None  # Base64 encoded image data
    updated_at: datetime
    user_id: Optional[int] = None
    club_id: Optional[int] = None


# Schemas para Club
class ClubCreate(BaseModel):
    name: str


class ClubResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    creation_date: datetime


# Schemas para ClubUser
class ClubUserCreate(BaseModel):
    user_id: int
    role: Optional[str] = "miembro"


class ClubUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    club_id: int
    role: str


class ClubUsersResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    club_id: int
    role: str
    username: str


# Schemas para SkillVote
class PlayerSkillsVote(BaseModel):
    velocidad: int
    resistencia: int
    control: int
    pases: int
    tiro: int
    defensa: int
    habilidad_arquero: int
    fuerza_cuerpo: int
    vision: int


class SkillVoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    voter_id: int
    velocidad: int
    resistencia: int
    control: int
    pases: int
    tiro: int
    defensa: int
    habilidad_arquero: int
    fuerza_cuerpo: int
    vision: int
    vote_date: datetime


class InviteRequest(BaseModel):
    invited_username: str


class MatchPlayerCreate(BaseModel):
    player_v1_id: Optional[int] = None
    player_v2_id: Optional[int] = None
    team: Literal["A", "B"]


class MatchCreate(BaseModel):
    club_id: Optional[int] = None
    played_at: datetime
    team_a_score: int
    team_b_score: int
    players: List[MatchPlayerCreate]


class MatchUpdate(BaseModel):
    played_at: Optional[datetime] = None
    team_a_score: Optional[int] = None
    team_b_score: Optional[int] = None
    players: Optional[List[MatchPlayerCreate]] = None


class MatchPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    player_v1_id: Optional[int] = None
    player_v2_id: Optional[int] = None
    team: str
    result: str


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    club_id: Optional[int] = None
    created_by: int
    played_at: datetime
    team_a_score: int
    team_b_score: int
    created_at: datetime
    players: List[MatchPlayerResponse] = Field(default_factory=list)


class MatchStatsResponse(BaseModel):
    played: int
    wins: int
    losses: int
    draws: int


class MatchStandingResponse(BaseModel):
    player_id: int
    player_name: str
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    last_match: datetime
