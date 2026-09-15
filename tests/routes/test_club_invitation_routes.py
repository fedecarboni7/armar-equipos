from app.db import models
from app.utils.email_service import EmailService


def _create_club_and_invited_user(db, invited_email):
    owner = db.query(models.User).filter(models.User.username == "testuser").first()
    invited_user = models.User(
        username="club_invited_user",
        email=invited_email,
        email_confirmed=1,
    )
    invited_user.set_password("Testpassword1*")
    club = models.Club(name="Invitation Test Club")
    db.add_all([invited_user, club])
    db.commit()
    db.add(models.ClubUser(club_id=club.id, user_id=owner.id, role="owner"))
    db.commit()
    return owner, invited_user, club


def test_invitation_sends_email_to_invited_user_with_inviter_cc(
    authenticated_client, db, monkeypatch
):
    _, invited_user, club = _create_club_and_invited_user(db, "invited@example.com")
    sent_email = {}

    def fake_send(self, **kwargs):
        sent_email.update(kwargs)
        return True

    monkeypatch.setattr(EmailService, "send_club_invitation_email", fake_send)

    response = authenticated_client.post(
        f"/clubs/{club.id}/invite",
        json={"invited_username": invited_user.username},
    )

    assert response.status_code == 200
    assert sent_email["to_email"] == invited_user.email
    assert sent_email["cc_email"] == "testuser@example.com"


def test_invitation_without_inviter_email_sends_without_cc(
    authenticated_client, db, monkeypatch
):
    owner, invited_user, club = _create_club_and_invited_user(db, "invited@example.com")
    owner.email = None
    db.commit()
    sent_email = {}

    def fake_send(self, **kwargs):
        sent_email.update(kwargs)
        return True

    monkeypatch.setattr(EmailService, "send_club_invitation_email", fake_send)

    response = authenticated_client.post(
        f"/clubs/{club.id}/invite",
        json={"invited_username": invited_user.username},
    )

    assert response.status_code == 200
    assert sent_email["to_email"] == invited_user.email
    assert sent_email["cc_email"] is None


def test_invitation_without_invited_user_email_is_created_without_sending(
    authenticated_client, db, monkeypatch
):
    _, invited_user, club = _create_club_and_invited_user(db, None)
    send_called = False

    def fake_send(self, **kwargs):
        nonlocal send_called
        send_called = True
        return True

    monkeypatch.setattr(EmailService, "send_club_invitation_email", fake_send)

    response = authenticated_client.post(
        f"/clubs/{club.id}/invite",
        json={"invited_username": invited_user.username},
    )

    assert response.status_code == 200
    assert send_called is False
    assert (
        db.query(models.ClubInvitation)
        .filter(models.ClubInvitation.invited_user_id == invited_user.id)
        .first()
        is not None
    )


def test_invitation_is_created_when_email_sending_fails(
    authenticated_client, db, monkeypatch
):
    _, invited_user, club = _create_club_and_invited_user(db, "invited@example.com")

    def failing_send(self, **kwargs):
        raise RuntimeError("Brevo unavailable")

    monkeypatch.setattr(EmailService, "send_club_invitation_email", failing_send)

    response = authenticated_client.post(
        f"/clubs/{club.id}/invite",
        json={"invited_username": invited_user.username},
    )

    assert response.status_code == 200
    assert (
        db.query(models.ClubInvitation)
        .filter(models.ClubInvitation.invited_user_id == invited_user.id)
        .first()
        is not None
    )
