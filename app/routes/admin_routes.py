from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.config import templates
from app.config.settings import Settings
from app.db.database import get_db
from app.db.models import User
from app.utils.auth import get_current_user
from app.utils.security import verify_admin_user
from app.config.logging_config import logger

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_admin_user(current_user, detail="Unauthorized access.")

    try:
        # Consultas para estadísticas completas
        with db.connection() as conn:
            # Estadísticas básicas
            total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            users_with_players = conn.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM players")
            ).scalar()
            users_in_clubs = conn.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM club_users")
            ).scalar()
            total_clubs = conn.execute(text("SELECT COUNT(*) FROM clubs")).scalar()
            total_players = conn.execute(text("SELECT COUNT(*) FROM players")).scalar()

            # Promedio de jugadores por usuario (solo usuarios activos)
            avg_players_per_user = (
                round(total_players / users_with_players, 1)
                if users_with_players > 0
                else 0
            )

            # Promedio de usuarios por club
            avg_users_per_club = (
                conn.execute(
                    text("""
                    SELECT AVG(user_count) 
                    FROM (
                        SELECT COUNT(*) as user_count 
                        FROM club_users 
                        GROUP BY club_id
                    )
                """)
                ).scalar()
                or 0
            )
            avg_users_per_club = (
                float(round(avg_users_per_club, 1)) if avg_users_per_club else 0
            )

            date_24h = "NOW() - INTERVAL '1 day'"
            date_7d = "NOW() - INTERVAL '7 days'"
            date_30d = "NOW() - INTERVAL '1 month'"

            # Usuarios nuevos en diferentes períodos
            new_users_24h = conn.execute(
                text(f"""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= {date_24h}
                """)
            ).scalar()

            new_users_week = conn.execute(
                text(f"""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= {date_7d}
                """)
            ).scalar()

            new_users_month = conn.execute(
                text(f"""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= {date_30d}
                """)
            ).scalar()

            # Clubes nuevos en diferentes períodos
            new_clubs_24h = conn.execute(
                text(f"""
                    SELECT COUNT(*) FROM clubs 
                    WHERE creation_date >= {date_24h}
                """)
            ).scalar()

            new_clubs_week = conn.execute(
                text(f"""
                    SELECT COUNT(*) FROM clubs 
                    WHERE creation_date >= {date_7d}
                """)
            ).scalar()

            new_clubs_month = conn.execute(
                text(f"""
                    SELECT COUNT(*) FROM clubs 
                    WHERE creation_date >= {date_30d}
                """)
            ).scalar()

            # Calcular usuarios activos (que han creado jugadores en v1 o v2, O están en clubes)
            active_users = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT user_id) FROM (
                        SELECT user_id FROM players
                        UNION
                        SELECT user_id FROM players_v2
                        UNION
                        SELECT user_id FROM club_users
                    ) AS active_users_combined
                """)
            ).scalar()

            # Tasa de abandono: usuarios que nunca crearon jugador NI están en clubs
            abandoned_users = total_users - active_users
            abandonment_rate = (
                round((abandoned_users / total_users) * 100, 1)
                if total_users > 0
                else 0
            )

            # Helper para contar usuarios con actividad reciente (edición de jugadores)
            def count_recently_active_users(date_expr: str) -> int:
                return conn.execute(
                    text(f"""
                        SELECT COUNT(DISTINCT user_id) FROM (
                            SELECT user_id FROM players WHERE updated_at >= {date_expr}
                            UNION
                            SELECT user_id FROM players_v2 WHERE updated_at >= {date_expr}
                        ) AS recently_active_users
                    """)
                ).scalar()

            # Usuarios con actividad reciente (edición de jugadores) en últimos 24h, 7 y 30 días
            active_users_24h = count_recently_active_users(date_24h)
            active_users_7d = count_recently_active_users(date_7d)
            active_users_30d = count_recently_active_users(date_30d)

            # Invitaciones: pendientes, aceptadas, rechazadas
            pending_invitations = conn.execute(
                text("SELECT COUNT(*) FROM club_invitations WHERE status = 'pending'")
            ).scalar()

            accepted_invitations = conn.execute(
                text("SELECT COUNT(*) FROM club_invitations WHERE status = 'accepted'")
            ).scalar()

            rejected_invitations = conn.execute(
                text("SELECT COUNT(*) FROM club_invitations WHERE status = 'rejected'")
            ).scalar()

            total_invitations = (
                pending_invitations + accepted_invitations + rejected_invitations
            )
            invitation_acceptance_rate = (
                round((accepted_invitations / total_invitations) * 100, 1)
                if total_invitations > 0
                else 0
            )

            # Tasa de confirmación de email (columna integer en ambos motores)
            users_email_confirmed = conn.execute(
                text("SELECT COUNT(*) FROM users WHERE email_confirmed = 1")
            ).scalar()

            email_confirmation_rate = (
                round((users_email_confirmed / total_users) * 100, 1)
                if total_users > 0
                else 0
            )

            # Resets de contraseña
            total_password_resets = conn.execute(
                text("SELECT COUNT(*) FROM password_reset_tokens")
            ).scalar()

            # Usuarios que han usado reset
            users_with_reset = conn.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM password_reset_tokens")
            ).scalar()

            # Usuarios en V1 vs V2 (usando NOT EXISTS para evitar problemas con NULL)
            users_v1_only = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT p.user_id) FROM players p
                    WHERE NOT EXISTS (SELECT 1 FROM players_v2 p2 WHERE p2.user_id = p.user_id)
                """)
            ).scalar()

            users_v2_only = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT p2.user_id) FROM players_v2 p2
                    WHERE NOT EXISTS (SELECT 1 FROM players p WHERE p.user_id = p2.user_id)
                """)
            ).scalar()

            users_both_versions = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT p.user_id) FROM players p
                    WHERE EXISTS (SELECT 1 FROM players_v2 p2 WHERE p2.user_id = p.user_id)
                """)
            ).scalar()

            total_players_v1 = conn.execute(
                text("SELECT COUNT(*) FROM players")
            ).scalar()

            total_players_v2 = conn.execute(
                text("SELECT COUNT(*) FROM players_v2")
            ).scalar()

            # Jugadores en clubs vs sin club (ambas versiones)
            players_in_clubs = conn.execute(
                text("""
                    SELECT COUNT(*) FROM (
                        SELECT id FROM players WHERE club_id IS NOT NULL
                        UNION ALL
                        SELECT id FROM players_v2 WHERE club_id IS NOT NULL
                    ) AS combined_players
                """)
            ).scalar()

            players_without_club = conn.execute(
                text("""
                    SELECT COUNT(*) FROM (
                        SELECT id FROM players WHERE club_id IS NULL
                        UNION ALL
                        SELECT id FROM players_v2 WHERE club_id IS NULL
                    ) AS combined_players
                """)
            ).scalar()

        # Tasas de engagement
        engagement_rate = (
            round((active_users / total_users) * 100, 1) if total_users > 0 else 0
        )
        player_creation_rate = (
            round((users_with_players / total_users) * 100, 1) if total_users > 0 else 0
        )
        club_participation_rate = (
            round((users_in_clubs / total_users) * 100, 1) if total_users > 0 else 0
        )

        # Preparar datos para la plantilla
        stats = {
            "total_users": total_users,
            "users_with_players": users_with_players,
            "users_in_clubs": users_in_clubs,
            "total_clubs": total_clubs,
            "active_users": active_users,
            "engagement_rate": engagement_rate,
            "player_creation_rate": player_creation_rate,
            "club_participation_rate": club_participation_rate,
            "new_clubs_24h": new_clubs_24h,
            "new_clubs_week": new_clubs_week,
            "new_clubs_month": new_clubs_month,
            "avg_players_per_user": avg_players_per_user,
            "avg_users_per_club": avg_users_per_club,
            "new_users_24h": new_users_24h,
            "new_users_week": new_users_week,
            "new_users_month": new_users_month,
            "abandoned_users": abandoned_users,
            "abandonment_rate": abandonment_rate,
            "active_users_24h": active_users_24h,
            "active_users_7d": active_users_7d,
            "active_users_30d": active_users_30d,
            "pending_invitations": pending_invitations,
            "accepted_invitations": accepted_invitations,
            "rejected_invitations": rejected_invitations,
            "invitation_acceptance_rate": invitation_acceptance_rate,
            "users_email_confirmed": users_email_confirmed,
            "email_confirmation_rate": email_confirmation_rate,
            "total_password_resets": total_password_resets,
            "users_with_reset": users_with_reset,
            "users_v1_only": users_v1_only,
            "users_v2_only": users_v2_only,
            "users_both_versions": users_both_versions,
            "total_players_v1": total_players_v1,
            "total_players_v2": total_players_v2,
            "players_in_clubs": players_in_clubs,
            "players_without_club": players_without_club,
        }

        return templates.TemplateResponse(
            request=request, name="admin_dashboard.html", context={"stats": stats}
        )
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error loading dashboard: {str(e)}"
        )


# Token secreto para proteger el endpoint
CRON_SECRET = Settings().cron_secret


def verify_cron_token(x_cron_token: str = Header(None)):
    if not CRON_SECRET or x_cron_token != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


@router.post("/cleanup-expired-users")
async def cleanup_expired_users(
    db: Session = Depends(get_db), _: bool = Depends(verify_cron_token)
):
    """
    Elimina usuarios no confirmados cuya fecha de expiración ya pasó.
    Este endpoint debe ser llamado por un cron job externo.
    """
    try:
        now = datetime.now(timezone.utc)

        # Buscar usuarios nuevos (email_confirmed=0, con email y token expirado)
        # No elimina usuarios legacy sin email
        expired_users = (
            db.query(User)
            .filter(
                User.email_confirmed == 0,
                User.email.isnot(None),
                User.email_confirmation_expires < now,
            )
            .all()
        )

        deleted_count = len(expired_users)

        for user in expired_users:
            db.delete(user)

        db.commit()

        logger.info(f"Cleanup completed: {deleted_count} expired users deleted")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "timestamp": now.isoformat(),
        }

    except Exception:
        db.rollback()
        logger.exception("Error during cleanup")
        raise HTTPException(status_code=500, detail="Internal server error")
