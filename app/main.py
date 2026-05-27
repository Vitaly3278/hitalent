import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.exceptions import AppError
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Organizational Structure API",
    description="API for managing departments and employees",
    version="1.0.0",
)
app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
def root() -> dict:
    return {
        "name": "Organizational Structure API",
        "description": "REST API для управления организационной структурой: дерево подразделений и сотрудники.",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "create_department": "POST /departments/",
            "create_employee": "POST /departments/{id}/employees/",
            "get_department": "GET /departments/{id}?depth=1&include_employees=true",
            "update_department": "PATCH /departments/{id}",
            "delete_department": "DELETE /departments/{id}?mode=cascade|reassign",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
