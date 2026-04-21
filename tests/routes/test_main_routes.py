from types import SimpleNamespace

from app.db.models import User
from app.routes.main_routes import build_player_scores, parse_goalkeeper_skill_flag
from app.utils.auth import get_current_user
from app.utils.team_optimizer import find_best_combination

def test_get_home(client, db):
    # First test without authentication
    response = client.get("/home")
    assert response.status_code == 200
    assert response.template.name == "landing-page.html"

    # Then test with authentication
    # Create a confirmed user directly for testing
    username = "hometestuser"
    password = "Testpassword1*"
    email = "hometestuser@example.com"
    
    # Check if user already exists and delete it
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    
    # Create user with confirmed email
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password(password)
    db.add(user)
    db.commit()
    
    # Login the user
    response = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/home"

def test_get_current_user(client, db):    # Create a unique user for this test
    user = User(username="testuser3", email="testuser3@example.com", email_confirmed=1)
    user.set_password("testpassword")
    db.add(user)
    db.commit()

    class MockRequest:
        def __init__(self):
            self.session = {"user_id": user.id}

    request = MockRequest()
    current_user = get_current_user(request, db)
    assert current_user is not None
    assert current_user.username == "testuser3"

def test_find_best_combination():
    scores = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [2, 2, 2, 2, 2, 2, 2, 2, 2],
        [3, 3, 3, 3, 3, 3, 3, 3, 3],
        [4, 4, 4, 4, 4, 4, 4, 4, 4]
    ]
    best_teams, min_difference_total = find_best_combination(scores)
    
    assert len(best_teams) == 1
    assert min_difference_total == 0

    # Check if the teams are balanced
    team1, team2 = best_teams[0]
    assert len(team1) == len(team2)


def test_build_player_scores_includes_goalkeeper_skill_when_enabled():
    players = [
        SimpleNamespace(
            velocidad=1,
            resistencia=2,
            control=3,
            pases=4,
            tiro=5,
            defensa=6,
            habilidad_arquero=9,
            fuerza_cuerpo=7,
            vision=8,
        )
    ]

    scores = build_player_scores(players, True)

    assert scores[0][6] == 9


def test_build_player_scores_ignores_goalkeeper_skill_when_disabled():
    players = [
        SimpleNamespace(
            velocidad=1,
            resistencia=2,
            control=3,
            pases=4,
            tiro=5,
            defensa=6,
            habilidad_arquero=9,
            fuerza_cuerpo=7,
            vision=8,
        )
    ]

    scores = build_player_scores(players, False)

    assert scores[0][6] == 0


def test_parse_goalkeeper_skill_flag():
    assert parse_goalkeeper_skill_flag(True) is True
    assert parse_goalkeeper_skill_flag(False) is False
    assert parse_goalkeeper_skill_flag("true") is True
    assert parse_goalkeeper_skill_flag("off") is False
    assert parse_goalkeeper_skill_flag(None) is True
