from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.config.config import templates
from app.db.database import get_db
from app.db.database_utils import execute_with_retries, query_user
from app.db.models import User
from app.utils.security import create_access_token, create_email_confirmation_token
from app.utils.validators import validate_password, validate_username, validate_email
from app.utils.email_service import EmailService, PasswordResetService


router = APIRouter()


@router.get("/signup", response_class=HTMLResponse, include_in_schema=False)
async def signup_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/home", status_code=302)
    return templates.TemplateResponse(request=request, name="signup.html")


@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip().lower()
    email = email.strip().lower()

    # Validar nombre de usuario, contraseña y email
    try:
        validate_username(username)
        validate_email(email)

        # Check if username already exists
        user = execute_with_retries(query_user, db, username)
        if user:
            return templates.TemplateResponse(
                request=request,
                name="signup.html",
                context={"error": "Usuario ya registrado"},
                status_code=409,
            )

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return templates.TemplateResponse(
                request=request,
                name="signup.html",
                context={"error": "Email ya registrado"},
                status_code=409,
            )
        validate_password(password)
    except ValueError as e:
        return templates.TemplateResponse(
            request=request, name="signup.html", context={"error": str(e)}
        )
    except OperationalError:
        return HTMLResponse(
            "Error al acceder a la base de datos. Inténtalo de nuevo más tarde.",
            status_code=500,
        )

    new_user = User(
        username=username, email=email, email_confirmed=0
    )  # 0 = nuevo usuario sin confirmar
    new_user.set_password(password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate email confirmation token
    confirmation_token = create_email_confirmation_token(db, new_user)

    # Send confirmation email
    email_service = EmailService()
    email_sent = email_service.send_email_confirmation(
        email, confirmation_token, username
    )
    if not email_sent:
        # If email fails, we still create the account but show a warning
        return templates.TemplateResponse(
            request=request,
            name="email_confirmation_pending.html",
            context={
                "user_email": email,
                "error": "Cuenta creada, pero hubo un problema enviando el email de confirmación. Intenta reenviar el email.",
            },
        )
    # Redirect to confirmation pending page
    return templates.TemplateResponse(
        request=request,
        name="email_confirmation_pending.html",
        context={"user_email": email},
    )


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    referer = request.headers.get("referer")
    if referer and "logout" in referer:
        request.session.clear()
    if request.session.get("user_id"):
        return RedirectResponse(url="/home", status_code=302)

    # Check if account was deleted
    deleted = request.query_params.get("deleted") == "true"
    context = {"deleted": deleted} if deleted else {}

    return templates.TemplateResponse(
        request=request, name="login.html", context=context
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip().lower()

    try:
        user: User = execute_with_retries(query_user, db, username)
    except OperationalError:
        return HTMLResponse(
            "Error al acceder a la base de datos. Inténtalo de nuevo más tarde.",
            status_code=500,
        )

    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Usuario o contraseña incorrectos"},
            status_code=401,
        )
    # Check if email confirmation is required (only for new users with email but unconfirmed)
    if (
        user.is_new_user() and user.email
    ):  # Only block if user has email but hasn't confirmed it
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Debes confirmar tu email antes de iniciar sesión. Revisa tu bandeja de entrada.",
                "email_not_confirmed": True,
                "user_email": user.email,
            },
            status_code=401,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/home", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=307)


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=15)

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


# Password reset routes
@router.get("/forgot-password", response_class=HTMLResponse, include_in_schema=False)
async def forgot_password_page(request: Request):
    """Display forgot password form"""
    if request.session.get("user_id"):
        return RedirectResponse(url="/home", status_code=302)
    return templates.TemplateResponse(request=request, name="forgot_password.html")


@router.post("/forgot-password")
async def forgot_password(
    request: Request, email: str = Form(...), db: Session = Depends(get_db)
):
    """Process forgot password request"""
    try:
        validate_email(email)
        # Find user by email
        user = db.query(User).filter(User.email == email.lower().strip()).first()

        if (
            user and user.is_email_confirmed()
        ):  # Solo permite reset si el email está confirmado
            # Generate reset token
            reset_token = PasswordResetService.create_reset_token(db, user.id)

            # Send email
            email_service = EmailService()
            email_sent = email_service.send_password_reset_email(
                to_email=user.email, reset_token=reset_token, username=user.username
            )

            if not email_sent:
                return templates.TemplateResponse(
                    request=request,
                    name="forgot_password.html",
                    context={
                        "error": "Error al enviar el email. Inténtalo de nuevo más tarde."
                    },
                )

        # Always show success message for security (don't reveal if email exists)
        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "success": "Si el email existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña."
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            request=request, name="forgot_password.html", context={"error": str(e)}
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={"error": "Error interno. Inténtalo de nuevo más tarde."},
        )


@router.get(
    "/reset-password/{token}", response_class=HTMLResponse, include_in_schema=False
)
async def reset_password_page(
    request: Request, token: str, db: Session = Depends(get_db)
):
    """Display reset password form"""
    if request.session.get("user_id"):
        return RedirectResponse(url="/home", status_code=302)

    # Validate token
    user = PasswordResetService.validate_reset_token(db, token)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "El enlace de restablecimiento no es válido o ha expirado.",
                "invalid_token": True,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={"token": token, "username": user.username},
    )


@router.post("/reset-password/{token}")
async def reset_password(
    request: Request,
    token: str,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process password reset"""
    try:
        # Validate passwords match
        if new_password != confirm_password:
            raise ValueError("Las contraseñas no coinciden.")

        # Validate password strength
        validate_password(new_password)

        # Validate token and get user
        user = PasswordResetService.validate_reset_token(db, token)
        if not user:
            return templates.TemplateResponse(
                request=request,
                name="reset_password.html",
                context={
                    "error": "El enlace de restablecimiento no es válido o ha expirado.",
                    "invalid_token": True,
                },
            )

        # Update password
        user.set_password(new_password)

        # Mark token as used
        PasswordResetService.use_reset_token(db, token)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "success": "Tu contraseña ha sido restablecida exitosamente. Ahora puedes iniciar sesión.",
                "password_reset": True,
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={"error": str(e), "token": token},
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Error interno. Inténtalo de nuevo más tarde.",
                "token": token,
            },
        )


# Profile management routes
@router.get("/perfil", response_class=HTMLResponse, include_in_schema=False)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    """Display user profile page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        request=request, name="profile.html", context={"user": user}
    )


@router.post("/perfil/update-email")
async def update_email(
    request: Request, email: str = Form(...), db: Session = Depends(get_db)
):
    """Update user email address with confirmation requirement"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    try:
        email = email.strip().lower()
        validate_email(email)

        # Check if email already exists for another user
        existing_email = (
            db.query(User).filter(User.email == email, User.id != user_id).first()
        )
        if existing_email:
            return templates.TemplateResponse(
                request=request,
                name="profile.html",
                context={
                    "user": user,
                    "error": "Este email ya está registrado por otro usuario.",
                },
            )

        # Check if it's the same email they already have
        if user.email == email:
            return templates.TemplateResponse(
                request=request,
                name="profile.html",
                context={
                    "user": user,
                    "error": "Este email ya está asociado a tu cuenta.",
                },
            )
        # Set email as unconfirmed for legacy users and generate confirmation token
        user.email = email
        user.email_confirmed = (
            -1
        )  # -1 = usuario legacy con email sin confirmar (puede hacer login)
        db.commit()
        db.refresh(user)

        # Generate confirmation token
        confirmation_token = create_email_confirmation_token(db, user)

        # Send confirmation email
        email_service = EmailService()
        email_sent = email_service.send_email_confirmation(
            email, confirmation_token, user.username
        )

        if not email_sent:
            return templates.TemplateResponse(
                request=request,
                name="profile.html",
                context={
                    "user": user,
                    "error": "Email actualizado pero hubo un problema enviando la confirmación. Puedes reenviar el email desde tu perfil.",
                },
            )

        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "success": "Email actualizado. Te hemos enviado un enlace de confirmación al nuevo email.",
                "email_pending_confirmation": True,
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={"user": user, "error": str(e)},
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": "Error interno. Inténtalo de nuevo más tarde.",
            },
        )


@router.post("/perfil/delete-account")
async def delete_account(request: Request, db: Session = Depends(get_db)):
    """Delete user account and all related data"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    try:
        # Import models here to avoid circular imports
        from app.db.models import (
            PasswordResetToken,
            Player,
            PlayerV2,
            ClubUser,
            Club,
            SkillVote,
            SkillVoteV2,
            ClubInvitation,
        )

        # 0. Clear last_modified_by references in both Player and PlayerV2 tables
        # (for players this user modified but doesn't own)
        db.query(Player).filter(Player.last_modified_by == user_id).update(
            {"last_modified_by": None}
        )
        db.query(PlayerV2).filter(PlayerV2.last_modified_by == user_id).update(
            {"last_modified_by": None}
        )

        # 1. Delete all players created by this user (legacy Player table)
        user_players = db.query(Player).filter(Player.user_id == user_id).all()
        for player in user_players:
            # Delete skill votes for this player first (foreign key constraint)
            db.query(SkillVote).filter(SkillVote.player_id == player.id).delete()
            # Delete the player
            db.delete(player)

        # 1b. Delete all players created by this user (PlayerV2 table)
        user_players_v2 = db.query(PlayerV2).filter(PlayerV2.user_id == user_id).all()
        for player in user_players_v2:
            # Delete skill votes for this player first (foreign key constraint)
            db.query(SkillVoteV2).filter(SkillVoteV2.player_id == player.id).delete()
            # Delete the player
            db.delete(player)

        # 2. Delete all skill votes made by this user (as voter)
        db.query(SkillVote).filter(SkillVote.voter_id == user_id).delete()
        db.query(SkillVoteV2).filter(SkillVoteV2.voter_id == user_id).delete()

        # 3. Handle club memberships
        user_club_memberships = (
            db.query(ClubUser).filter(ClubUser.user_id == user_id).all()
        )

        for membership in user_club_memberships:
            club_id = membership.club_id

            if membership.role == "owner":
                # Check if there are other owners in this club
                other_owners = (
                    db.query(ClubUser)
                    .filter(
                        ClubUser.club_id == club_id,
                        ClubUser.role == "owner",
                        ClubUser.user_id != user_id,
                    )
                    .count()
                )

                if other_owners > 0:
                    # There are other owners, just remove this user from the club
                    db.delete(membership)
                else:
                    # This user is the only owner, delete the entire club
                    # First delete all related data for this club

                    # Delete all club invitations
                    db.query(ClubInvitation).filter(
                        ClubInvitation.club_id == club_id
                    ).delete()

                    # Delete all skill votes for players in this club
                    club_players = (
                        db.query(Player).filter(Player.club_id == club_id).all()
                    )
                    for player in club_players:
                        db.query(SkillVote).filter(
                            SkillVote.player_id == player.id
                        ).delete()

                    # Delete all club players (set club_id to None, they become personal players)
                    db.query(Player).filter(Player.club_id == club_id).update(
                        {"club_id": None}
                    )

                    # Delete all club members
                    db.query(ClubUser).filter(ClubUser.club_id == club_id).delete()

                    # Delete the club itself
                    club = db.query(Club).filter(Club.id == club_id).first()
                    if club:
                        db.delete(club)
            else:
                # User is admin or member, just remove from club
                db.delete(membership)

        # 4. Delete invitations sent by this user
        db.query(ClubInvitation).filter(ClubInvitation.inviter_id == user_id).delete()

        # 5. Delete invitations received by this user
        db.query(ClubInvitation).filter(
            ClubInvitation.invited_user_id == user_id
        ).delete()

        # 6. Delete password reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id
        ).delete()

        # 7. Finally, delete the user account
        db.delete(user)
        db.commit()

        # Clear session
        request.session.clear()

        # Redirect to login with a message
        return RedirectResponse(url="/login?deleted=true", status_code=302)

    except Exception as e:
        db.rollback()
        import logging

        logging.error(f"Error deleting account for user_id {user_id}: {str(e)}")
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": "Error al borrar la cuenta. Inténtalo de nuevo más tarde.",
            },
        )


# Email confirmation routes
@router.get(
    "/confirm-email/{token}", response_class=HTMLResponse, include_in_schema=False
)
async def confirm_email(request: Request, token: str, db: Session = Depends(get_db)):
    """Confirm user email with token"""
    from app.utils.security import validate_email_confirmation_token, confirm_user_email

    # Validate token and get user
    user = validate_email_confirmation_token(db, token)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error": "El enlace de confirmación no es válido o ha expirado.",
                "invalid_token": True,
            },
        )

    # Confirm email
    success = confirm_user_email(db, user)
    if not success:
        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error": "Error al confirmar el email. Inténtalo de nuevo más tarde.",
                "confirmation_failed": True,
            },
        )
    # Auto-login the user after successful confirmation
    request.session["user_id"] = user.id

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "success": "¡Email confirmado exitosamente! Ya puedes usar tu cuenta."
        },
    )


@router.post("/resend-confirmation")
async def resend_confirmation(
    request: Request, email: str = Form(...), db: Session = Depends(get_db)
):
    """Resend email confirmation"""
    from app.utils.security import create_email_confirmation_token

    try:
        email = email.strip().lower()
        validate_email(email)

        # Find user with this email (any unconfirmed state)
        user = (
            db.query(User)
            .filter(User.email == email, User.email_confirmed.in_([0, -1]))
            .first()
        )

        if user:
            # Generate new confirmation token
            confirmation_token = create_email_confirmation_token(db, user)

            # Send confirmation email
            email_service = EmailService()
            email_sent = email_service.send_email_confirmation(
                email, confirmation_token, user.username
            )
            if not email_sent:
                return templates.TemplateResponse(
                    request=request,
                    name="email_confirmation_pending.html",
                    context={
                        "error": "Error al enviar el email. Inténtalo de nuevo más tarde.",
                        "user_email": email,
                    },
                )
        # Always show success message for security (don't reveal if email exists)
        return templates.TemplateResponse(
            request=request,
            name="email_confirmation_pending.html",
            context={
                "success": "Si el email existe y no está confirmado, recibirás un nuevo enlace de confirmación.",
                "user_email": email,
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="email_confirmation_pending.html",
            context={"error": str(e), "user_email": email},
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="email_confirmation_pending.html",
            context={
                "error": "Error interno. Inténtalo de nuevo más tarde.",
                "user_email": email,
            },
        )


@router.post("/perfil/resend-email-confirmation")
async def resend_email_confirmation_profile(
    request: Request, db: Session = Depends(get_db)
):
    """Resend email confirmation from profile page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    # Check if user has email and it's not confirmed
    if not user.email:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": "No tienes un email configurado para confirmar.",
            },
        )
    if user.is_email_confirmed():
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={"user": user, "error": "Tu email ya está confirmado."},
        )

    try:
        # Generate new confirmation token
        confirmation_token = create_email_confirmation_token(db, user)

        # Send confirmation email
        email_service = EmailService()
        email_sent = email_service.send_email_confirmation(
            user.email, confirmation_token, user.username
        )

        if not email_sent:
            return templates.TemplateResponse(
                request=request,
                name="profile.html",
                context={
                    "user": user,
                    "error": "Error al enviar el email de confirmación. Intentalo de nuevo más tarde.",
                },
            )

        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "success": "Email de confirmación reenviado exitosamente.",
                "email_pending_confirmation": True,
            },
        )

    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": "Error interno. Inténtalo de nuevo más tarde.",
            },
        )
