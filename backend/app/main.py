from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, get_db
import app.database as _db
from app.routers.auth import router as auth_router
from app.routers.countries import router as countries_router
from app.routers.indicators import router as indicators_router
from app.routers.macro_data import router as macro_data_router
from app.routers.datasets import router as datasets_router
from app.routers.connectors import router as connectors_router
from app.routers.catalog import router as catalog_router
from app.routers.surveys import router as surveys_router
from app.routers.schedules import router as schedules_router
from app.routers.health_sources import router as health_sources_router
from app.routers.rag import router as rag_router
from app.routers.search import router as search_router
from app.routers.sdg import router as sdg_router
from app.services.worldbank_connector import seed_countries, seed_indicators
from app.services.connector_service import seed_data_sources
from app.services.survey_service import seed_surveys
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.services.research_source_service import seed_research_sources
from app.routers.research import router as research_router
import app.connectors.tier1 # noqa: F401 — triggers all register_connector() calls
import app.connectors.tier2 # noqa: F401 — triggers all tier2 register_connector() calls
import app.connectors.tier3 # noqa: F401 — triggers all tier3 register_connector() calls
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.monitoring_middleware import MonitoringMiddleware, get_metrics

settings = get_settings()


def _bootstrap_macro_data_sync(db):
    """Bootstrap: sync each live-registry connector once if it has no data yet."""
    from app.models.macro_data import MacroData
    from app.connectors.registry import REGISTRY
    from app.services.connector_service import run_sync
    import logging
    log = logging.getLogger(__name__)
    live_sources = [sid for sid, meta in REGISTRY.items() if meta.get("connector_status") == "live"]
    for source_id in live_sources:
        try:
            has_data = db.query(MacroData).filter(MacroData.source_id == source_id).first() is not None
            if not has_data:
                run_sync(db, source_id)
        except Exception:
            log.warning("Bootstrap sync failed for %s (non-fatal)", source_id, exc_info=True)

def _run_startup_tasks():
    try:
        Base.metadata.create_all(bind=_db.engine, checkfirst=True)
        db = _db.SessionLocal()
        try:
            seed_countries(db)
            seed_indicators(db)
            seed_data_sources(db)
            seed_surveys(db)
            seed_research_sources(db)
            _bootstrap_macro_data_sync(db)
            start_scheduler(db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Startup task failed (non-fatal): %s", e, exc_info=True)
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Startup DB init failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run DB init/seeding + scheduler start in a background thread so the app
    # can start accepting requests (and pass Cloud Run health checks) right away,
    # instead of blocking ~45s on cold start before serving any traffic.
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_startup_tasks)
    yield
    stop_scheduler()

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
app.include_router(schedules_router, prefix="/api/v1")
app.include_router(health_sources_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(sdg_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": settings.app_version, "service": settings.app_name}

@app.get("/metrics", tags=["Ops"])
def metrics():
    return get_metrics()
