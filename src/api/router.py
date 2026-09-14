from fastapi import APIRouter

from src.api.routes import calls, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(calls.router)
