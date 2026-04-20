import pytest
from app.db.models import User

# Test the signup endpoints
def test_get_signup(client):
    response = client.get("/signup")
    assert response.status_code == 200
    assert response.template.name == "signup.html"

@pytest.mark.brevo
def test_post_signup(client, db):
    username = "newuser1"
    password = "Newpassword1*"
    email = "newuser1@example.com"
    response = client.post("/signup", data={"username": username, "password": password, "email": email}, follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "email_confirmation_pending.html"

    db_user = db.query(User).filter(User.username == username).first()
    assert db_user is not None
    assert db_user.verify_password(password)
    assert db_user.email == email
    assert db_user.email_confirmed == 0
    assert db_user.email_confirmation_token is not None

    # Test that the user cannot be created again
    response = client.post("/signup", data={"username": username, "password": password, "email": email}, follow_redirects=False)
    assert response.status_code == 409
    assert response.context["error"] == "Usuario ya registrado"

    # Test that the same email cannot be used for another user
    response = client.post("/signup", data={"username": "newuser2", "password": password, "email": email}, follow_redirects=False)
    assert response.status_code == 409
    assert response.context["error"] == "Email ya registrado"


# Test the login endpoints
def test_get_login(client):
    response = client.get("/logout", follow_redirects=False)
    
    response = client.get("/login")
    assert response.status_code == 200
    assert response.template.name == "login.html"

def test_post_login(client, db):
    # Create a unique user for this test
    username = "logintest_user"
    password = "Testpassword1*"
    email = "logintest@example.com"
    
    # First check if the user already exists and delete it
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    # Create user with email and confirm it
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password(password)
    db.add(user)
    db.commit()

    response = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/home"

    # Test that the user cannot login with wrong password
    response = client.post("/login", data={"username": username, "password": "wrongpassword"}, follow_redirects=False)
    assert response.status_code == 401
    assert response.template.name == "login.html"
    assert "Usuario o contraseña incorrectos" in response.text

    # Test that the user cannot login with wrong username
    response = client.post("/login", data={"username": "wronguser", "password": password}, follow_redirects=False)
    assert response.status_code == 401
    assert response.template.name == "login.html"
    assert "Usuario o contraseña incorrectos" in response.text


# Test the logout endpoint
def test_logout(client):
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/login"


# Test the token endpoint
@pytest.fixture
def token_user(db):
    # Create a unique user for token tests
    username = "tokenuser"
    password = "Tokenpassword1*"
    email = "tokenuser@example.com"
    
    # Check if user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, email=email, email_confirmed=1)
        user.set_password(password)
        db.add(user)
        db.commit()
    
    return {"username": username, "password": password}

def test_create_token(client, token_user):
    response = client.post("/token", 
                          data={"username": token_user["username"], 
                                "password": token_user["password"]}, 
                          follow_redirects=False)
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"

def test_token_with_wrong_password(client, token_user):
    response = client.post("/token", 
                          data={"username": token_user["username"], 
                                "password": "wrongpassword"}, 
                          follow_redirects=False)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_token_with_wrong_username(client, token_user):
    response = client.post("/token", 
                          data={"username": "wronguser", 
                                "password": token_user["password"]}, 
                          follow_redirects=False)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_token_with_empty_credentials(client):
    response = client.post("/token", follow_redirects=False)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Field required"
    assert response.json()["detail"][1]["msg"] == "Field required"

def test_token_with_empty_username(client):
    response = client.post("/token", data={"password": "tokenpassword"}, follow_redirects=False)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Field required"

def test_token_with_empty_password(client):
    response = client.post("/token", data={"username": "tokenuser"}, follow_redirects=False)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Field required"

def test_signup_missing_email(client):
    """Test signup fails when email is missing"""
    username = "testuser"
    password = "Testpassword1*"
    response = client.post("/signup", data={"username": username, "password": password}, follow_redirects=False)
    assert response.status_code == 422  # FastAPI validation error

def test_signup_invalid_email(client):
    """Test signup fails with invalid email format"""
    username = "testuser"
    password = "Testpassword1*"
    email = "invalid-email"
    response = client.post("/signup", data={"username": username, "password": password, "email": email}, follow_redirects=False)
    assert response.status_code == 200  # Returns form with error
    assert "error" in response.context

@pytest.mark.brevo
def test_signup_valid_email_formats(client, db):
    """Test signup works with various valid email formats"""
    test_cases = [
        ("user1", "User1password!", "user1@example.com"),
        ("user2", "User2password!", "test.email+tag@example.org"),
        ("user3", "User3password!", "user_name@domain-name.co.uk"),
    ]
    
    for username, password, email in test_cases:
        # Clean up any existing user
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        response = client.post("/signup", data={"username": username, "password": password, "email": email}, follow_redirects=False)
        assert response.status_code == 200
        assert response.template.name == "email_confirmation_pending.html"
        
        # Verify user was created with correct email but not confirmed
        db_user = db.query(User).filter(User.username == username).first()
        assert db_user is not None
        assert db_user.email == email
        assert db_user.email_confirmed == 0


# Test password reset functionality
def test_forgot_password_get(client):
    """Test forgot password page loads correctly"""
    response = client.get("/forgot-password")
    assert response.status_code == 200
    assert response.template.name == "forgot_password.html"

@pytest.mark.brevo
def test_forgot_password_post_existing_email(client, db):
    """Test forgot password with existing email"""
    # Create a user with email
    username = "resetuser"
    email = "resetuser@example.com"
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    response = client.post("/forgot-password", data={"email": email}, follow_redirects=False)
    assert response.status_code == 200
    assert "success" in response.context

def test_forgot_password_post_nonexistent_email(client):
    """Test forgot password with non-existent email (should still show success for security)"""
    response = client.post("/forgot-password", data={"email": "nonexistent@example.com"}, follow_redirects=False)
    assert response.status_code == 200
    assert "success" in response.context

def test_forgot_password_invalid_email(client):
    """Test forgot password with invalid email format"""
    response = client.post("/forgot-password", data={"email": "invalid-email"}, follow_redirects=False)
    assert response.status_code == 200
    assert "error" in response.context

def test_reset_password_get_valid_token(client, db):
    """Test reset password page with valid token"""
    # Create a user and a reset token
    from app.utils.email_service import PasswordResetService
    username = "resetuser"
    email = "resetuser@example.com"
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password("Oldpassword1*")
    db.add(user)
    db.commit()
    
    # Create a reset token
    token = PasswordResetService.create_reset_token(db, user.id)
    
    response = client.get(f"/reset-password/{token}")
    assert response.status_code == 200
    assert response.template.name == "reset_password.html"
    assert "token" in response.context

def test_reset_password_get_invalid_token(client):
    """Test reset password page with invalid token"""
    response = client.get("/reset-password/invalid-token")
    assert response.status_code == 200
    assert response.template.name == "reset_password.html"
    assert "error" in response.context

def test_reset_password_post_valid_token(client, db):
    """Test password reset with valid token"""
    from app.utils.email_service import PasswordResetService
    
    username = "resetuser2"
    email = "resetuser2@example.com"
    old_password = "Oldpassword1*"
    new_password = "Newpassword1*"
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password(old_password)
    db.add(user)
    db.commit()
    
    # Create a reset token
    token = PasswordResetService.create_reset_token(db, user.id)
    
    response = client.post(f"/reset-password/{token}", 
                          data={"new_password": new_password, "confirm_password": new_password}, 
                          follow_redirects=False)
    assert response.status_code == 200
    assert "success" in response.context
    
    # Verify password was changed
    db.refresh(user)
    assert user.verify_password(new_password)
    assert not user.verify_password(old_password)

def test_reset_password_post_mismatched_passwords(client, db):
    """Test password reset with mismatched passwords"""
    from app.utils.email_service import PasswordResetService
    
    username = "resetuser3"
    email = "resetuser3@example.com"
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password("Oldpassword1*")
    db.add(user)
    db.commit()
    
    token = PasswordResetService.create_reset_token(db, user.id)
    
    response = client.post(f"/reset-password/{token}", 
                          data={"new_password": "Newpassword1*", "confirm_password": "DifferentPassword1*"}, 
                          follow_redirects=False)
    assert response.status_code == 200
    assert "error" in response.context

def test_reset_password_post_invalid_token(client):
    """Test password reset with invalid token"""
    response = client.post("/reset-password/invalid-token", 
                          data={"new_password": "Newpassword1*", "confirm_password": "Newpassword1*"}, 
                          follow_redirects=False)
    assert response.status_code == 200
    assert "error" in response.context


# Test profile email update functionality  
@pytest.mark.brevo
def test_profile_update_email(client, db):
    """Test updating user email in profile"""
    username = "profileuser"
    old_email = "old@example.com"
    new_email = "new@example.com"
    user = User(username=username, email=old_email, email_confirmed=1)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Login the user
    response = client.post("/login", data={"username": username, "password": "Testpassword1*"}, follow_redirects=False)
    assert response.status_code == 302
    
    response = client.post("/perfil/update-email", data={"email": new_email}, follow_redirects=False)
    assert response.status_code == 200
    assert "success" in response.context
    
    # Verify email was updated
    db.refresh(user)
    assert user.email == new_email

def test_profile_update_email_duplicate(client, db):
    """Test updating email to one that already exists"""
    # Create two users
    user1 = User(username="user1", email="user1@example.com", email_confirmed=1)
    user1.set_password("Testpassword1*")
    user2 = User(username="user2", email="user2@example.com", email_confirmed=1)
    user2.set_password("Testpassword1*")
    
    db.add_all([user1, user2])
    db.commit()
    
    # Login as user2
    response = client.post("/login", data={"username": "user2", "password": "Testpassword1*"}, follow_redirects=False)
    assert response.status_code == 302
    
    # Try to update user2's email to user1's email
    response = client.post("/perfil/update-email", data={"email": "user1@example.com"}, follow_redirects=False)
    assert response.status_code == 200
    assert "error" in response.context
    assert "ya está registrado" in response.context["error"]

# Test email confirmation functionality
def test_login_with_unconfirmed_email(client, db):
    """Test that users with unconfirmed email cannot login"""
    username = "unconfirmed_user"
    password = "Testpassword1*"
    email = "unconfirmed@example.com"
    
    # Create user without confirming email
    user = User(username=username, email=email, email_confirmed=0)
    user.set_password(password)
    db.add(user)
    db.commit()
    
    # Try to login - should fail
    response = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert response.status_code == 401
    assert response.template.name == "login.html"
    assert "Debes confirmar tu email" in response.context["error"]
    assert response.context["email_not_confirmed"] == True
    assert response.context["user_email"] == email

def test_confirm_email_with_valid_token(client, db):
    """Test email confirmation with valid token"""
    from app.utils.security import create_email_confirmation_token
    
    username = "confirm_user"
    email = "confirm@example.com"
    
    # Create user with unconfirmed email
    user = User(username=username, email=email, email_confirmed=0)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Create confirmation token
    token = create_email_confirmation_token(db, user)
    
    # Confirm email
    response = client.get(f"/confirm-email/{token}", follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "login.html"
    assert "Email confirmado exitosamente" in response.context["success"]
    
    # Verify user is now confirmed
    db.refresh(user)
    assert user.email_confirmed == 1
    assert user.email_confirmation_token is None

def test_confirm_email_with_invalid_token(client):
    """Test email confirmation with invalid token"""
    response = client.get("/confirm-email/invalid-token", follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "signup.html"
    assert "no es válido o ha expirado" in response.context["error"]
    assert response.context["invalid_token"] == True

@pytest.mark.brevo
def test_resend_confirmation_email(client, db):
    """Test resending confirmation email"""
    username = "resend_user"
    email = "resend@example.com"
    
    # Create user with unconfirmed email
    user = User(username=username, email=email, email_confirmed=0)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Resend confirmation email
    response = client.post("/resend-confirmation", data={"email": email}, follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "email_confirmation_pending.html"
    assert "recibirás un nuevo enlace" in response.context["success"]

def test_resend_confirmation_email_nonexistent(client):
    """Test resending confirmation to non-existent email"""
    response = client.post("/resend-confirmation", data={"email": "nonexistent@example.com"}, follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "email_confirmation_pending.html"
    assert "recibirás un nuevo enlace" in response.context["success"]  # Security: don't reveal if email exists

def test_resend_confirmation_already_confirmed(client, db):
    """Test resending confirmation to already confirmed email"""
    username = "confirmed_user"
    email = "confirmed@example.com"
    
    # Create user with confirmed email
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Try to resend confirmation
    response = client.post("/resend-confirmation", data={"email": email}, follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "email_confirmation_pending.html"
    assert "recibirás un nuevo enlace" in response.context["success"]  # Security: same message for all cases

@pytest.mark.brevo
def test_profile_resend_email_confirmation(client, db):
    """Test resending email confirmation from profile page"""
    username = "profile_resend_user"
    email = "profileresend@example.com"
    
    # Create user with unconfirmed email
    user = User(username=username, email=email, email_confirmed=0)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Manually confirm email to allow login, then revert it back
    user.email_confirmed = 1
    db.commit()
    
    # Login the user
    response = client.post("/login", data={"username": username, "password": "Testpassword1*"}, follow_redirects=False)
    assert response.status_code == 302
    
    # Set email back to unconfirmed to test resend functionality
    user.email_confirmed = 0
    db.commit()
    
    # Try to resend confirmation from profile
    response = client.post("/perfil/resend-email-confirmation", follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "profile.html"
    assert "Email de confirmación reenviado exitosamente" in response.context["success"]
    assert response.context["email_pending_confirmation"] == True

def test_profile_resend_email_confirmation_no_email(client, db):
    """Test resending confirmation from profile when user has no email"""
    username = "no_email_user"
    
    # Create user without email (legacy user)
    user = User(username=username)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Login the user (should work for legacy users)
    response = client.post("/login", data={"username": username, "password": "Testpassword1*"}, follow_redirects=False)
    assert response.status_code == 302
    
    # Try to resend confirmation from profile
    response = client.post("/perfil/resend-email-confirmation", follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "profile.html"
    assert "No tienes un email configurado" in response.context["error"]

def test_profile_resend_email_confirmation_already_confirmed(client, db):
    """Test resending confirmation from profile when email is already confirmed"""
    username = "confirmed_profile_user"
    email = "confirmedprofile@example.com"
    
    # Create user with confirmed email
    user = User(username=username, email=email, email_confirmed=1)
    user.set_password("Testpassword1*")
    db.add(user)
    db.commit()
    
    # Login the user
    response = client.post("/login", data={"username": username, "password": "Testpassword1*"}, follow_redirects=False)
    assert response.status_code == 302
    
    # Try to resend confirmation from profile
    response = client.post("/perfil/resend-email-confirmation", follow_redirects=False)
    assert response.status_code == 200
    assert response.template.name == "profile.html"
    assert "Tu email ya está confirmado" in response.context["error"]
