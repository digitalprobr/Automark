from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from pathlib import Path
import traceback

from .core.config import settings
from .api.routes import router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage exists for logs
LOG_DIR = Path(__file__).resolve().parents[2] / "storage"
LOG_DIR.mkdir(parents=True, exist_ok=True)
ERROR_LOG = LOG_DIR / "errors.log"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"Request: {request.method} {request.url}\n")
            f.write(tb + "\n")
            f.flush()
    except Exception:
        logging.exception("Failed to write to error log")
    logging.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


app.include_router(router, prefix=settings.api_prefix)
