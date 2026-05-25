from app.db import models


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


def _login(client, username, password):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 302


def _create_user(db, username):
    user = models.User(username=username, email=f"{username}@example.com", email_confirmed=1)
    user.set_password("password123")
    db.add(user)
    db.commit()
    return user


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


def test_vote_requires_open_voting(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player = _create_player_s5(db, club.id, user.id)

    response = authenticated_client.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={**SKILL_PAYLOAD, "player_s5_id": player.id},
    )

    assert response.status_code == 403


def test_vote_open_and_upsert(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player = _create_player_s5(db, club.id, user.id)

    club.voting_open_s5 = True
    db.commit()

    response = authenticated_client.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={**SKILL_PAYLOAD, "player_s5_id": player.id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["velocidad"] == 4
    assert "voter_id" not in payload

    response = authenticated_client.post(
        f"/api/clubs/{club.id}/players/{player.id}/vote?scale=s5",
        json={**SKILL_PAYLOAD, "player_s5_id": player.id, "velocidad": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["velocidad"] == 5


def test_get_vote_and_players_with_votes(authenticated_client, db):
    user = db.query(models.User).filter(models.User.username == "testuser").first()
    club = _create_club_with_owner(db, user)
    player = _create_player_s5(db, club.id, user.id)

    club.voting_open_s5 = True
    db.commit()

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


def test_toggle_voting_owner_only(client, db):
    owner = _create_user(db, "owner_toggle")
    member = _create_user(db, "member_toggle")
    club = _create_club_with_owner(db, owner)
    db.add(models.ClubUser(club_id=club.id, user_id=member.id, role="member"))
    db.commit()

    _login(client, "member_toggle", "password123")
    response = client.post(f"/api/clubs/{club.id}/voting?scale=s5&action=open")
    assert response.status_code == 403

    _login(client, "owner_toggle", "password123")
    response = client.post(f"/api/clubs/{club.id}/voting?scale=s5&action=open")
    assert response.status_code == 200
    payload = response.json()
    assert payload["voting_open_s5"] is True
