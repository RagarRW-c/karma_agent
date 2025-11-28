from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from .db import check_db_connection


app = FastAPI(
    title="Cat Food Price Agent API",
    version="0.1.0",
    description="API do monitorowania cen karmy dla kota."
)


class HealthResponse(BaseModel):
    status: str
    services: List[str]


class DBHealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        services=["api"]
    )


@app.get("/db-health", response_model=DBHealthResponse)
async def db_health_check():
    ok = check_db_connection()
    return DBHealthResponse(status="ok" if ok else "error")
