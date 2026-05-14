import pytest
from app.db.models import User


@pytest.fixture
def unauthorized_client(client, db):
    # Create a regular user for the test
    username = "regularuser"
    password = "Loginpassword123"
    email = "regularuser@example.com"

    # Check if user already exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, email=email, email_confirmed=1)
        user.set_password(password)
        db.add(user)
        db.commit()

    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/home"
    return client


@pytest.fixture
def authorized_client(client, db):
    # Create an admin user for the test
    username = "admin"
    password = "Loginpassword123"
    email = "admin@example.com"

    # Check if admin already exists
    admin_user = db.query(User).filter(User.username == username).first()
    if not admin_user:
        admin_user = User(username=username, email=email, email_confirmed=1)
        admin_user.set_password(password)
        db.add(admin_user)
        db.commit()

    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/home"
    return client


def test_get_docs_unauthenticated_user(client):
    client.get("/logout")  # Ensure user is logged out
    response = client.get("/docs")
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuario no autenticado", "error": 401}


def test_get_docs_unauthorized_user(unauthorized_client):
    response = unauthorized_client.get("/docs")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized: /docs", "error": 401}


def test_get_docs_authorized(authorized_client):
    response = authorized_client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text


# Test the /openapi.json endpoint


def test_get_openapi_unauthenticated_user(client):
    client.get("/logout")  # Ensure user is logged out
    response = client.get("/openapi.json")
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuario no autenticado", "error": 401}


def test_get_openapi_unauthorized_user(unauthorized_client):
    response = unauthorized_client.get("/openapi.json")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized: /openapi.json", "error": 401}


def test_get_openapi_authorized(authorized_client):
    response = authorized_client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
