import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.database import create_sync_engine, get_db
from app.main import app
from app.db.models import User
import sib_api_v3_sdk


def _get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set for tests.")
    return database_url


def _run_migrations() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    alembic_ini = root_dir / "alembic.ini"
    config = Config(str(alembic_ini))
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def engine():
    _get_database_url()
    _run_migrations()
    engine = create_sync_engine(os.environ["DATABASE_URL"])
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db(engine, TestingSessionLocal):
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, db):
    test_user = db.query(User).filter(User.username == "testuser").first()
    if not test_user:
        test_user = User(
            username="testuser", email="testuser@example.com", email_confirmed=1
        )
        test_user.set_password("testpassword")
        db.add(test_user)
        db.commit()

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client


@pytest.fixture(autouse=True)
def brevo_mock(request, monkeypatch):
    """Automatically mock Brevo transactional email calls for tests marked with @pytest.mark.brevo.

    This patches `sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email` to a no-op that returns None.
    """
    if "brevo" in getattr(request.node, "keywords", {}):

        def _fake_send_transac_email(self, *args, **kwargs):
            return None

        monkeypatch.setattr(
            sib_api_v3_sdk.TransactionalEmailsApi,
            "send_transac_email",
            _fake_send_transac_email,
        )
    yield
