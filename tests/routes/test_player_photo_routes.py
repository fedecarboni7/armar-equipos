import io
import os
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.db import models
from app.utils.r2 import process_player_photo

FAKE_PHOTO_URL = "https://fake-r2.example.com/players/s5/1/fake-uuid.webp"
FAKE_PHOTO_URL_2 = "https://fake-r2.example.com/players/s5/1/fake-uuid-2.webp"


def _make_valid_image_bytes(fmt="JPEG", size=(200, 200)):
    img = Image.new("RGB", size, color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


def _make_too_large_image_bytes():
    width, height = 2000, 2000
    random_bytes = os.urandom(width * height * 3)
    img = Image.frombytes("RGB", (width, height), random_bytes)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _get_test_user(db):
    return db.query(models.User).filter(models.User.username == "testuser").first()


def _create_personal_player(db, user, name="Photo Player"):
    player = models.PlayerScale5(
        name=name,
        velocidad=3,
        resistencia=3,
        control=3,
        pases=3,
        tiro=3,
        defensa=3,
        habilidad_arquero=3,
        fuerza_cuerpo=3,
        vision=3,
        user_id=user.id,
        club_id=None,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def _create_club_with_player(db, user, role="admin"):
    club = models.Club(name="Photo Test Club")
    db.add(club)
    db.flush()

    club_user = models.ClubUser(club_id=club.id, user_id=user.id, role=role)
    db.add(club_user)

    player = models.PlayerScale5(
        name="Club Photo Player",
        velocidad=3,
        resistencia=3,
        control=3,
        pases=3,
        tiro=3,
        defensa=3,
        habilidad_arquero=3,
        fuerza_cuerpo=3,
        vision=3,
        user_id=user.id,
        club_id=club.id,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return club, player


@pytest.fixture(autouse=True)
def r2_mock(monkeypatch):
    upload_mock = MagicMock(return_value=FAKE_PHOTO_URL)
    delete_mock = MagicMock()
    process_mock = MagicMock(side_effect=lambda b: b)

    monkeypatch.setattr("app.routes.player_routes.upload_player_photo", upload_mock)
    monkeypatch.setattr("app.routes.player_routes.delete_player_photo", delete_mock)
    monkeypatch.setattr("app.routes.player_routes.process_player_photo", process_mock)

    return {
        "upload": upload_mock,
        "delete": delete_mock,
        "process": process_mock,
    }


# --- Upload tests ---


def test_upload_unauthenticated(client):
    response = client.post(
        "/api/players/s5/1/photo",
        files={"file": ("test.jpg", b"fake", "image/jpeg")},
    )
    assert response.status_code == 401


def test_upload_no_file(authenticated_client):
    response = authenticated_client.post("/api/players/s5/1/photo")
    assert response.status_code == 422


def test_upload_too_large(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    big_bytes = _make_too_large_image_bytes()
    r2_mock["process"].side_effect = ValueError("La imagen no puede superar 5MB")

    response = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("big.png", big_bytes, "image/png")},
    )
    assert response.status_code == 400
    assert "5MB" in response.json()["detail"]


def test_upload_invalid_format(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    r2_mock["process"].side_effect = ValueError(
        "Formato no soportado: GIF. Usá JPEG, PNG o WEBP"
    )

    response = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("bad.gif", b"GIF89a not a real gif", "image/gif")},
    )
    assert response.status_code == 400
    assert "Formato no soportado" in response.json()["detail"]


def test_upload_valid_personal_player(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    response = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["photo_url"] == FAKE_PHOTO_URL
    r2_mock["upload"].assert_called_once()


def test_upload_club_player_admin(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    club, player = _create_club_with_player(db, user, role="admin")

    response = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["photo_url"] == FAKE_PHOTO_URL


def test_upload_club_player_non_admin(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    club, player = _create_club_with_player(db, user, role="miembro")

    response = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 403


def test_upload_club_player_not_member(authenticated_client, db, r2_mock):
    other_user = models.User(
        username="otheruser", email="other@example.com", email_confirmed=1
    )
    other_user.set_password("otherpass")
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    club = models.Club(name="Other Club")
    db.add(club)
    db.flush()

    player = models.PlayerScale5(
        name="Other Player",
        velocidad=3,
        resistencia=3,
        control=3,
        pases=3,
        tiro=3,
        defensa=3,
        habilidad_arquero=3,
        fuerza_cuerpo=3,
        vision=3,
        user_id=other_user.id,
        club_id=club.id,
    )
    db.add(player)
    db.commit()
    db.refresh(player)

    response = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 403


def test_upload_replaces_existing_photo(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    r2_mock["upload"].return_value = FAKE_PHOTO_URL
    response1 = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo1.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )
    assert response1.status_code == 200

    r2_mock["upload"].return_value = FAKE_PHOTO_URL_2
    r2_mock["delete"].reset_mock()

    response2 = authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo2.jpg", _make_valid_image_bytes("PNG"), "image/png")},
    )
    assert response2.status_code == 200
    assert response2.json()["photo_url"] == FAKE_PHOTO_URL_2
    r2_mock["delete"].assert_called_once_with(FAKE_PHOTO_URL)


def test_upload_nonexistent_player(authenticated_client, db, r2_mock):
    response = authenticated_client.post(
        "/api/players/s5/99999/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 404


def test_upload_invalid_player_type(authenticated_client, db):
    response = authenticated_client.post(
        "/api/players/s15/1/photo",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
    )
    assert response.status_code == 422


# --- Delete photo tests ---


def test_delete_photo_unauthenticated(client):
    response = client.delete("/api/players/s5/1/photo")
    assert response.status_code == 401


def test_delete_photo_no_photo(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    response = authenticated_client.delete(f"/api/players/s5/{player.id}/photo")
    assert response.status_code == 404


def test_delete_photo_success(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    r2_mock["upload"].return_value = FAKE_PHOTO_URL
    auth_client = authenticated_client
    auth_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )

    r2_mock["delete"].reset_mock()
    response = auth_client.delete(f"/api/players/s5/{player.id}/photo")
    assert response.status_code == 200
    assert response.json()["photo_url"] is None
    r2_mock["delete"].assert_called_once_with(FAKE_PHOTO_URL)


def test_delete_photo_club_admin(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    club, player = _create_club_with_player(db, user, role="admin")

    r2_mock["upload"].return_value = FAKE_PHOTO_URL
    authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )

    response = authenticated_client.delete(f"/api/players/s5/{player.id}/photo")
    assert response.status_code == 200


def test_delete_photo_non_admin_member(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    club, player = _create_club_with_player(db, user, role="miembro")

    player.photo_url = FAKE_PHOTO_URL
    db.commit()

    response = authenticated_client.delete(f"/api/players/s5/{player.id}/photo")
    assert response.status_code == 403


# --- GET player list includes photo_url ---


def test_get_players_includes_photo_url_null(authenticated_client, db):
    user = _get_test_user(db)
    _create_personal_player(db, user, name="NoPhoto Player")

    response = authenticated_client.get("/api/players")
    assert response.status_code == 200
    players = response.json()
    matching = [p for p in players if p["name"] == "NoPhoto Player"]
    assert len(matching) == 1
    assert matching[0]["photo_url"] is None


def test_get_players_includes_photo_url_after_upload(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user, name="WithPhoto Player")

    authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )

    response = authenticated_client.get("/api/players")
    assert response.status_code == 200
    matching = [p for p in response.json() if p["name"] == "WithPhoto Player"]
    assert len(matching) == 1
    assert matching[0]["photo_url"] == FAKE_PHOTO_URL


# --- Player deletion cleans up photo ---


def test_delete_player_cleans_up_photo(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    r2_mock["upload"].return_value = FAKE_PHOTO_URL
    authenticated_client.post(
        f"/api/players/s5/{player.id}/photo",
        files={"file": ("photo.jpg", _make_valid_image_bytes(), "image/jpeg")},
    )

    r2_mock["delete"].reset_mock()
    response = authenticated_client.delete(f"/api/players/{player.id}")
    assert response.status_code == 200
    r2_mock["delete"].assert_called_once_with(FAKE_PHOTO_URL)


def test_delete_player_no_photo_skips_r2(authenticated_client, db, r2_mock):
    user = _get_test_user(db)
    player = _create_personal_player(db, user)

    r2_mock["delete"].reset_mock()
    response = authenticated_client.delete(f"/api/players/{player.id}")
    assert response.status_code == 200
    r2_mock["delete"].assert_not_called()


def test_process_photo_rejects_oversized_file():
    big_bytes = _make_too_large_image_bytes()  # necesita ser genuinamente >5MB
    with pytest.raises(ValueError, match="5MB"):
        process_player_photo(big_bytes)


def test_process_photo_rejects_invalid_format():
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    with pytest.raises(ValueError, match="Formato no soportado"):
        process_player_photo(buf.getvalue())


def test_process_photo_resizes_and_converts_to_webp():
    valid_bytes = _make_valid_image_bytes(fmt="PNG", size=(1000, 600))  # no cuadrada
    result = process_player_photo(valid_bytes)
    img = Image.open(io.BytesIO(result))
    assert img.size == (512, 512)
    assert img.format == "WEBP"
