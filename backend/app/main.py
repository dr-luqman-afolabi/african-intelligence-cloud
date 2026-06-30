from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.routers.auth import router as auth_router
from app.routers.countries import router as countries_router
from app.routers.indicators import router as indicators_router
from app.routers.macro_data import router as macro_data_router
from app.routers.datasets import router as datasets_router
from app.routers.connectors import router as connectors_router
from app.routers.catalog import router as catalog_router
from app.routers.surveys import router as surveys_router
from app.services.worldbank_connector import seed_countries, seed_indicators
from app.services.connector_service import seed_data_sources
from app.services.survey_service import seed_surveys
import app.connectors.tier1  # noqa: F401 — triggers all register_connector() calls
import app.connectors.tier2  # noqa: F401 — triggers all tier2 register_connector() calls
import app.connectors.tier3  # noqa: F401 — triggers all tier3 register_connector() calls
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.monitoring_middleware import MonitoringMiddleware, get_metrics

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine, checkfirst=True)
    db = SessionLocal()
    try:
        seed_countries(db)
        seed_indicators(db)
        seed_data_sources(db)
        seed_surveys(db)
    except Exception:
        pass
    finally:
        db.close()
    yield


app = FastAPI(
    title="African Intelligence Cloud API",
    description="Macroeconomic data, analytics, and policy intelligence for Africa",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Starlette applies middleware LIFO — MonitoringMiddleware added first becomes innermost
app.add_middleware(MonitoringMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(countries_router, prefix="/api/v1")
app.include_router(indicators_router, prefix="/api/v1")
app.include_router(macro_data_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1")
app.include_router(connectors_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(surveys_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": settings.app_version, "service": settings.app_name}


@app.get("/metrics", tags=["Ops"])
def metrics():
    return get_metrics()
