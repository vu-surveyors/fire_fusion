import os
from io import StringIO
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd

from src.db.session import get_duckdb_conn
from src.api.routes import (
    calendar,
    clusters,
    cells,
    validation,
    anomalies,
    summary,
    meta,
    brief,
    bundle
)

app = FastAPI(
    title="FireFusion Backend API",
    description="Scientific Spatio-Temporal Harmonization Engine for NASA MODIS and VIIRS Active Fire Hotspots (NASA Space Apps 2026 Challenge #9).",
    version="2.1.0"
)

# CORS configuration
origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://localhost:5522",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API routers
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["Calendar"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["Clusters"])
app.include_router(cells.router, prefix="/api/v1/cells", tags=["Grid Cells"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["Validation"])
app.include_router(anomalies.router, prefix="/api/v1/anomalies", tags=["Anomalies"])
app.include_router(summary.router, prefix="/api/v1/summary", tags=["Summary"])
app.include_router(brief.router, prefix="/api/v1/brief", tags=["Analyst Brief"])
app.include_router(bundle.router, prefix="/api/v1/bundle", tags=["Data Bundle"])
app.include_router(meta.router, prefix="/api/v1", tags=["Metadata & Health"])

# Root and backward-compatible endpoints
@app.get("/")
def root():
    return {
        "service": "FireFusion Harmonised Backend API",
        "challenge": "NASA Space Apps Challenge 2026 — Harmonization of MODIS and VIIRS Hot Spots",
        "docs": "/docs",
        "endpoints": {
            "calendar": "/api/v1/calendar",
            "clusters": "/api/v1/clusters",
            "cells": "/api/v1/cells",
            "validation": "/api/v1/validation",
            "anomalies": "/api/v1/anomalies",
            "baseline": "/api/v1/anomalies/baseline",
            "summary": "/api/v1/summary",
            "brief": "/api/v1/brief",
            "bundle": "/api/v1/bundle",
            "health": "/api/v1/health",
            "meta": "/api/v1/meta"
        }
    }


@app.get("/api/v1/hotspots")
def get_canonical_hotspots(
    limit: int = Query(5000, ge=1, le=20000),
    sensor: str = Query("all", description="'all', 'MODIS', or 'VIIRS'"),
    date: str = Query(None, description="Local date YYYY-MM-DD")
):
    """Backward compatibility endpoint returning canonical detections."""
    conn = get_duckdb_conn()
    try:
        where = ["1=1"]
        if sensor.lower() != "all":
            where.append(f"sensor_family = '{sensor.upper()}'")
        if date:
            where.append(f"local_date = '{date}'")
            
        where_sql = " AND ".join(where)
        query = f"""
            SELECT * FROM canonical_detections 
            WHERE {where_sql}
            ORDER BY ts_utc DESC 
            LIMIT {int(limit)}
        """
        df = conn.execute(query).df()
        return {"count": len(df), "data": df.to_dict(orient="records")}
    finally:
        conn.close()


@app.get("/api/v1/download/hotspots.csv")
def download_hotspots(year: int = Query(2025)):
    conn = get_duckdb_conn()
    try:
        query = f"SELECT * FROM canonical_detections WHERE local_date LIKE '{year}%' LIMIT 10000"
        df = conn.execute(query).df()
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=firefusion_hotspots_{year}.csv"}
        )
    finally:
        conn.close()


@app.get("/api/v1/download/calendar.csv")
def download_calendar(year: int = Query(2025)):
    """Export daily aggregates time-series as CSV."""
    conn = get_duckdb_conn()
    try:
        query = f"SELECT * FROM daily_aggregates WHERE year = {int(year)} ORDER BY date ASC"
        df = conn.execute(query).df()
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=firefusion_calendar_{year}.csv"}
        )
    finally:
        conn.close()


@app.post("/api/v1/pipeline/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Trigger an end-to-end compute pipeline execution in the background."""
    from src.compute.pipeline import run_pipeline
    
    background_tasks.add_task(run_pipeline)
    return {
        "status": "accepted",
        "message": "Harmonization pipeline execution scheduled in background."
    }
