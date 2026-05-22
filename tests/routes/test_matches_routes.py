from datetime import date

from app.db import models


def create_club_with_players(db, user, n=4, scale=2):
    club = models.Club(name=f"Test Club {scale}")
    db.add(club)
    db.flush()

    club_user = models.ClubUser(club_id=club.id, user_id=user.id, role="admin")
    db.add(club_user)

    players = []
    for index in range(n):
        player = models.PlayerScale10(
            name=f"Player {scale}-{index + 1}",
            velocidad=5,
            resistencia=5,
            control=5,
            pases=5,
            tiro=5,
            defensa=5,
            habilidad_arquero=5,
            fuerza_cuerpo=5,
            vision=5,
            user_id=user.id,
            club_id=club.id,
        )
        db.add(player)
        players.append(player)

    db.commit()
    return club, players


def _get_test_user(db):
    return db.query(models.User).filter(models.User.username == "testuser").first()


def test_create_match_basic(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=4)
    played_at = date(2026, 5, 20).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 2,
            "team_b_score": 1,
            "notes": "Test note",
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 0, "assists": 0},
                {"player_v2_id": players[1].id, "team": "A", "goals": 0, "assists": 0},
                {"player_v2_id": players[2].id, "team": "B", "goals": 0, "assists": 0},
                {"player_v2_id": players[3].id, "team": "B", "goals": 0, "assists": 0},
            ],
        },
    )

    assert response.status_code in (200, 201)
    payload = response.json()
    assert payload["notes"] == "Test note"
    assert all(
        player["goals"] == 0 and player["assists"] == 0 for player in payload["players"]
    )


def test_create_match_goals_assists_persisted(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=4)
    played_at = date(2026, 5, 20).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 3,
            "team_b_score": 1,
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 2, "assists": 1},
                {"player_v2_id": players[1].id, "team": "A", "goals": 1, "assists": 0},
                {"player_v2_id": players[2].id, "team": "B", "goals": 1, "assists": 0},
                {"player_v2_id": players[3].id, "team": "B", "goals": 0, "assists": 1},
            ],
        },
    )

    assert response.status_code in (200, 201)
    match_id = response.json()["id"]

    detail_response = authenticated_client.get(f"/matches/{match_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    players_by_id = {player["player_v2_id"]: player for player in detail["players"]}

    assert players_by_id[players[0].id]["goals"] == 2
    assert players_by_id[players[0].id]["assists"] == 1
    assert players_by_id[players[1].id]["goals"] == 1
    assert players_by_id[players[1].id]["assists"] == 0
    assert players_by_id[players[2].id]["goals"] == 1
    assert players_by_id[players[2].id]["assists"] == 0
    assert players_by_id[players[3].id]["goals"] == 0
    assert players_by_id[players[3].id]["assists"] == 1


def test_create_match_goals_exceed_score(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=2)
    played_at = date(2026, 5, 20).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 1,
            "team_b_score": 0,
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 2, "assists": 0},
                {"player_v2_id": players[1].id, "team": "B", "goals": 0, "assists": 0},
            ],
        },
    )

    assert response.status_code in (400, 422)


def test_create_match_assists_exceed_score(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=2)
    played_at = date(2026, 5, 20).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 0,
            "team_b_score": 1,
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 0, "assists": 0},
                {"player_v2_id": players[1].id, "team": "B", "goals": 0, "assists": 2},
            ],
        },
    )

    assert response.status_code in (400, 422)


def test_edit_match_updates_notes_goals_assists(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=2)
    played_at = date(2026, 5, 20).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 1,
            "team_b_score": 0,
            "notes": "original",
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 0, "assists": 0},
                {"player_v2_id": players[1].id, "team": "B", "goals": 0, "assists": 0},
            ],
        },
    )
    assert response.status_code in (200, 201)
    match_id = response.json()["id"]

    patch_response = authenticated_client.patch(
        f"/matches/{match_id}",
        json={
            "team_a_score": 1,
            "team_b_score": 0,
            "notes": "updated",
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 1, "assists": 0},
                {"player_v2_id": players[1].id, "team": "B", "goals": 0, "assists": 0},
            ],
        },
    )
    assert patch_response.status_code == 200

    detail_response = authenticated_client.get(f"/matches/{match_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    players_by_id = {player["player_v2_id"]: player for player in detail["players"]}

    assert detail["notes"] == "updated"
    assert players_by_id[players[0].id]["goals"] == 1


def test_leaderboard_returns_goals_assists(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=2)
    played_at = date(2026, 5, 20).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 2,
            "team_b_score": 0,
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 2, "assists": 1},
                {"player_v2_id": players[1].id, "team": "B", "goals": 0, "assists": 0},
            ],
        },
    )
    assert response.status_code in (200, 201)

    standings_response = authenticated_client.get(
        f"/matches/standings?version=v2&club_id={club.id}"
    )
    assert standings_response.status_code == 200
    standings = standings_response.json()
    standings_by_id = {row["player_id"]: row for row in standings}

    assert standings_by_id[players[0].id]["goals"] == 2
    assert standings_by_id[players[0].id]["assists"] == 1
    assert standings_by_id[players[1].id]["goals"] == 0
    assert standings_by_id[players[1].id]["assists"] == 0


def test_leaderboard_orders_by_goals_tiebreaker(authenticated_client, db):
    user = _get_test_user(db)
    club, players = create_club_with_players(db, user, n=2)
    played_at = date(2026, 5, 20).isoformat()

    authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 2,
            "team_b_score": 1,
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 2, "assists": 0},
                {"player_v2_id": players[1].id, "team": "B", "goals": 1, "assists": 0},
            ],
        },
    )

    authenticated_client.post(
        "/matches",
        json={
            "club_id": club.id,
            "played_at": played_at,
            "team_a_score": 1,
            "team_b_score": 2,
            "players": [
                {"player_v2_id": players[0].id, "team": "A", "goals": 1, "assists": 0},
                {"player_v2_id": players[1].id, "team": "B", "goals": 1, "assists": 0},
            ],
        },
    )

    standings_response = authenticated_client.get(
        f"/matches/standings?version=v2&club_id={club.id}"
    )
    assert standings_response.status_code == 200
    standings = standings_response.json()

    assert standings[0]["player_id"] == players[0].id
