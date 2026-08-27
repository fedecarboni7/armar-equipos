from app.config.config import create_app
from app.routes.player_routes import router as player_router
from app.routes.auth_routes import router as auth_router
from app.routes.main_routes import router as main_router
from app.routes.clubs_routes import router as clubs_router
from app.routes.public_routes import router as public_router
from app.routes.admin_routes import router as admin_router
from app.routes.matches_routes import router as matches_router
from app.routes.health_routes import router as health_router

app = create_app()

app.include_router(player_router, tags=["player"])
app.include_router(auth_router, tags=["auth"])
app.include_router(main_router, tags=["main"])
app.include_router(clubs_router, tags=["clubs"])
app.include_router(public_router, tags=["public"])
app.include_router(admin_router, tags=["admin"])
app.include_router(matches_router, tags=["matches"])
app.include_router(health_router, tags=["health"])

if __name__ == "__main__":
    import uvicorn

    # Esta configuración se usa solo cuando ejecutas directamente con:
    # python -m app.main
    # Para desarrollo usa el debugger de VS Code
    # Para producción Railway usa: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    uvicorn.run(app, host="127.0.0.1", port=8000)
