from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.database_utils import (
    execute_with_retries,
    query_player,
    query_players,
    has_club_write_permission,
)
from app.db.models import PlayerScale5, PlayerScale10, User
from app.db.schemas import PlayerCreate, PlayerResponse
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/api/players")
def get_players(
    scale: str = Query("1-5", pattern="^(1-5|1-10)$"),
    club_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PlayerResponse]:
    """Obtener jugadores según la escala especificada"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    try:
        players = execute_with_retries(
            query_players, db, current_user.id, club_id, scale
        )
        return players
    except OperationalError:
        raise HTTPException(
            status_code=500,
            detail="Error al acceder a la base de datos. Intentalo de nuevo más tarde.",
        )


@router.post("/api/player")
def save_player(
    player_data: PlayerCreate,
    scale: str = Query("1-5", pattern="^(1-5|1-10)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlayerResponse:
    """Crear jugador"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    # Verificar permisos si el jugador pertenece a un club
    if player_data.club_id is not None:
        if not has_club_write_permission(db, player_data.club_id, current_user.id):
            raise HTTPException(
                status_code=403,
                detail="No tenés permisos para crear jugadores en este club",
            )

    try:
        # Crear nuevo jugador
        if scale == "1-10":
            new_player = PlayerScale10(**player_data.model_dump(), user_id=current_user.id)
        else:
            new_player = PlayerScale5(**player_data.model_dump(), user_id=current_user.id)
        db.add(new_player)
        db.commit()
        return new_player
    except OperationalError:
        raise HTTPException(
            status_code=500,
            detail="Error al guardar el jugador. Intentalo de nuevo más tarde.",
        )


@router.put("/api/player")
def update_player(
    player_data: PlayerCreate,
    scale: str = Query("1-5", pattern="^(1-5|1-10)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlayerResponse:
    """Actualizar jugador"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    try:
        existing_player = execute_with_retries(
            query_player, db, player_data.id, current_user.id, scale
        )

        if existing_player is None:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")

        # Verificar permisos si el jugador pertenece a un club
        if existing_player.club_id is not None:
            if not has_club_write_permission(
                db, existing_player.club_id, current_user.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="No tenés permisos para editar jugadores en este club",
                )

        for key, value in player_data.model_dump().items():
            setattr(existing_player, key, value)

        db.commit()
        return existing_player

    except OperationalError:
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar el jugador. Intentalo de nuevo más tarde.",
        )


@router.delete("/api/players/{player_id}")
def delete_player(
    player_id: int,
    scale: str = Query("1-5", pattern="^(1-5|1-10)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar un jugador"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    try:
        existing_player = execute_with_retries(
            query_player, db, player_id, current_user.id, scale
        )

        if existing_player is None:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")

        # Verificar permisos si el jugador pertenece a un club
        if existing_player.club_id is not None:
            if not has_club_write_permission(
                db, existing_player.club_id, current_user.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="No tenés permisos para eliminar jugadores en este club",
                )

        def delete_operation():
            db.delete(existing_player)
            db.commit()

        execute_with_retries(delete_operation)
        return {"message": "Jugador eliminado correctamente"}

    except OperationalError:
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el jugador. Intentalo de nuevo más tarde.",
        )
