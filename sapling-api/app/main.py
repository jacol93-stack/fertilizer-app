import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.rate_limit import limiter, rate_limit_middleware
from app.routers import analysis_v2, blends, soil, materials, clients, crop_norms, reports, admin, quotes, programmes_v2, leaf, sessions, dashboard, workbench


class _JsonLogFormatter(logging.Formatter):
    """Minimal JSON log formatter. No extra dependency — stdlib logging only.

    Emits one JSON object per line with timestamp, level, logger name, message,
    and any extras attached via logger.info(..., extra={...}). Good enough
    to pipe into CloudWatch/Loki/Datadog without a full python-json-logger
    install. Swap for python-json-logger later if schemas need to be stricter.
    """

    _BUILTIN_ATTRS = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for key, val in record.__dict__.items():
            if key in self._BUILTIN_ATTRS or key.startswith("_"):
                continue
            try:
                json.dumps(val)
                payload[key] = val
            except (TypeError, ValueError):
                payload[key] = repr(val)
        return json.dumps(payload, default=str)


def _configure_logging() -> None:
    """Install the JSON formatter on the root logger if nothing else has
    configured logging yet. Respects $LOG_LEVEL (default INFO). Idempotent."""
    root = logging.getLogger()
    if getattr(root, "_sapling_json_configured", False):
        return
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonLogFormatter())
    # Replace default handlers so we don't double-log.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(level)
    root._sapling_json_configured = True  # type: ignore[attr-defined]


_configure_logging()
logger = logging.getLogger("sapling")

METRICS_INTERVAL_SECONDS = 300  # 5 minutes
METRICS_RETENTION_DAYS = 7


async def _collect_metrics_loop():
    """Background task: collect VPS metrics every 5 minutes, clean old rows."""
    from app.services.vps_metrics import get_all_metrics
    from app.supabase_client import get_supabase_admin

    while True:
        await asyncio.sleep(METRICS_INTERVAL_SECONDS)
        try:
            metrics = get_all_metrics()
            if metrics:
                # Remove human-readable fields before DB insert
                metrics.pop("uptime_human", None)
                sb = get_supabase_admin()
                sb.table("vps_metrics_history").insert(metrics).execute()

                # Clean old rows
                cutoff = (datetime.now(timezone.utc) - timedelta(days=METRICS_RETENTION_DAYS)).isoformat()
                sb.table("vps_metrics_history").delete().lt("recorded_at", cutoff).execute()
        except Exception as e:
            logger.warning(f"Metrics collection failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_collect_metrics_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Sapling API", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS: only allow known origins ---
_allowed_origins = [
    "https://app.saplingfertilizer.co.za",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # `Content-Disposition` is NOT a CORS-safelisted response header, so
    # without exposing it explicitly the browser hides it from JS — and
    # our PDF download helper falls back to a generic filename. Expose
    # the headers the frontend needs to see.
    expose_headers=["Content-Disposition", "Content-Length"],
)


# --- Tiered rate limiting (path-classified) ---
# Registered as a plain @middleware decorator below; no per-route decorations
# needed. Rules live in app/rate_limit.py.
app.middleware("http")(rate_limit_middleware)


# --- Correlation ID + request logging middleware ---
# Attach an X-Correlation-ID to every request (honoring any inbound value so
# that upstream proxies / the frontend can trace a single user action across
# the stack). Log request start/finish as structured JSON records. Keeps
# audit trail lean — one line in, one line out, with duration_ms and status.

@app.middleware("http")
async def _request_logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
    request.state.correlation_id = correlation_id
    start = time.perf_counter()
    logger.info(
        "request.start",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request.error",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        "request.finish",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

app.include_router(blends.router, prefix="/api/blends", tags=["Blends"])
app.include_router(soil.router, prefix="/api/soil", tags=["Soil Analysis"])
app.include_router(materials.router, prefix="/api/materials", tags=["Materials"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(crop_norms.router, prefix="/api/crop-norms", tags=["Crop Norms"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["Quotes"])
app.include_router(programmes_v2.router, prefix="/api", tags=["Programmes v2"])
app.include_router(analysis_v2.router, prefix="/api/analysis/v2", tags=["Quick Analysis v2"])
app.include_router(leaf.router, prefix="/api/leaf", tags=["Leaf Analysis"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(dashboard.router, prefix="/api/admin/dashboard", tags=["Dashboard"])
app.include_router(workbench.router, prefix="/api/workbench", tags=["Workbench"])


# --- Sanitize unhandled exceptions in production ---
@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    """Return a generic error in production; include details only in dev."""
    if os.environ.get("ENV", "production") == "development":
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health():
    """Liveness probe. Returns 503 if the database is unreachable so that
    load balancers and the Docker HEALTHCHECK can route around a broken
    instance instead of serving errors from it."""
    try:
        from app.supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        sb.table("profiles").select("id").limit(1).execute()
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    return {
        "status": "ok",
        "database": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
