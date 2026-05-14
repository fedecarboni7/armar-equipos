import pytest
from datetime import datetime, timedelta, timezone
from app.db.models import User
from app.routes import admin_routes


TEST_CRON_TOKEN = "test-cron-token"


@pytest.fixture(autouse=True)
def mock_cron_secret(monkeypatch):
    monkeypatch.setattr(admin_routes, "CRON_SECRET", TEST_CRON_TOKEN)


def test_cleanup_expired_users_without_token(client):
    response = client.post("/cleanup-expired-users")
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_cleanup_expired_users_with_invalid_token(client):
    response = client.post(
        "/cleanup-expired-users", headers={"X-Cron-Token": "invalid_token"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_cleanup_expired_users_with_valid_token(client, db):
    now = datetime.now(timezone.utc)

    # Usuario expirado con email (debe eliminarse)
    expired_user_with_email = User(
        username="expired_user",
        email="expired@example.com",
        email_confirmed=0,
        email_confirmation_token="token123",
        email_confirmation_expires=now - timedelta(days=1),
    )
    expired_user_with_email.set_password("password123")
    db.add(expired_user_with_email)

    # Usuario legacy sin email (NO debe eliminarse)
    legacy_user_no_email = User(
        username="legacy_user",
        email=None,
        email_confirmed=0,
        email_confirmation_token=None,
        email_confirmation_expires=None,
    )
    legacy_user_no_email.set_password("password123")
    db.add(legacy_user_no_email)

    # Usuario con token válido (NO debe eliminarse)
    valid_user = User(
        username="valid_user",
        email="valid@example.com",
        email_confirmed=0,
        email_confirmation_token="token456",
        email_confirmation_expires=now + timedelta(days=1),
    )
    valid_user.set_password("password123")
    db.add(valid_user)

    # Usuario confirmado (NO debe eliminarse)
    confirmed_user = User(
        username="confirmed_user",
        email="confirmed@example.com",
        email_confirmed=1,
        email_confirmation_token=None,
        email_confirmation_expires=None,
    )
    confirmed_user.set_password("password123")
    db.add(confirmed_user)

    db.commit()

    # Ejecutar cleanup con token válido
    response = client.post(
        "/cleanup-expired-users",
        headers={"X-Cron-Token": TEST_CRON_TOKEN},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_count"] == 1
    assert "timestamp" in data

    # Verificar que el usuario expirado con email fue eliminado
    assert db.query(User).filter(User.username == "expired_user").first() is None

    # Verificar que los otros usuarios siguen existiendo
    assert db.query(User).filter(User.username == "legacy_user").first() is not None
    assert db.query(User).filter(User.username == "valid_user").first() is not None
    assert db.query(User).filter(User.username == "confirmed_user").first() is not None


def test_cleanup_expired_users_no_expired_users(client, db):
    now = datetime.now(timezone.utc)

    # Usuario con token válido
    valid_user = User(
        username="valid_user_test",
        email="valid_test@example.com",
        email_confirmed=0,
        email_confirmation_token="token789",
        email_confirmation_expires=now + timedelta(days=1),
    )
    valid_user.set_password("password123")
    db.add(valid_user)
    db.commit()

    response = client.post(
        "/cleanup-expired-users",
        headers={"X-Cron-Token": TEST_CRON_TOKEN},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_count"] == 0

    # Verificar que el usuario sigue existiendo
    assert db.query(User).filter(User.username == "valid_user_test").first() is not None
