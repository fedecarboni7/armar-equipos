import re


def validate_username(username: str):
    if len(username) < 3 or len(username) > 30:
        raise ValueError("El nombre de usuario debe tener entre 3 y 30 caracteres.")
    if not re.match(r"^[\w.@]+$", username):
        raise ValueError(
            "El nombre de usuario solo puede contener letras, números, guiones bajos y puntos."
        )


def validate_email(email: str):
    """Validate email format"""
    if not email:
        raise ValueError("El email es requerido.")

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValueError("El formato del email no es válido.")

    if len(email) > 254:  # RFC 5322 limit
        raise ValueError("El email es demasiado largo.")


def validate_password(password: str):
    if len(password) < 8 or len(password) > 30:
        raise ValueError("La contraseña debe tener entre 8 y 30 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"[0-9]", password):
        raise ValueError("La contraseña debe contener al menos un número.")
    if len(password) < 12 and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError(
            "La contraseña de menos de 12 caracteres debe contener al menos un carácter especial."
        )
