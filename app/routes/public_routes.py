from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/robots.txt")
async def get_robots():
    robots_path = Path("static/robots.txt")
    return FileResponse(
        robots_path,
        media_type="text/plain",
        headers={"Content-Disposition": "inline"}
    )

@router.get("/sitemap.xml")
async def get_sitemap():
    sitemap_path = Path("static/sitemap.xml")
    return FileResponse(
        sitemap_path,
        media_type="application/xml",
        headers={"Content-Disposition": "inline"}
    )

@router.get("/service-worker.js")
async def get_service_worker():
    service_worker_path = Path("static/service-worker.js")
    return FileResponse(
        service_worker_path,
        media_type="application/javascript",
        headers={
            "Content-Disposition": "inline",
            "Service-Worker-Allowed": "/",
        },
    )
