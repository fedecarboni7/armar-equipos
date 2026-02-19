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
        self.run_db_migration = os.getenv("RUN_DB_MIGRATION", "false").lower() == "true"
        self.arg_timezone = pytz.timezone("America/Argentina/Buenos_Aires")
        self.cron_secret = os.getenv("CRON_SECRET_TOKEN")
        self.sentry_dsn = os.getenv("SENTRY_DSN")
        self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
