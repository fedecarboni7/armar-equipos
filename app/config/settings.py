import os
import pytz

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.secret_key = os.getenv("SECRET_KEY")
        self.logging_level = os.getenv("LOGGING_LEVEL", "INFO")
        self.brevo_api_key = os.getenv("BREVO_API_KEY")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
        self.arg_timezone = pytz.timezone("America/Argentina/Buenos_Aires")
        self.cron_secret = os.getenv("CRON_SECRET_TOKEN")
        self.sentry_dsn = os.getenv("SENTRY_DSN")
        self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        self.environment = os.getenv("ENVIRONMENT", "local")
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        self.r2_account_id = os.getenv("R2_ACCOUNT_ID")
        self.r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.r2_bucket_name = os.getenv("R2_BUCKET_NAME")
        self.r2_public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
