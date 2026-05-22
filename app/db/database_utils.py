from sqlalchemy.exc import OperationalError, DatabaseError
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_fixed

from app.db.models import Club, ClubUser, PlayerScale5, PlayerScale10, User


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def execute_with_retries(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except (OperationalError, DatabaseError) as e:
        raise e


def query_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def query_player(db: Session, player_id: int, current_user_id: int, scale: str = "1-5"):
    PlayerModel = PlayerScale10 if scale == "1-10" else PlayerScale5
    player = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()

    if player is None:
        return None

    # Si el jugador pertenece a un club, verificar que el usuario sea miembro
    if player.club_id is not None:
        is_club_member = (
            db.query(ClubUser)
            .filter(
                ClubUser.club_id == player.club_id, ClubUser.user_id == current_user_id
            )
            .first()
            is not None
        )
        if is_club_member:
            return player
        return None

    # Si el jugador no pertenece a un club, verificar que sea el propietario
    if player.user_id == current_user_id:
        return player

    return None


def query_players(
    db: Session, current_user_id: int, club_id: int = None, scale: str = "1-5"
):
    if scale == "1-10":
        if club_id is None:
            return (
                db.query(PlayerScale10)
                .filter(
                    PlayerScale10.user_id == current_user_id,
                    PlayerScale10.club_id.is_(None),
                )
                .all()
            )
        else:
            return db.query(PlayerScale10).filter(PlayerScale10.club_id == club_id).all()
    else:
        if club_id is None:
            return (
                db.query(PlayerScale5)
                .filter(
                    PlayerScale5.user_id == current_user_id,
                    PlayerScale5.club_id.is_(None),
                )
                .all()
            )
        else:
            return db.query(PlayerScale5).filter(PlayerScale5.club_id == club_id).all()


def query_clubs(db: Session, current_user_id: int):
    return (
        db.query(Club).join(ClubUser).filter(ClubUser.user_id == current_user_id).all()
    )


def query_club_members(db: Session, club_id: int):
    return (
        db.query(ClubUser, User)
        .join(User, ClubUser.user_id == User.id)
        .filter(ClubUser.club_id == club_id)
        .all()
    )


def get_club_user_role(db: Session, club_id: int, user_id: int) -> str | None:
    """Obtiene el rol de un usuario en un club. Retorna None si no es miembro."""
    club_user = (
        db.query(ClubUser)
        .filter(ClubUser.club_id == club_id, ClubUser.user_id == user_id)
        .first()
    )
    return club_user.role if club_user else None


def has_club_write_permission(db: Session, club_id: int, user_id: int) -> bool:
    """Verifica si un usuario tiene permisos de escritura en un club (admin u owner)."""
    role = get_club_user_role(db, club_id, user_id)
    return role in ("admin", "owner")
