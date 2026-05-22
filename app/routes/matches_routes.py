from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, case, func
from sqlalchemy.orm import Session, joinedload

from app.db import models, schemas
from app.db.database import get_db
from app.utils.auth import get_current_user

router = APIRouter()


def _require_auth(current_user: Optional[models.User]) -> models.User:
    if not current_user:
        raise HTTPException(status_code=401, detail="No hay un usuario autenticado")
    return current_user


def _ensure_club_member(db: Session, club_id: int, user_id: int) -> None:
    member = (
        db.query(models.ClubUser)
        .filter(models.ClubUser.club_id == club_id, models.ClubUser.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="No sos miembro de este club")


def _compute_result(team: str, team_a_score: int, team_b_score: int) -> str:
    if team_a_score == team_b_score:
        return "draw"
    if team == "A":
        return "win" if team_a_score > team_b_score else "loss"
    return "win" if team_b_score > team_a_score else "loss"


def _parse_date_param(value: Optional[str]) -> Optional[date]:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Fecha inválida")


def _serialize_match(match: models.Match) -> schemas.MatchResponse:
    players = [
        {
            "id": player.id,
            "match_id": player.match_id,
            "player_v1_id": player.player_v1_id,
            "player_v2_id": player.player_v2_id,
            "team": player.team,
            "result": player.result,
            "goals": player.goals,
            "assists": player.assists,
        }
        for player in match.match_players
    ]
    return {
        "id": match.id,
        "club_id": match.club_id,
        "created_by": match.created_by,
        "played_at": match.played_at,
        "team_a_score": match.team_a_score,
        "team_b_score": match.team_b_score,
        "notes": match.notes,
        "created_at": match.created_at,
        "players": players,
    }


def _validate_player_stats(
    players: List[schemas.MatchPlayerCreate], team_a_score: int, team_b_score: int
) -> None:
    team_a_goals = 0
    team_b_goals = 0
    team_a_assists = 0
    team_b_assists = 0

    for player in players:
        if player.team == "A":
            team_a_goals += player.goals
            team_a_assists += player.assists
        elif player.team == "B":
            team_b_goals += player.goals
            team_b_assists += player.assists

    if team_a_goals > team_a_score:
        raise HTTPException(
            status_code=400,
            detail="Los goles del Equipo A no pueden superar el marcador",
        )
    if team_b_goals > team_b_score:
        raise HTTPException(
            status_code=400,
            detail="Los goles del Equipo B no pueden superar el marcador",
        )
    if team_a_assists > team_a_score:
        raise HTTPException(
            status_code=400,
            detail="Las asistencias del Equipo A no pueden superar el marcador",
        )
    if team_b_assists > team_b_score:
        raise HTTPException(
            status_code=400,
            detail="Las asistencias del Equipo B no pueden superar el marcador",
        )


@router.post("/matches", response_model=schemas.MatchResponse)
async def create_match(
    match_data: schemas.MatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user = _require_auth(current_user)

    if match_data.club_id is not None:
        _ensure_club_member(db, match_data.club_id, current_user.id)

    if not match_data.players:
        raise HTTPException(status_code=400, detail="Debes incluir jugadores")

    _validate_player_stats(
        match_data.players, match_data.team_a_score, match_data.team_b_score
    )

    match = models.Match(
        club_id=match_data.club_id,
        created_by=current_user.id,
        played_at=match_data.played_at,
        team_a_score=match_data.team_a_score,
        team_b_score=match_data.team_b_score,
        notes=match_data.notes,
    )
    db.add(match)
    db.flush()

    match_players: List[models.MatchPlayer] = []
    for player_entry in match_data.players:
        has_v1 = player_entry.player_v1_id is not None
        has_v2 = player_entry.player_v2_id is not None
        if has_v1 == has_v2:
            raise HTTPException(
                status_code=400,
                detail="Debes enviar exactamente un player_v1_id o player_v2_id",
            )

        if has_v1:
            player = (
                db.query(models.PlayerScale5)
                .filter(models.PlayerScale5.id == player_entry.player_v1_id)
                .first()
            )
        else:
            player = (
                db.query(models.PlayerScale10)
                .filter(models.PlayerScale10.id == player_entry.player_v2_id)
                .first()
            )

        if not player:
            raise HTTPException(status_code=404, detail="Jugador no encontrado")

        result = _compute_result(
            player_entry.team, match_data.team_a_score, match_data.team_b_score
        )
        match_players.append(
            models.MatchPlayer(
                match_id=match.id,
                player_v1_id=player_entry.player_v1_id,
                player_v2_id=player_entry.player_v2_id,
                team=player_entry.team,
                result=result,
                goals=player_entry.goals,
                assists=player_entry.assists,
            )
        )

    db.add_all(match_players)
    db.commit()

    match = (
        db.query(models.Match)
        .options(joinedload(models.Match.match_players))
        .filter(models.Match.id == match.id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=500, detail="Error al crear el partido")

    return _serialize_match(match)


@router.get("/matches", response_model=List[schemas.MatchResponse])
def list_matches(
    club_id: Optional[int] = Query(None),
    player_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user = _require_auth(current_user)

    start_dt = _parse_date_param(start_date)
    end_dt = _parse_date_param(end_date)
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=400, detail="Rango de fechas inválido")

    query = db.query(models.Match).options(joinedload(models.Match.match_players))

    if club_id is not None:
        _ensure_club_member(db, club_id, current_user.id)
        query = query.filter(models.Match.club_id == club_id)
    else:
        query = query.filter(
            models.Match.club_id.is_(None),
            models.Match.created_by == current_user.id,
        )

    if player_id is not None:
        query = (
            query.join(models.Match.match_players)
            .filter(
                or_(
                    models.MatchPlayer.player_v1_id == player_id,
                    models.MatchPlayer.player_v2_id == player_id,
                )
            )
            .distinct()
        )

    if start_dt is not None:
        query = query.filter(models.Match.played_at >= start_dt)
    if end_dt is not None:
        query = query.filter(models.Match.played_at <= end_dt)

    matches = query.order_by(models.Match.played_at.desc()).all()
    return [_serialize_match(match) for match in matches]


@router.get("/matches/standings", response_model=List[schemas.MatchStandingResponse])
async def get_match_standings(
    version: str = Query(..., pattern="^(v1|v2)$"),
    club_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user = _require_auth(current_user)

    start_dt = _parse_date_param(start_date)
    end_dt = _parse_date_param(end_date)
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=400, detail="Rango de fechas inválido")

    if club_id is not None:
        _ensure_club_member(db, club_id, current_user.id)

    win_count = func.sum(case((models.MatchPlayer.result == "win", 1), else_=0))
    draw_count = func.sum(case((models.MatchPlayer.result == "draw", 1), else_=0))
    loss_count = func.sum(case((models.MatchPlayer.result == "loss", 1), else_=0))
    goals_sum = func.sum(models.MatchPlayer.goals)
    assists_sum = func.sum(models.MatchPlayer.assists)

    if version == "v1":
        query = (
            db.query(
                models.PlayerScale5.id.label("player_id"),
                models.PlayerScale5.name.label("player_name"),
                func.count(models.MatchPlayer.id).label("played"),
                win_count.label("wins"),
                draw_count.label("draws"),
                loss_count.label("losses"),
                goals_sum.label("goals"),
                assists_sum.label("assists"),
                func.max(models.Match.played_at).label("last_match"),
            )
            .join(
                models.MatchPlayer,
                models.MatchPlayer.player_v1_id == models.PlayerScale5.id,
            )
            .join(models.Match, models.Match.id == models.MatchPlayer.match_id)
        )
    else:
        query = (
            db.query(
                models.PlayerScale10.id.label("player_id"),
                models.PlayerScale10.name.label("player_name"),
                func.count(models.MatchPlayer.id).label("played"),
                win_count.label("wins"),
                draw_count.label("draws"),
                loss_count.label("losses"),
                goals_sum.label("goals"),
                assists_sum.label("assists"),
                func.max(models.Match.played_at).label("last_match"),
            )
            .join(
                models.MatchPlayer,
                models.MatchPlayer.player_v2_id == models.PlayerScale10.id,
            )
            .join(models.Match, models.Match.id == models.MatchPlayer.match_id)
        )

    if club_id is not None:
        query = query.filter(models.Match.club_id == club_id)
    else:
        query = query.filter(
            models.Match.club_id.is_(None),
            models.Match.created_by == current_user.id,
        )

    if start_dt is not None:
        query = query.filter(models.Match.played_at >= start_dt)
    if end_dt is not None:
        query = query.filter(models.Match.played_at <= end_dt)

    rows = query.group_by("player_id", "player_name").all()

    standings = []
    for row in rows:
        points = (row.wins or 0) * 3 + (row.draws or 0)
        standings.append(
            {
                "player_id": row.player_id,
                "player_name": row.player_name,
                "points": points,
                "played": row.played,
                "wins": row.wins or 0,
                "draws": row.draws or 0,
                "losses": row.losses or 0,
                "goals": row.goals or 0,
                "assists": row.assists or 0,
                "last_match": row.last_match,
            }
        )

    standings.sort(
        key=lambda item: (
            item["points"],
            item["wins"],
            item["goals"],
            item["assists"],
            -(item["played"] or 0),
            item["last_match"] or date.min,
        ),
        reverse=True,
    )

    return standings


@router.get("/matches/{match_id}", response_model=schemas.MatchResponse)
async def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user = _require_auth(current_user)

    match = (
        db.query(models.Match)
        .options(joinedload(models.Match.match_players))
        .filter(models.Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if match.club_id is not None:
        _ensure_club_member(db, match.club_id, current_user.id)
    elif match.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    return _serialize_match(match)


@router.patch("/matches/{match_id}", response_model=schemas.MatchResponse)
async def update_match(
    match_id: int,
    match_data: schemas.MatchUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user = _require_auth(current_user)

    match = (
        db.query(models.Match)
        .options(joinedload(models.Match.match_players))
        .filter(models.Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if match.club_id is not None:
        _ensure_club_member(db, match.club_id, current_user.id)
    elif match.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    if match_data.players is not None and not match_data.players:
        raise HTTPException(status_code=400, detail="Debes incluir jugadores")

    played_at = match_data.played_at or match.played_at
    team_a_score = (
        match_data.team_a_score
        if match_data.team_a_score is not None
        else match.team_a_score
    )
    team_b_score = (
        match_data.team_b_score
        if match_data.team_b_score is not None
        else match.team_b_score
    )

    match.played_at = played_at
    match.team_a_score = team_a_score
    match.team_b_score = team_b_score
    if "notes" in match_data.model_fields_set:
        match.notes = match_data.notes

    if match_data.players is not None:
        _validate_player_stats(match_data.players, team_a_score, team_b_score)
        for existing in match.match_players:
            db.delete(existing)
        db.flush()

        match_players: List[models.MatchPlayer] = []
        for player_entry in match_data.players:
            has_v1 = player_entry.player_v1_id is not None
            has_v2 = player_entry.player_v2_id is not None
            if has_v1 == has_v2:
                raise HTTPException(
                    status_code=400,
                    detail="Debes enviar exactamente un player_v1_id o player_v2_id",
                )

            if has_v1:
                player = (
                    db.query(models.PlayerScale5)
                    .filter(models.PlayerScale5.id == player_entry.player_v1_id)
                    .first()
                )
            else:
                player = (
                    db.query(models.PlayerScale10)
                    .filter(models.PlayerScale10.id == player_entry.player_v2_id)
                    .first()
                )

            if not player:
                raise HTTPException(status_code=404, detail="Jugador no encontrado")

            result = _compute_result(player_entry.team, team_a_score, team_b_score)
            match_players.append(
                models.MatchPlayer(
                    match_id=match.id,
                    player_v1_id=player_entry.player_v1_id,
                    player_v2_id=player_entry.player_v2_id,
                    team=player_entry.team,
                    result=result,
                    goals=player_entry.goals,
                    assists=player_entry.assists,
                )
            )

        db.add_all(match_players)
    else:
        for player in match.match_players:
            player.result = _compute_result(player.team, team_a_score, team_b_score)

    db.commit()

    match = (
        db.query(models.Match)
        .options(joinedload(models.Match.match_players))
        .filter(models.Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=500, detail="Error al actualizar el partido")

    return _serialize_match(match)


@router.delete("/matches/{match_id}")
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user = _require_auth(current_user)

    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if match.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    db.delete(match)
    db.commit()
    return {"status": "deleted"}
