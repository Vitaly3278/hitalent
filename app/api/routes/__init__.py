from fastapi import APIRouter

from app.api.routes import departments

api_router = APIRouter()
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
