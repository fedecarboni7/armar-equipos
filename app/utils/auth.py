from fastapi import Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import DatabaseError

from app.db.database import get_db
from app.db.models import User
from app.config.logging_config import logger


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except DatabaseError as e:
            if "HRANA_WEBSOCKET_ERROR" in str(e):
                logger.error(f"Database error occurred: {e}")
                db.rollback()
                return None
            raise e
    return None
