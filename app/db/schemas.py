from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


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