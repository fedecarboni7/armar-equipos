from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.db.models import User
from app.config.settings import Settings

SECRET_KEY = Settings().secret_key
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def verify_admin_user(current_user: User, detail: str):
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    if current_user.username != "admin":
        raise HTTPException(status_code=401, detail=detail)


def generate_email_confirmation_token() -> str:
    """Generate a secure random token for email confirmation"""
    return secrets.token_urlsafe(32)


def create_email_confirmation_token(db: Session, user: User) -> str:
    """Create and assign an email confirmation token to user"""
    # Generate token
    token = generate_email_confirmation_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hours expiration

    # Update user with token
    user.email_confirmation_token = token
    user.email_confirmation_expires = expires_at

    db.commit()
    db.refresh(user)

    return token


def validate_email_confirmation_token(db: Session, token: str) -> Optional[User]:
    """Validate email confirmation token and return user if valid"""
    from app.db.models import User as UserModel

    user = (
        db.query(UserModel)
        .filter(
            UserModel.email_confirmation_token == token,
            UserModel.email_confirmation_expires > datetime.now(timezone.utc),
            UserModel.email_confirmed.in_(
                [0, -1]
            ),  # Both new users (0) and legacy users (-1) with unconfirmed emails
        )
        .first()
    )

    return user


def confirm_user_email(db: Session, user: User) -> bool:
    """Mark user email as confirmed and clear confirmation token"""
    try:
        user.email_confirmed = 1  # 1 = email confirmado
        user.email_confirmation_token = None
        user.email_confirmation_expires = None

        db.commit()
        db.refresh(user)
        return True
    except Exception:
        db.rollback()
        return False
