from datetime import timedelta

from app.db import models
from app.utils.time_utils import get_calendar_week_bounds


SKILL_PAYLOAD = {
    "velocidad": 4,
    "resistencia": 4,
    "control": 3,
    "pases": 5,
    "tiro": 2,
    "defensa": 3,
    "habilidad_arquero": 1,
    "fuerza_cuerpo": 4,
    "vision": 5,
}


def _create_club_with_owner(db, user):
    club = models.Club(name="Club Votos")
    db.add(club)
    db.flush()
    db.add(models.ClubUser(club_id=club.id, user_id=user.id, role="owner"))
    db.commit()
    return club


def _create_player_s5(db, club_id, user_id):
    player = models.PlayerScale5(
        name="Jugador Voto",
        velocidad=3,
        resistencia=3,
        control=3,
        pases=3,
        tiro=3,
        defensa=3,
        habilidad_arquero=3,
        fuerza_cuerpo=3,
        vision=3,
        user_id=user_id,
        club_id=club_id,
    )
    db.add(player)
    db.commit()
    return player


def _get_vote(db, user_id, player_id):
    return (
        db.query(models.SkillVote)
        .filter(
            models.SkillVote.voter_id == user_id,
            models.SkillVote.player_s5_id == player_id,
        )
        .first()
    )


def _post_vote(client, club, player, **overrides):
    return client.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={**SKILL_PAYLOAD, "player_s5_id": player.id, **overrides},
    )


def _backdate_vote(db, vote, when):
    vote.updated_at = when.replace(tzinfo=None)
    db.commit()


def test_vote_create_and_update(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player = _create_player_s5(db, club.id, user.id)

    response = _post_vote(authenticated_client, club, player)
    assert response.status_code == 200
    payload = response.json()
    assert payload["velocidad"] == 4
    assert "voter_id" not in payload

    week_start, _ = get_calendar_week_bounds()
    vote = _get_vote(db, user.id, player.id)
    _backdate_vote(db, vote, week_start - timedelta(days=7))

    response = _post_vote(authenticated_client, club, player, velocidad=5)
    assert response.status_code == 200
    payload = response.json()
    assert payload["velocidad"] == 5


def test_second_vote_same_week_rejected(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player = _create_player_s5(db, club.id, user.id)

    response = _post_vote(authenticated_client, club, player)
    assert response.status_code == 200

    response = _post_vote(authenticated_client, club, player, velocidad=5)
    assert response.status_code == 400
    assert "lunes" in response.json()["detail"]

    db.expire_all()
    vote = _get_vote(db, user.id, player.id)
    assert vote.velocidad == 4


def test_vote_week_boundary_monday_blocks_and_previous_sunday_allows(
    authenticated_client, db
):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    week_start, _ = get_calendar_week_bounds()

    player_this_week = _create_player_s5(db, club.id, user.id)
    response = _post_vote(authenticated_client, club, player_this_week)
    assert response.status_code == 200

    vote = _get_vote(db, user.id, player_this_week.id)
    _backdate_vote(db, vote, week_start)

    response = _post_vote(authenticated_client, club, player_this_week, velocidad=5)
    assert response.status_code == 400
    assert "lunes" in response.json()["detail"]

    player_last_week = _create_player_s5(db, club.id, user.id)
    response = _post_vote(authenticated_client, club, player_last_week)
    assert response.status_code == 200

    vote = _get_vote(db, user.id, player_last_week.id)
    _backdate_vote(db, vote, week_start - timedelta(hours=4))

    response = _post_vote(authenticated_client, club, player_last_week, velocidad=5)
    assert response.status_code == 200
    assert response.json()["velocidad"] == 5


def test_votes_independent_per_player(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player_a = _create_player_s5(db, club.id, user.id)
    player_b = _create_player_s5(db, club.id, user.id)

    response = _post_vote(authenticated_client, club, player_a)
    assert response.status_code == 200

    response = _post_vote(authenticated_client, club, player_b)
    assert response.status_code == 200
    assert response.json()["player_s5_id"] == player_b.id


def test_get_vote_and_players_with_votes(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player = _create_player_s5(db, club.id, user.id)

    authenticated_client.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={**SKILL_PAYLOAD, "player_s5_id": player.id},
    )

    response = authenticated_client.get(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["pases"] == 5

    players_response = authenticated_client.get(
        f"/api/players?scale=1-5&club_id={club.id}"
    )
    assert players_response.status_code == 200
    players = players_response.json()
    target = next(item for item in players if item["id"] == player.id)
    assert target["velocidad"] == 4
    assert target["vote_average"]["velocidad"] == 4


def test_fractional_average_with_multiple_voters(authenticated_client, db):
    """Two voters with different skill values produce a non-integer average."""
    user1 = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user1)
    player = _create_player_s5(db, club.id, user1.id)

    # First voter (voting all 4s)
    authenticated_client.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={
            **{k: 4 for k in SKILL_PAYLOAD},
            "player_s5_id": player.id,
        },
    )

    # Second user
    user2 = models.User(
        username="voter2", email="voter2@example.com", email_confirmed=1
    )
    user2.set_password("pass2")
    db.add(user2)
    db.commit()
    db.refresh(user2)

    db.add(models.ClubUser(club_id=club.id, user_id=user2.id, role="miembro"))
    db.commit()

    from fastapi.testclient import TestClient

    from app.main import app as _app
    from app.db.database import get_db as _get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    _app.dependency_overrides[_get_db] = override_get_db
    client2 = TestClient(_app)
    client2.post(
        "/login",
        data={"username": "voter2", "password": "pass2"},
        follow_redirects=False,
    )

    # Second voter (voting all 5s)
    vote_resp = client2.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={
            **{k: 5 for k in SKILL_PAYLOAD},
            "player_s5_id": player.id,
        },
    )
    assert vote_resp.status_code == 200

    # Restore authenticated_client override and GET /api/players
    _app.dependency_overrides[_get_db] = override_get_db
    response = authenticated_client.get(f"/api/players?scale=1-5&club_id={club.id}")
    assert response.status_code == 200
    players = response.json()
    target = next(item for item in players if item["id"] == player.id)

    assert target["velocidad"] == 4.5
    assert target["vote_average"]["velocidad"] == 4.5
    assert target["skills"]["velocidad"] == 3
