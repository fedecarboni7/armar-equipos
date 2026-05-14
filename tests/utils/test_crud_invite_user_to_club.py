from app.db import models
from app.utils import crud


def test_invite_user_to_club_username_is_lowercased_before_lookup(db):
    owner = models.User(
        username="owner_invite_test",
        email="owner_invite_test@example.com",
        email_confirmed=1,
    )
    owner.set_password("Testpassword1*")
    db.add(owner)

    invited = models.User(
        username="invited_user_test",
        email="invited_user_test@example.com",
        email_confirmed=1,
    )
    invited.set_password("Testpassword1*")
    db.add(invited)

    club = models.Club(name="Case Insensitive Club")
    db.add(club)
    db.commit()

    club_owner = models.ClubUser(club_id=club.id, user_id=owner.id, role="owner")
    db.add(club_owner)
    db.commit()

    invitation = crud.invite_user_to_club(
        db=db,
        club_id=club.id,
        inviter_id=owner.id,
        invited_username="InViTeD_UsEr_TeSt",
    )

    assert invitation.club_id == club.id
    assert invitation.invited_user_id == invited.id
