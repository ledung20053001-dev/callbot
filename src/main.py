from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.exception_handlers import register_exception_handlers
from src.api.router import api_router
from src.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )
    application.include_router(api_router)
    register_exception_handlers(application)
    ui_directory = Path(__file__).parent / "ui"

    @application.get("/internal", include_in_schema=False)
    @application.get("/internal/", include_in_schema=False)
    async def internal_ui() -> FileResponse:
        return FileResponse(
            ui_directory / "index.html",
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    application.mount(
        "/internal",
        StaticFiles(directory=ui_directory, html=True),
        name="internal-ui",
    )
    return application


app = create_app()
