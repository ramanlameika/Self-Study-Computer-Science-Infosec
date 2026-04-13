"""Agency service FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import Base
from app.routes.agencies import router as agencies_router
from app.routes.gtfs import router as gtfs_router

app = FastAPI(
    title="OpenTransit Agency Service",
    description="Transit agency management and GTFS feed import for OpenTransit.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agencies_router)
app.include_router(gtfs_router)


@app.on_event("startup")
async def on_startup() -> None:
    from app.database import get_engine
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": settings.service_name}
