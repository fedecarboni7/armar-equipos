import sentry_sdk
from fastapi import Depends, FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config.logging_config import configure_logging
from app.config.settings import Settings
from app.db.models import User
from app.utils.auth import get_current_user
from app.utils.security import verify_admin_user

templates = Jinja2Templates(directory="templates")

def create_app() -> FastAPI:
    # Configuración de logging
    configure_logging()

    settings = Settings()
    secret_key = settings.secret_key

    # Configuración de Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            send_default_pii=True,
            enable_logs=True,
            traces_sample_rate=1.0,
            profile_session_sample_rate=1.0,
            profile_lifecycle="trace",
        )

    app = FastAPI(title="Armar Equipos", docs_url=None, redoc_url=None, openapi_url=None)

    app.add_middleware(SessionMiddleware, secret_key=secret_key)
    
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code in [405]:  # Not Found y Method Not Allowed
            return RedirectResponse(url="/home")
        
        if exc.status_code == 404:
            return templates.TemplateResponse(request=request, name="404.html", status_code=404, context={"error": exc.detail})

        if exc.status_code == 500:
            return templates.TemplateResponse(request=request, name="500.html", status_code=500)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.status_code,
                "detail": exc.detail
            }
        )
    
    @app.get("/docs", include_in_schema=False)
    async def get_documentation(current_user: User = Depends(get_current_user)):
        verify_admin_user(current_user, detail="Unauthorized: /docs")
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi(current_user: User = Depends(get_current_user)):
        verify_admin_user(current_user, detail="Unauthorized: /openapi.json")
        return app.openapi()

    return app