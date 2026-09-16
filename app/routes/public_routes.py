import time
from collections import deque
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.db.schemas import PublicPlayerResponse
from app.utils import crud

router = APIRouter()

PUBLIC_SHARE_RATE_LIMIT = 20
PUBLIC_SHARE_RATE_WINDOW_SECONDS = 60

# In-memory per-IP request timestamps for the public share endpoint.
# Per-process only: counters reset on restart/deploy. Accepted v1 limitation.
_rate_limit_store: dict[str, deque[float]] = {}


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def check_public_share_rate_limit(request: Request) -> JSONResponse | None:
    # Returns a 429 JSONResponse when the limit is exceeded, else None.
    # A direct response (instead of raising HTTPException) is used so the
    # Retry-After header survives the app's custom exception handler,
    # which drops headers from raised HTTPExceptions.
    now = time.monotonic()
    ip = get_client_ip(request)
    hits = _rate_limit_store.setdefault(ip, deque())
    while hits and hits[0] <= now - PUBLIC_SHARE_RATE_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= PUBLIC_SHARE_RATE_LIMIT:
        retry_after = max(
            1, int(PUBLIC_SHARE_RATE_WINDOW_SECONDS - (now - hits[0])) + 1
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intentalo de nuevo más tarde."},
            headers={"Retry-After": str(retry_after)},
        )
    hits.append(now)
    return None


@router.get("/robots.txt")
async def get_robots():
    robots_path = Path("static/robots.txt")
    return FileResponse(
        robots_path, media_type="text/plain", headers={"Content-Disposition": "inline"}
    )


@router.get("/sitemap.xml")
async def get_sitemap():
    sitemap_path = Path("static/sitemap.xml")
    return FileResponse(
        sitemap_path,
        media_type="application/xml",
        headers={"Content-Disposition": "inline"},
    )


@router.get("/service-worker.js")
async def get_service_worker():
    service_worker_path = Path("static/service-worker.js")
    return FileResponse(
        service_worker_path,
        media_type="application/javascript",
        headers={
            "Content-Disposition": "inline",
            "Service-Worker-Allowed": "/",
        },
    )


@router.get("/public/players/{token}", response_model=PublicPlayerResponse)
def get_public_player(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Devolver el perfil público de solo lectura de un jugador por su share token"""
    limited = check_public_share_rate_limit(request)
    if limited is not None:
        return limited

    player, scale = crud.get_player_by_share_token(db, token)
    if player is None:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")

    votes = []
    if player.club_id is not None:
        if scale == "s10":
            votes = (
                db.query(models.SkillVote)
                .filter(
                    models.SkillVote.club_id == player.club_id,
                    models.SkillVote.player_s10_id == player.id,
                )
                .all()
            )
        else:
            votes = (
                db.query(models.SkillVote)
                .filter(
                    models.SkillVote.club_id == player.club_id,
                    models.SkillVote.player_s5_id == player.id,
                )
                .all()
            )

    _, effective, _ = crud.compute_effective_skills(player, votes)

    return {
        "name": player.name,
        "photo_url": player.photo_url,
        "scale": scale,
        **{field: round(float(effective[field]), 1) for field in crud.SKILL_FIELDS},
    }
