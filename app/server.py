"""FastAPI server entrypoint."""
import argparse
import logging
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import app.core.config as cfg
from app.routes import qa, sql, summarize, upsert

logger = logging.getLogger("log_analyzer_server")
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _patch_binary_upload_schema(node):
    """Convert JSON Schema contentMediaType upload hints to OpenAPI binary format."""
    if isinstance(node, dict):
        if node.get("type") == "string" and node.get("contentMediaType") == "application/octet-stream":
            node.pop("contentMediaType", None)
            node["format"] = "binary"
        for value in node.values():
            _patch_binary_upload_schema(value)
    elif isinstance(node, list):
        for value in node:
            _patch_binary_upload_schema(value)


def create_application() -> FastAPI:
    """Create and configure the FastAPI app."""
    app = FastAPI(
        title=cfg.PROJECT_NAME,
        description=cfg.PROJECT_DESCRIPTION,
        debug=cfg.DEBUG,
        version=cfg.VERSION,
    )
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.CORS_ALLOW_ORIGINS,
        allow_credentials=cfg.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(upsert.router, prefix="/upsert", tags=["upsert"])
    app.include_router(qa.router, prefix="/qa", tags=["qa"])
    app.include_router(sql.router, prefix="/sql", tags=["sql"])
    app.include_router(summarize.router, prefix="/summarize", tags=["summarize"])

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=cfg.PROJECT_NAME,
            version=cfg.VERSION,
            description=cfg.PROJECT_DESCRIPTION,
            routes=app.routes,
        )
        _patch_binary_upload_schema(schema)
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_application()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add per-request latency in response headers."""
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    return response


@app.get("/")
async def index():
    """Service root endpoint."""
    return {"message": "Log Analyzer API is running. Visit /docs for API documentation."}


@app.get("/healthz")
async def healthz():
    """Kubernetes-style liveness endpoint."""
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon for docs and browsers."""
    return FileResponse(path=str(STATIC_DIR / "favicon.ico"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start FastAPI with Uvicorn")
    parser.add_argument(
        "--ip",
        "--host_ip",
        dest="host_ip",
        type=str,
        default="0.0.0.0",
        help="host ip address. (default: %(default)s)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=cfg.API_SERVER_PORT,
        help="uvicorn port number. Overrides .env (default: %(default)s)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=1,
        help="number of uvicorn workers. (default: %(default)s)",
    )
    parser.add_argument(
        "-r",
        "--reload",
        action="store_true",
        help="enable reload in dev mode. (default: %(default)s)",
    )
    args = parser.parse_args()
    args.reload = False if args.workers > 1 else args.reload
    logger.info(
        "Starting uvicorn on %s:%s with %s worker(s)",
        args.host_ip,
        args.port,
        args.workers,
    )
    uvicorn.run(
        "app.server:app",
        host=args.host_ip,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        reload_dirs=["app"],
    )
