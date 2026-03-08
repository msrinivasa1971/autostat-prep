from fastapi import FastAPI

from app.api.routes import router
from app.config import APP_TITLE, APP_VERSION
from app.utils.logging_config import get_logger

logger = get_logger("autostat_prep")

app = FastAPI(
    title=APP_TITLE,
    description=(
        "AutoStat Prep — converts messy survey datasets into normalized "
        "statistical datasets for analysis by AutoStat."
    ),
    version=APP_VERSION,
)

app.include_router(router)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "service": "autostat-prep", "version": APP_VERSION}
