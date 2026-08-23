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
    get_club_user_role,
)
from app.db import models
from app.db.models import PlayerScale5, PlayerScale10, User, MatchPlayer
from app.db.schemas import PlayerCreate, PlayerResponse, PlayerSkillsWithVotes, SkillVoteCreate, SkillVoteResponse
from app.utils.auth import get_current_user
from app.utils import crud
from app.utils.time_utils import get_calendar_week_bounds

router = APIRouter()


def _ensure_club_member(db: Session, club_id: int, user_id: int) -> str:
    role = get_club_user_role(db, club_id, user_id)
    if not role:
        raise HTTPException(status_code=403, detail="No sos miembro de este club")
    return role


@router.get("/api/players")
def get_players(
    scale: str = Query("1-5", pattern="^(1-5|1-10)$"),
    club_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PlayerSkillsWithVotes]:
    """Obtener jugadores según la escala especificada"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    try:
        if club_id is not None:
            _ensure_club_member(db, club_id, current_user.id)

        players = execute_with_retries(
            query_players, db, current_user.id, club_id, scale
        )

        if not players:
            return []

        votes_by_player = {}
        if club_id is not None:
            if scale == "1-10":
                votes = (
                    db.query(models.SkillVote)
                    .filter(
                        models.SkillVote.club_id == club_id,
                        models.SkillVote.player_s10_id.in_([p.id for p in players]),
                    )
                    .all()
                )
                for vote in votes:
                    votes_by_player.setdefault(vote.player_s10_id, []).append(vote)
            else:
                votes = (
                    db.query(models.SkillVote)
                    .filter(
                        models.SkillVote.club_id == club_id,
                        models.SkillVote.player_s5_id.in_([p.id for p in players]),
                    )
                    .all()
                )
                for vote in votes:
                    votes_by_player.setdefault(vote.player_s5_id, []).append(vote)

        response_payload = []
        for player in players:
            effective, averages = crud.compute_effective_skills(
                player, votes_by_player.get(player.id, [])
            )
            response_payload.append(
                {
                    "id": player.id,
                    "name": player.name,
                    "velocidad": effective["velocidad"],
                    "resistencia": effective["resistencia"],
                    "control": effective["control"],
                    "pases": effective["pases"],
                    "tiro": effective["tiro"],
                    "defensa": effective["defensa"],
                    "habilidad_arquero": effective["habilidad_arquero"],
                    "fuerza_cuerpo": effective["fuerza_cuerpo"],
                    "vision": effective["vision"],
                    "updated_at": player.updated_at,
                    "user_id": player.user_id,
                    "club_id": player.club_id,
                    "vote_average": averages,
                }
            )

        return response_payload
    except OperationalError:
        raise HTTPException(
            status_code=500,
            detail="Error al acceder a la base de datos. Intentalo de nuevo más tarde.",
        )


@router.post(
    "/api/clubs/{club_id}/players/{player_id}/vote",
    response_model=SkillVoteResponse,
)
def vote_player_skills(
    club_id: int,
    player_id: int,
    vote_data: SkillVoteCreate,
    scale: str = Query("s5", pattern="^(s5|s10)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    _ensure_club_member(db, club_id, current_user.id)

    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club no encontrado")

    is_s10 = scale == "s10"

    if is_s10:
        player = (
            db.query(PlayerScale10)
            .filter(PlayerScale10.id == player_id, PlayerScale10.club_id == club_id)
            .first()
        )
    else:
        player = (
            db.query(PlayerScale5)
            .filter(PlayerScale5.id == player_id, PlayerScale5.club_id == club_id)
            .first()
        )

    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    if is_s10:
        if vote_data.player_s10_id not in (None, player_id) or vote_data.player_s5_id is not None:
            raise HTTPException(status_code=400, detail="Jugador invalido para la escala")
    else:
        if vote_data.player_s5_id not in (None, player_id) or vote_data.player_s10_id is not None:
            raise HTTPException(status_code=400, detail="Jugador invalido para la escala")

    vote = (
        db.query(models.SkillVote)
        .filter(
            models.SkillVote.voter_id == current_user.id,
            (models.SkillVote.player_s10_id == player_id)
            if is_s10
            else (models.SkillVote.player_s5_id == player_id),
        )
        .first()
    )

    if vote:
        current_week_start, _ = get_calendar_week_bounds()
        vote_week_start, _ = get_calendar_week_bounds(vote.updated_at)
        if vote_week_start == current_week_start:
            raise HTTPException(
                status_code=400,
                detail="Ya votaste por este jugador esta semana. Podras volver a votar el proximo lunes.",
            )
        for field in crud.SKILL_FIELDS:
            setattr(vote, field, getattr(vote_data, field))
    else:
        vote = models.SkillVote(
            club_id=club_id,
            voter_id=current_user.id,
            player_s10_id=player_id if is_s10 else None,
            player_s5_id=player_id if not is_s10 else None,
            **{field: getattr(vote_data, field) for field in crud.SKILL_FIELDS},
        )
        db.add(vote)

    db.commit()
    db.refresh(vote)
    return vote


@router.get(
    "/api/clubs/{club_id}/players/{player_id}/vote",
    response_model=SkillVoteResponse,
)
def get_player_vote(
    club_id: int,
    player_id: int,
    scale: str = Query("s5", pattern="^(s5|s10)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")

    _ensure_club_member(db, club_id, current_user.id)

    is_s10 = scale == "s10"
    vote = (
        db.query(models.SkillVote)
        .filter(
            models.SkillVote.club_id == club_id,
            models.SkillVote.voter_id == current_user.id,
            (models.SkillVote.player_s10_id == player_id)
            if is_s10
            else (models.SkillVote.player_s5_id == player_id),
        )
        .first()
    )

    if not vote:
        raise HTTPException(status_code=404, detail="Voto no encontrado")

    return vote


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
