from app.db.models import PlayerScale5

# Test create player endpoint


def test_create_player_unauthenticated(client):
    # Test that the user cannot create a player without being authenticated
    response = client.post(
        "/api/player",
        json={
            "name": "Test Player",
            "velocidad": 4,
            "resistencia": 5,
            "control": 5,
            "pases": 3,
            "tiro": 3,
            "defensa": 2,
            "habilidad_arquero": 3,
            "fuerza_cuerpo": 5,
            "vision": 1,
        },
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_create_player(authenticated_client, db):
    # Create a player
    response = authenticated_client.post(
        "/api/player",
        json={
            "name": "Test Player",
            "velocidad": 4,
            "resistencia": 5,
            "control": 5,
            "pases": 3,
            "tiro": 3,
            "defensa": 2,
            "habilidad_arquero": 3,
            "fuerza_cuerpo": 5,
            "vision": 1,
        },
    )

    assert response.status_code == 200
    player_data = response.json()
    assert player_data["name"] == "Test Player"
    assert player_data["velocidad"] == 4

    db_player = (
        db.query(PlayerScale5).filter(PlayerScale5.name == "Test Player").first()
    )
    assert db_player is not None
    assert db_player.name == "Test Player"
    assert db_player.velocidad == 4


# Test get players endpoint


def test_get_players_unauthenticated(client):
    # Test that the user cannot access the get players endpoint without being authenticated
    response = client.get("/api/players", follow_redirects=False)
    assert response.status_code == 401


def test_get_players(authenticated_client, db):
    # Create some players
    authenticated_client.post(
        "/api/player",
        json={
            "name": "Player 1",
            "velocidad": 4,
            "resistencia": 5,
            "control": 5,
            "pases": 3,
            "tiro": 3,
            "defensa": 2,
            "habilidad_arquero": 3,
            "fuerza_cuerpo": 5,
            "vision": 1,
        },
    )

    authenticated_client.post(
        "/api/player",
        json={
            "name": "Player 2",
            "velocidad": 3,
            "resistencia": 4,
            "control": 4,
            "pases": 4,
            "tiro": 2,
            "defensa": 3,
            "habilidad_arquero": 2,
            "fuerza_cuerpo": 4,
            "vision": 2,
        },
    )

    # Get all players
    response = authenticated_client.get("/api/players")
    assert response.status_code == 200
    players = response.json()
    assert len(players) >= 2

    player_names = [p["name"] for p in players]
    assert "Player 1" in player_names
    assert "Player 2" in player_names


# Test update player endpoint


def test_update_player(authenticated_client, db):
    # Create a player
    create_response = authenticated_client.post(
        "/api/player",
        json={
            "name": "Player to Update",
            "velocidad": 4,
            "resistencia": 5,
            "control": 5,
            "pases": 3,
            "tiro": 3,
            "defensa": 2,
            "habilidad_arquero": 3,
            "fuerza_cuerpo": 5,
            "vision": 1,
        },
    )
    player_data = create_response.json()
    player_id = player_data["id"]

    # Update the player
    update_response = authenticated_client.put(
        "/api/player",
        json={
            "id": player_id,
            "name": "Updated Player",
            "velocidad": 5,
            "resistencia": 5,
            "control": 5,
            "pases": 4,
            "tiro": 4,
            "defensa": 3,
            "habilidad_arquero": 3,
            "fuerza_cuerpo": 5,
            "vision": 2,
        },
    )

    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["name"] == "Updated Player"
    assert updated_data["velocidad"] == 5
    assert updated_data["pases"] == 4


# Test delete player endpoint


def test_delete_player(authenticated_client, db):
    # Create a player
    create_response = authenticated_client.post(
        "/api/player",
        json={
            "name": "Player to Delete",
            "velocidad": 4,
            "resistencia": 5,
            "control": 5,
            "pases": 3,
            "tiro": 3,
            "defensa": 2,
            "habilidad_arquero": 3,
            "fuerza_cuerpo": 5,
            "vision": 1,
        },
    )
    player_data = create_response.json()
    player_id = player_data["id"]

    # Delete the player
    delete_response = authenticated_client.delete(f"/api/players/{player_id}")
    assert delete_response.status_code == 200

    # Verify it's deleted from database
    db_player = db.query(PlayerScale5).filter(PlayerScale5.id == player_id).first()
    assert db_player is None


def test_delete_nonexistent_player(authenticated_client):
    # Try to delete a player that does not exist
    response = authenticated_client.delete("/api/players/99999")
    assert response.status_code == 404
