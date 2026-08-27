from datetime import timedelta
from typing import Iterable, Tuple, Dict
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models, schemas
from app.db.models import get_argentina_now
from app.utils.auth import get_current_user


SKILL_FIELDS = (
    "velocidad",
    "resistencia",
    "control",
    "pases",
    "tiro",
    "defensa",
    "habilidad_arquero",
    "fuerza_cuerpo",
    "vision",
)


def compute_effective_skills(
    player: models.PlayerScale5 | models.PlayerScale10,
    votes: Iterable[models.SkillVote],
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float | None]]:
    base_values = {field: getattr(player, field) for field in SKILL_FIELDS}

    votes_list = list(votes)
    if not votes_list:
        return base_values, base_values, {field: None for field in SKILL_FIELDS}

    totals = {field: 0 for field in SKILL_FIELDS}
    for vote in votes_list:
        for field in SKILL_FIELDS:
            totals[field] += getattr(vote, field)

    count = len(votes_list)
    averages = {field: round(totals[field] / count, 1) for field in SKILL_FIELDS}
    return base_values, averages, averages


def get_club_members(
    club_id: int, db: Session, current_user: models.User = Depends(get_current_user)
):
    # Verificar que el club existe
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Verificar que el usuario actual es miembro del club
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == current_user.id,
        )
        .first()
    )
    if not club_user:
        raise HTTPException(status_code=403, detail="You are not a member of this club")

    # Obtener los miembros del club junto con sus usernames
    members = (
        db.query(models.ClubUser, models.User.username)
        .join(models.User, models.ClubUser.user_id == models.User.id)
        .filter(models.ClubUser.club_id == club_id)
        .all()
    )

    # Obtener los username de los usuarios invitados al club
    invited_users = (
        db.query(models.ClubInvitation, models.User.username)
        .join(models.User, models.ClubInvitation.invited_user_id == models.User.id)
        .filter(
            models.ClubInvitation.club_id == club_id,
            models.ClubInvitation.status == models.InvitationStatus.PENDING.value,
        )
        .all()
    )

    # Convertir el resultado a una lista de diccionarios
    members_list = [
        {
            "id": member.ClubUser.id,
            "club_id": member.ClubUser.club_id,
            "user_id": member.ClubUser.user_id,
            "role": member.ClubUser.role,
            "username": member.username,
        }
        for member in members
    ]

    # Agregar los usuarios invitados a la lista de miembros y ponerles member.status = "pending"
    for invitation, username in invited_users:
        members_list.append(
            {
                "id": invitation.id,
                "club_id": club_id,
                "user_id": invitation.invited_user_id,
                "role": "pending",
                "username": username,
            }
        )

    return members_list


def add_user_to_club(
    club_id: int,
    user_data: schemas.ClubUserCreate,
    db: Session,
    current_user: models.User = Depends(get_current_user),
):
    # Verificar que el club existe
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Verificar que el usuario actual tiene rol de "owner"
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == current_user.id,
        )
        .first()
    )
    if not club_user or club_user.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to add users to this club",
        )

    # Verificar que el usuario existe
    user = db.query(models.User).filter(models.User.id == user_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Crear la membresía en el club
    club_user = models.ClubUser(
        club_id=club_id, user_id=user_data.user_id, role=user_data.role
    )
    db.add(club_user)
    db.commit()
    db.refresh(club_user)
    return club_user


def remove_user_from_club(
    club_id: int,
    user_id: int,
    db: Session,
    current_user: models.User = Depends(get_current_user),
):
    # Verificar que el club existe
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Verificar que el usuario actual tiene rol de "owner"
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == current_user.id,
        )
        .first()
    )
    if not club_user or club_user.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to remove users from this club",
        )

    # Verificar que el usuario a eliminar existe
    user_to_remove = (
        db.query(models.ClubUser)
        .filter(models.ClubUser.club_id == club_id, models.ClubUser.user_id == user_id)
        .first()
    )
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found in this club")

    # Verificar que el usuario a eliminar no sea el mismo que el usuario actual
    if user_to_remove.user_id == current_user.id:
        raise HTTPException(
            status_code=403, detail="You can't remove yourself from the club"
        )

    # Eliminar al usuario del club
    db.delete(user_to_remove)
    db.commit()
    return user_to_remove


def create_club(db: Session, club: schemas.ClubCreate, user_id: int):
    # Crear el nuevo club
    new_club = models.Club(name=club.name)
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    # Agregar al creador como miembro del club con rol de "owner"
    club_user = models.ClubUser(club_id=new_club.id, user_id=user_id, role="owner")
    db.add(club_user)
    db.commit()
    db.refresh(club_user)

    return new_club


def delete_club(
    db: Session, club_id: int, current_user: models.User = Depends(get_current_user)
):
    # Verificar que el club existe
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Verificar que el usuario actual tiene rol de "owner"
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == current_user.id,
        )
        .first()
    )
    if not club_user or club_user.role != "owner":
        raise HTTPException(
            status_code=403, detail="You don't have permission to delete this club"
        )

    # Eliminar los miembros
    db.query(models.ClubUser).filter(models.ClubUser.club_id == club_id).delete()

    # Eliminar los jugadores
    db.query(models.PlayerScale5).filter(
        models.PlayerScale5.club_id == club_id
    ).delete()

    # Delete pending invitations associated with the club
    db.query(models.ClubInvitation).filter(
        models.ClubInvitation.club_id == club_id
    ).delete()

    # Eliminar el club
    db.delete(club)
    db.commit()
    return club


def invite_user_to_club(
    db: Session,
    club_id: int,
    inviter_id: int,
    invited_username: str,
    expiration_days: int = 7,
):
    # Verificar que el invitador es owner del club
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == inviter_id,
            models.ClubUser.role == "owner",
        )
        .first()
    )
    if not club_user:
        raise ValueError("No tenés permisos para invitar usuarios a este club")

    invited_username_normalized = invited_username.strip().lower()
    if not invited_username_normalized:
        raise ValueError("Usuario no encontrado")

    # Buscar al usuario invitado por username
    invited_user = (
        db.query(models.User)
        .filter(models.User.username == invited_username_normalized)
        .first()
    )
    if not invited_user:
        raise ValueError(f"Usuario {invited_username_normalized} no encontrado")

    # Verificar que el usuario no pertenezca ya al club
    existing_membership = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == invited_user.id,
        )
        .first()
    )
    if existing_membership:
        raise ValueError(f"{invited_username_normalized} ya es miembro del club")

    # Verificar si ya existe una invitación pendiente
    existing_invitation = (
        db.query(models.ClubInvitation)
        .filter(
            models.ClubInvitation.club_id == club_id,
            models.ClubInvitation.invited_user_id == invited_user.id,
            models.ClubInvitation.status == models.InvitationStatus.PENDING.value,
        )
        .first()
    )
    if existing_invitation:
        raise ValueError(
            f"Ya existe una invitación pendiente para {invited_username_normalized}"
        )

    # Crear nueva invitación
    invitation = models.ClubInvitation(
        club_id=club_id,
        invited_user_id=invited_user.id,
        inviter_id=inviter_id,
        expiration_date=get_argentina_now() + timedelta(days=expiration_days),
    )
    db.add(invitation)
    db.commit()
    return invitation


def accept_club_invitation(db: Session, invitation_id: int, user_id: int):
    invitation = (
        db.query(models.ClubInvitation)
        .filter(
            models.ClubInvitation.id == invitation_id,
            models.ClubInvitation.invited_user_id == user_id,
            models.ClubInvitation.status == models.InvitationStatus.PENDING.value,
        )
        .first()
    )

    if not invitation:
        raise ValueError("Invitación no encontrada o no válida")

    if invitation.expiration_date < get_argentina_now().replace(tzinfo=None):
        invitation.status = models.InvitationStatus.EXPIRED.value
        db.commit()
        raise ValueError("La invitación ha expirado")

    # Crear nueva membresía en el club
    club_user = models.ClubUser(
        club_id=invitation.club_id,
        user_id=user_id,
        role="member",  # Rol por defecto para nuevos miembros
    )

    invitation.status = models.InvitationStatus.ACCEPTED.value
    db.add(club_user)
    db.commit()
    return club_user


def reject_club_invitation(db: Session, invitation_id: int, user_id: int):
    invitation = (
        db.query(models.ClubInvitation)
        .filter(
            models.ClubInvitation.id == invitation_id,
            models.ClubInvitation.invited_user_id == user_id,
            models.ClubInvitation.status == models.InvitationStatus.PENDING.value,
        )
        .first()
    )

    if not invitation:
        raise ValueError("Invitación no encontrada o no válida")

    invitation.status = models.InvitationStatus.REJECTED.value
    db.commit()
    return invitation


def get_user_pending_invitations(db: Session, user_id: int):
    invitations = (
        db.query(models.ClubInvitation, models.Club.name.label("club_name"))
        .join(models.Club, models.ClubInvitation.club_id == models.Club.id)
        .filter(
            models.ClubInvitation.invited_user_id == user_id,
            models.ClubInvitation.status == models.InvitationStatus.PENDING.value,
            models.ClubInvitation.expiration_date > get_argentina_now(),
        )
        .all()
    )

    # Convert to dictionary and include club name
    return [
        {**invitation[0].__dict__, "club_name": invitation[1]}
        for invitation in invitations
    ]


def update_member_role(
    db: Session,
    club_id: int,
    user_id: int,
    role_data: str,
    current_user: models.User = Depends(get_current_user),
):
    # Verificar que el current_user es owner
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == current_user.id,
            models.ClubUser.role == "owner",
        )
        .first()
    )

    if not club_user:
        raise HTTPException(status_code=403, detail="Not authorized")

    member = (
        db.query(models.ClubUser)
        .filter(models.ClubUser.club_id == club_id, models.ClubUser.user_id == user_id)
        .first()
    )

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Verify that the at least one owner remains
    if member.role == "owner" and role_data["role"] != "owner":
        owners = (
            db.query(models.ClubUser)
            .filter(models.ClubUser.club_id == club_id, models.ClubUser.role == "owner")
            .count()
        )
        if owners == 1:
            raise HTTPException(
                status_code=400, detail="At least one owner must remain in the club"
            )

    member.role = role_data["role"]
    db.commit()
    return {"status": "success"}


def cancel_club_invitation(
    db: Session, club_id: int, invitation_id: int, current_user: models.User
):
    # Verify that the current user is club owner
    club_user = (
        db.query(models.ClubUser)
        .filter(
            models.ClubUser.club_id == club_id,
            models.ClubUser.user_id == current_user.id,
            models.ClubUser.role.in_(["owner", "admin"]),
        )
        .first()
    )

    if not club_user:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel invitations"
        )

    # Find the invitation
    invitation = (
        db.query(models.ClubInvitation)
        .filter(
            models.ClubInvitation.id == invitation_id,
            models.ClubInvitation.club_id == club_id,
            models.ClubInvitation.status == models.InvitationStatus.PENDING.value,
        )
        .first()
    )

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Cancel the invitation
    invitation.status = models.InvitationStatus.CANCELLED.value
    db.commit()
    return invitation
