from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# Reminder: configure redirect URIs in Google Cloud Console:
# - http://localhost:8000/auth/google/callback
# - https://<railway-domain>/auth/google/callback
config = Config(".env")
oauth = OAuth(config)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
