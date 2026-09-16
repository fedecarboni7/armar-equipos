import time
from collections import deque

import pytest

from app.db import models
from app.routes import public_routes
from app.routes.public_routes import PUBLIC_SHARE_RATE_LIMIT
from app.utils import crud

SKILLS_S5 = {
    "velocidad": 3,
    "resistencia": 3,
    "control": 3,
    "pases": 3,
    "tiro": 3,
    "defensa": 3,
    "habilidad_arquero": 3,
    "fuerza_cuerpo": 3,
    "vision": 3,
}


@pytest.fixture(autouse=True)
def _clear_rate_limit_store():
    public_routes._rate_limit_store.clear()
    yield
    public_routes._rate_limit_store.clear()


def _get_test_user(db):
    return db.query(models.User).filter(models.User.username == "testuser").first()


def _create_user(db, username):
    user = models.User(
        username=username, email=f"{username}@example.com", email_confirmed=1
    )
    user.set_password("password")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_club(db, user, role="owner", name="Share Test Club"):
    club = models.Club(name=name)
    db.add(club)
    db.flush()
    db.add(models.ClubUser(club_id=club.id, user_id=user.id, role=role))
    db.commit()
    db.refresh(club)
    return club


def _create_player_s5(db, user, club=None, name="Share Player S5", **skills):
    player = models.PlayerScale5(
        name=name,
        user_id=user.id,
        club_id=club.id if club else None,
        **{**SKILLS_S5, **skills},
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def _create_player_s10(db, user, club=None, name="Share Player S10", **skills):
    player = models.PlayerScale10(
        name=name,
        user_id=user.id,
        club_id=club.id if club else None,
        **{**SKILLS_S5, **skills},
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def _create_vote_s5(db, club, voter, player, value):
    vote = models.SkillVote(
        club_id=club.id,
        voter_id=voter.id,
        player_s5_id=player.id,
        velocidad=value,
        resistencia=value,
        control=value,
        pases=value,
        tiro=value,
        defensa=value,
        habilidad_arquero=value,
        fuerza_cuerpo=value,
        vision=value,
    )
    db.add(vote)
    db.commit()
    return vote


def _create_vote_s10(db, club, voter, player, value):
    vote = models.SkillVote(
        club_id=club.id,
        voter_id=voter.id,
        player_s10_id=player.id,
        velocidad=value,
        resistencia=value,
        control=value,
        pases=value,
        tiro=value,
        defensa=value,
        habilidad_arquero=value,
        fuerza_cuerpo=value,
        vision=value,
    )
    db.add(vote)
    db.commit()
    return vote


def test_generate_share_as_owner_succeeds(authenticated_client, db):
    user = _get_test_user(db)
    club = _create_club(db, user, role="owner")
    player = _create_player_s5(db, user, club)

    response = authenticated_client.post(f"/api/players/s5/{player.id}/share")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"]
    assert data["share_url"].endswith(f"/p/{data['share_token']}")

    db.refresh(player)
    assert player.share_token == data["share_token"]


def test_generate_share_as_admin_succeeds(authenticated_client, db):
    user = _get_test_user(db)
    club = _create_club(db, user, role="admin")
    player = _create_player_s10(db, user, club)

    response = authenticated_client.post(f"/api/players/s10/{player.id}/share")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"]
    assert data["share_url"].endswith(f"/p/{data['share_token']}")

    db.refresh(player)
    assert player.share_token == data["share_token"]


def test_generate_share_as_non_admin_rejected(authenticated_client, db):
    user = _get_test_user(db)
    club = _create_club(db, user, role="miembro")
    player = _create_player_s5(db, user, club)

    response = authenticated_client.post(f"/api/players/s5/{player.id}/share")

    assert response.status_code == 403


def test_generate_share_unauthenticated_rejected(client, db):
    response = client.post("/api/players/s5/1/share")

    assert response.status_code == 401


def test_generate_share_nonexistent_player_404(authenticated_client):
    response = authenticated_client.post("/api/players/s5/99999/share")

    assert response.status_code == 404


def test_generate_share_clubless_player_owner_succeeds(authenticated_client, db):
    user = _get_test_user(db)
    player = _create_player_s5(db, user, club=None)

    response = authenticated_client.post(f"/api/players/s5/{player.id}/share")

    assert response.status_code == 200
    assert response.json()["share_token"]


def test_generate_share_clubless_player_non_owner_rejected(authenticated_client, db):
    other_user = _create_user(db, "shareother")
    player = _create_player_s5(db, other_user, club=None)

    response = authenticated_client.post(f"/api/players/s5/{player.id}/share")

    assert response.status_code == 403


def test_share_status_without_token(authenticated_client, db):
    user = _get_test_user(db)
    player = _create_player_s5(db, user)

    response = authenticated_client.get(f"/api/players/s5/{player.id}/share-status")

    assert response.status_code == 200
    assert response.json() == {
        "is_shared": False,
        "share_token": None,
        "share_url": None,
    }


def test_share_status_with_active_token(authenticated_client, db):
    user = _get_test_user(db)
    player = _create_player_s10(db, user)
    token = crud.generate_player_share_token(db, player)

    response = authenticated_client.get(f"/api/players/s10/{player.id}/share-status")

    assert response.status_code == 200
    data = response.json()
    assert data["is_shared"] is True
    assert data["share_token"] == token
    assert data["share_url"].endswith(f"/p/{token}")


def test_share_status_non_admin_rejected(authenticated_client, db):
    user = _get_test_user(db)
    club = _create_club(db, user, role="miembro")
    player = _create_player_s5(db, user, club)

    response = authenticated_client.get(f"/api/players/s5/{player.id}/share-status")

    assert response.status_code == 403


def test_share_status_nonexistent_player_404(authenticated_client):
    response = authenticated_client.get("/api/players/s10/99999/share-status")

    assert response.status_code == 404


def test_revoke_share_works_and_public_404s_after(authenticated_client, db, client):
    user = _get_test_user(db)
    club = _create_club(db, user, role="owner")
    player = _create_player_s5(db, user, club)

    token = crud.generate_player_share_token(db, player)

    response = client.get(f"/public/players/{token}")
    assert response.status_code == 200

    response = authenticated_client.delete(f"/api/players/s5/{player.id}/share")
    assert response.status_code == 200

    db.refresh(player)
    assert player.share_token is None

    response = client.get(f"/public/players/{token}")
    assert response.status_code == 404


def test_regenerate_invalidates_old_token(authenticated_client, db, client):
    user = _get_test_user(db)
    club = _create_club(db, user, role="owner")
    player = _create_player_s5(db, user, club)

    first = authenticated_client.post(f"/api/players/s5/{player.id}/share")
    assert first.status_code == 200
    old_token = first.json()["share_token"]

    second = authenticated_client.post(f"/api/players/s5/{player.id}/share")
    assert second.status_code == 200
    new_token = second.json()["share_token"]

    assert new_token != old_token

    assert client.get(f"/public/players/{old_token}").status_code == 404
    assert client.get(f"/public/players/{new_token}").status_code == 200


def test_public_returns_combined_shape_s5(authenticated_client, db, client):
    user = _get_test_user(db)
    other_user = _create_user(db, "sharevoter")
    club = _create_club(db, user, role="owner")
    player = _create_player_s5(db, user, club)
    _create_vote_s5(db, club, user, player, 5)
    _create_vote_s5(db, club, other_user, player, 4)

    token = crud.generate_player_share_token(db, player)

    response = client.get(f"/public/players/{token}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == player.name
    assert data["scale"] == "s5"
    assert data["photo_url"] is None
    for field in crud.SKILL_FIELDS:
        assert data[field] == 4.5
        assert isinstance(data[field], float)
    for absent in (
        "skills",
        "vote_average",
        "vote_count",
        "user_id",
        "club_id",
        "club_name",
    ):
        assert absent not in data


def test_public_returns_combined_shape_s10(authenticated_client, db, client):
    user = _get_test_user(db)
    club = _create_club(db, user, role="owner")
    player = _create_player_s10(db, user, club)

    token = crud.generate_player_share_token(db, player)

    response = client.get(f"/public/players/{token}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == player.name
    assert data["scale"] == "s10"
    for field in crud.SKILL_FIELDS:
        assert data[field] == 3.0
        assert isinstance(data[field], float)
    for absent in (
        "skills",
        "vote_average",
        "vote_count",
        "user_id",
        "club_id",
        "club_name",
    ):
        assert absent not in data


def test_public_vote_average_s10_with_votes(authenticated_client, db, client):
    user = _get_test_user(db)
    other_user = _create_user(db, "sharevoter10")
    club = _create_club(db, user, role="owner")
    player = _create_player_s10(db, user, club)
    _create_vote_s10(db, club, user, player, 8)
    _create_vote_s10(db, club, other_user, player, 6)

    token = crud.generate_player_share_token(db, player)

    response = client.get(f"/public/players/{token}")

    assert response.status_code == 200
    data = response.json()
    for field in crud.SKILL_FIELDS:
        assert data[field] == 7.0


def test_public_garbage_token_404s(client):
    response = client.get("/public/players/nonexistent-token-xyz")

    assert response.status_code == 404


def test_public_rate_limit_429_without_sleeping(authenticated_client, db, client):
    user = _get_test_user(db)
    club = _create_club(db, user, role="owner")
    player = _create_player_s5(db, user, club)
    token = crud.generate_player_share_token(db, player)

    now = time.monotonic()
    public_routes._rate_limit_store["testclient"] = deque(
        [now] * PUBLIC_SHARE_RATE_LIMIT
    )

    response = client.get(f"/public/players/{token}")

    assert response.status_code == 429
    assert "retry-after" in response.headers

    response = client.get(
        f"/public/players/{token}", headers={"x-forwarded-for": "10.0.0.1"}
    )
    assert response.status_code == 200
