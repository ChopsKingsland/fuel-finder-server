import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routers import stations
from api.database import pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup database connection pool on startup
    pool.open()
    yield
    # Close pool on shutdown
    pool.close()

app = FastAPI(
    title="Fuel Finder API",
    description="API for finding nearby fuel prices.",
    lifespan=lifespan
)

app.include_router(stations.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
