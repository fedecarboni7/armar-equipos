from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from typing import Literal, List

from app.db.database import get_db
from app.db.database_utils import (
    execute_with_retries,
    get_club_user_role,
    query_player,
    query_players,
    has_club_write_permission,
)
from app.db.models import PlayerScale5, PlayerScale10, User, MatchPlayer
from app.db.schemas import PlayerCreate, PlayerResponse
from app.utils.auth import get_current_user
from app.utils.r2 import process_player_photo, upload_player_photo, delete_player_photo

from app.config.logging_config import logger

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
            new_player = PlayerScale10(
                **player_data.model_dump(), user_id=current_user.id
            )
        else:
            new_player = PlayerScale5(
                **player_data.model_dump(), user_id=current_user.id
            )
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

        # Clean up photo from R2 before deleting the player record
        if existing_player.photo_url:
            try:
                delete_player_photo(existing_player.photo_url)
            except Exception:
                logger.warning(
                    "Failed to delete photo for player %s, proceeding with deletion",
                    player_id,
                )

        def delete_operation():
            # First delete all match_players that reference this player
            if scale == "1-10":
                # Deleting PlayerScale10 - delete match_players where player_s10_id matches
                db.query(MatchPlayer).filter(
                    MatchPlayer.player_s10_id == player_id
                ).delete()
            else:
                # Deleting PlayerScale5 - delete match_players where player_s5_id matches
                db.query(MatchPlayer).filter(
                    MatchPlayer.player_s5_id == player_id
                ).delete()

            # Then delete the player itself
            db.delete(existing_player)
            db.commit()

        execute_with_retries(delete_operation)
        return {"message": "Jugador eliminado correctamente"}

    except OperationalError:
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el jugador. Intentalo de nuevo más tarde.",
        )


def _resolve_player_model(player_type: str):
    if player_type == "s10":
        return PlayerScale10
    return PlayerScale5


def _get_player_by_type(db: Session, player_type: str, player_id: int):
    model = _resolve_player_model(player_type)
    return db.query(model).filter(model.id == player_id).first()


def _check_photo_authorization(
    db: Session, current_user: User, player, player_type: str
):
    if player is None:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    if player.club_id is not None:
        role = get_club_user_role(db, player.club_id, current_user.id)
        if role not in ("admin", "owner"):
            raise HTTPException(
                status_code=403,
                detail="No tenés permisos para modificar la foto de este jugador",
            )
    else:
        if player.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tenés permisos para modificar la foto de este jugador",
            )


@router.post(
    "/api/players/{player_type}/{player_id}/photo",
    response_model=PlayerResponse,
)
async def upload_photo(
    player_type: Literal["s5", "s10"],
    player_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Subir foto de perfil de un jugador"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    player = _get_player_by_type(db, player_type, player_id)
    _check_photo_authorization(db, current_user, player, player_type)

    file_bytes = await file.read()

    try:
        processed_bytes = process_player_photo(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    old_photo_url = player.photo_url

    try:
        new_url = upload_player_photo(player_type, player_id, processed_bytes)
    except Exception as e:
        logger.error("Failed to upload photo to R2: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error al subir la foto. Intentalo de nuevo más tarde.",
        )

    if old_photo_url:
        try:
            delete_player_photo(old_photo_url)
        except Exception:
            logger.warning(
                "Failed to delete old photo %s after successful upload", old_photo_url
            )

    player.photo_url = new_url
    db.commit()
    db.refresh(player)
    return player


@router.delete(
    "/api/players/{player_type}/{player_id}/photo",
    response_model=PlayerResponse,
)
def delete_photo(
    player_type: Literal["s5", "s10"],
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar foto de perfil de un jugador"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    player = _get_player_by_type(db, player_type, player_id)
    _check_photo_authorization(db, current_user, player, player_type)

    if player.photo_url is None:
        raise HTTPException(status_code=404, detail="El jugador no tiene una foto")

    try:
        delete_player_photo(player.photo_url)
    except Exception:
        logger.warning(
            "Failed to delete photo %s from R2, clearing DB reference anyway",
            player.photo_url,
        )

    player.photo_url = None
    db.commit()
    db.refresh(player)
    return player
