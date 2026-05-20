from datetime import datetime, timezone


def _create_player(authenticated_client, scale: str = "1-5"):
    payload = {
        "name": f"Test Player {scale}",
        "velocidad": 4,
        "resistencia": 5,
        "control": 5,
        "pases": 3,
        "tiro": 3,
        "defensa": 2,
        "habilidad_arquero": 3,
        "fuerza_cuerpo": 5,
        "vision": 1,
    }
    suffix = "?scale=1-10" if scale == "1-10" else ""
    response = authenticated_client.post(f"/api/player{suffix}", json=payload)
    assert response.status_code == 200
    return response.json()["id"]


def get_result(players, field, player_id):
    return next(p["result"] for p in players if p[field] == player_id)


def test_create_match_and_stats_v1(authenticated_client):
    player_v1_id = _create_player(authenticated_client, scale="1-5")
    player_v2_id = _create_player(authenticated_client, scale="1-5")

    played_at = datetime(2026, 5, 19, 10, 0, 0, tzinfo=timezone.utc).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "played_at": played_at,
            "team_a_score": 2,
            "team_b_score": 1,
            "players": [
                {"player_v1_id": player_v1_id, "team": "A"},
                {"player_v1_id": player_v2_id, "team": "B"},
            ],
        },
    )
    assert response.status_code == 200
    match_data = response.json()
    assert get_result(match_data["players"], "player_v1_id", player_v1_id) == "win"
    assert get_result(match_data["players"], "player_v1_id", player_v2_id) == "loss"

    response = authenticated_client.post(
        "/matches",
        json={
            "played_at": played_at,
            "team_a_score": 1,
            "team_b_score": 1,
            "players": [
                {"player_v1_id": player_v1_id, "team": "A"},
                {"player_v1_id": player_v2_id, "team": "B"},
            ],
        },
    )
    assert response.status_code == 200

    stats_v1 = authenticated_client.get(
        f"/players/{player_v1_id}/stats?version=v1"
    ).json()
    assert stats_v1["played"] == 2
    assert stats_v1["wins"] == 1
    assert stats_v1["losses"] == 0
    assert stats_v1["draws"] == 1

    stats_v2 = authenticated_client.get(
        f"/players/{player_v2_id}/stats?version=v1"
    ).json()
    assert stats_v2["played"] == 2
    assert stats_v2["wins"] == 0
    assert stats_v2["losses"] == 1
    assert stats_v2["draws"] == 1


def test_create_match_and_stats_v2(authenticated_client):
    player_v1_id = _create_player(authenticated_client, scale="1-10")
    player_v2_id = _create_player(authenticated_client, scale="1-10")

    played_at = datetime(2026, 5, 19, 10, 0, 0, tzinfo=timezone.utc).isoformat()

    response = authenticated_client.post(
        "/matches",
        json={
            "played_at": played_at,
            "team_a_score": 2,
            "team_b_score": 1,
            "players": [
                {"player_v2_id": player_v1_id, "team": "A"},
                {"player_v2_id": player_v2_id, "team": "B"},
            ],
        },
    )
    assert response.status_code == 200
    match_data = response.json()
    assert get_result(match_data["players"], "player_v2_id", player_v1_id) == "win"
    assert get_result(match_data["players"], "player_v2_id", player_v2_id) == "loss"

    response = authenticated_client.post(
        "/matches",
        json={
            "played_at": played_at,
            "team_a_score": 1,
            "team_b_score": 1,
            "players": [
                {"player_v2_id": player_v1_id, "team": "A"},
                {"player_v2_id": player_v2_id, "team": "B"},
            ],
        },
    )
    assert response.status_code == 200

    stats_v1 = authenticated_client.get(
        f"/players/{player_v1_id}/stats?version=v2"
    ).json()
    assert stats_v1["played"] == 2
    assert stats_v1["wins"] == 1
    assert stats_v1["losses"] == 0
    assert stats_v1["draws"] == 1

    stats_v2 = authenticated_client.get(
        f"/players/{player_v2_id}/stats?version=v2"
    ).json()
    assert stats_v2["played"] == 2
    assert stats_v2["wins"] == 0
    assert stats_v2["losses"] == 1
    assert stats_v2["draws"] == 1
