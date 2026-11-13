import json
from fastapi import APIRouter
from src.db.session import get_duckdb_conn, DB_PATH

router = APIRouter()

@router.get("/health")
def health():
    conn = get_duckdb_conn()
    try:
        n_det = conn.execute("SELECT COUNT(*) FROM canonical_detections").fetchall()[0][0]
        n_clust = conn.execute("SELECT COUNT(*) FROM fire_clusters").fetchall()[0][0]
        n_daily = conn.execute("SELECT COUNT(*) FROM daily_aggregates").fetchall()[0][0]
        
        return {
            "status": "ok",
            "service": "FireFusion Harmonised Backend API",
            "database": "DuckDB",
            "database_file": str(DB_PATH.name),
            "records": {
                "canonical_detections": n_det,
                "fire_clusters": n_clust,
                "daily_aggregates": n_daily
            },
            "harmonization_engine": "DBSCAN Spatio-Temporal + Poisson GLM"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }
    finally:
        conn.close()


@router.get("/meta")
def get_metadata():
    conn = get_duckdb_conn()
    try:
        _meta_rows = conn.execute("SELECT * FROM pipeline_metadata ORDER BY created_at DESC LIMIT 1").fetchall()
        meta_row = _meta_rows[0] if _meta_rows else None
        if meta_row:
            params = json.loads(meta_row[6])
            run_id = meta_row[0]
            created_at = meta_row[1]
        else:
            params = {}
            run_id = "initial"
            created_at = None

        return {
            "project": "FireFusion",
            "challenge": "NASA Space Apps Challenge 2026 #9 — Harmonization of MODIS and VIIRS Hot Spots",
            "team": "VU_Surveyors",
            "license": "Apache-2.0",
            "pipeline_run_id": run_id,
            "pipeline_timestamp": created_at,
            "datasets": [
                {
                    "name": "MODIS Active Fire (C6.1)",
                    "platforms": ["Terra", "Aqua"],
                    "resolution": "1 km",
                    "source": "NASA FIRMS"
                },
                {
                    "name": "VIIRS Active Fire (Collection 2)",
                    "platforms": ["Suomi-NPP", "NOAA-20", "NOAA-21"],
                    "resolution": "375 m",
                    "source": "NASA FIRMS"
                }
            ],
            "parameters": params,
            "disclaimer": "FireFusion is an exploratory analytical platform developed for satellite thermal anomaly research and trend analysis. It is not an operational tactical wildfire prediction tool or real-time evacuation system."
        }
    finally:
        conn.close()

