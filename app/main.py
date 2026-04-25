import os
import traceback
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.core.exceptions import AppException
from app.core.response import success_response
from app.database import engine
from app.admin.models import Admin  # noqa: F401
from app.clients.models import Client, Location  # noqa: F401
from app.clients.router import router as clients_router
from app.orders.models import Order, OrderItem  # noqa: F401
from app.orders.router import router as orders_router
from app.products.models import Product  # noqa: F401
from app.products.router import router as products_router

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Grocery Distribution API")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost").split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app-level startup and shutdown resources."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=APP_NAME,
    debug=DEBUG,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(products_router, prefix=API_V1_PREFIX)
app.include_router(clients_router, prefix=API_V1_PREFIX)
app.include_router(orders_router, prefix=API_V1_PREFIX)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500},
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": APP_ENV}


@app.get(f"{API_V1_PREFIX}/health", tags=["Health"])
async def versioned_health_check() -> dict[str, str]:
    return {"status": "ok", "environment": APP_ENV}


@app.get(f"{API_V1_PREFIX}/")
async def api_summary() -> dict:
    endpoints = [
        {"method": "POST", "path": "/api/v1/auth/admin/login"},
        {"method": "POST", "path": "/api/v1/auth/client/login"},
        {"method": "POST", "path": "/api/v1/admin/products"},
        {"method": "GET", "path": "/api/v1/admin/products"},
        {"method": "GET", "path": "/api/v1/admin/products/{product_id}"},
        {"method": "PATCH", "path": "/api/v1/admin/products/{product_id}"},
        {"method": "DELETE", "path": "/api/v1/admin/products/{product_id}"},
        {"method": "GET", "path": "/api/v1/products"},
        {"method": "GET", "path": "/api/v1/products/{product_id}"},
        {"method": "POST", "path": "/api/v1/admin/clients"},
        {"method": "GET", "path": "/api/v1/admin/clients"},
        {"method": "GET", "path": "/api/v1/admin/clients/{client_id}"},
        {"method": "PATCH", "path": "/api/v1/admin/clients/{client_id}"},
        {"method": "POST", "path": "/api/v1/admin/clients/{client_id}/locations"},
        {"method": "PATCH", "path": "/api/v1/admin/clients/{client_id}/locations/{location_id}"},
        {"method": "DELETE", "path": "/api/v1/admin/clients/{client_id}/locations/{location_id}"},
        {"method": "GET", "path": "/api/v1/me"},
        {"method": "GET", "path": "/api/v1/me/locations"},
        {"method": "POST", "path": "/api/v1/orders"},
        {"method": "GET", "path": "/api/v1/orders"},
        {"method": "GET", "path": "/api/v1/orders/{order_id}"},
        {"method": "GET", "path": "/api/v1/admin/orders"},
        {"method": "GET", "path": "/api/v1/admin/orders/{order_id}"},
        {"method": "PATCH", "path": "/api/v1/admin/orders/{order_id}/status"},
    ]
    return success_response(data=endpoints, message="API endpoints", status_code=200)
