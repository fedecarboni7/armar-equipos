from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, get_argentina_now


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            today = get_argentina_now().date()
            if user.last_seen_at is None or user.last_seen_at.date() < today:
                user.last_seen_at = get_argentina_now()
                db.commit()
        return user
    return None
