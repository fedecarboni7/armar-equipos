from datetime import date, datetime
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


class InviteRequest(BaseModel):
    invited_username: str


class MatchPlayerCreate(BaseModel):
    player_s5_id: Optional[int] = None
    player_s10_id: Optional[int] = None
    team: Literal["A", "B"]
    goals: int = 0
    assists: int = 0


class MatchCreate(BaseModel):
    club_id: Optional[int] = None
    played_at: date
    team_a_score: int
    team_b_score: int
    notes: Optional[str] = None
    players: List[MatchPlayerCreate]


class MatchUpdate(BaseModel):
    played_at: Optional[date] = None
    team_a_score: Optional[int] = None
    team_b_score: Optional[int] = None
    notes: Optional[str] = None
    players: Optional[List[MatchPlayerCreate]] = None


class MatchPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    player_s5_id: Optional[int] = None
    player_s10_id: Optional[int] = None
    team: str
    result: str
    goals: int
    assists: int


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    club_id: Optional[int] = None
    created_by: int
    played_at: date
    team_a_score: int
    team_b_score: int
    notes: Optional[str] = None
    created_at: datetime
    players: List[MatchPlayerResponse] = Field(default_factory=list)


class MatchStandingResponse(BaseModel):
    player_id: int
    player_name: str
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    goals: int
    assists: int
    last_match: date
