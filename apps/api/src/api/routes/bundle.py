import json
from typing import Optional
from fastapi import APIRouter, Query
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_data_bundle(
    limit_clusters: int = Query(200, ge=10, le=2000),
    limit_detections: int = Query(500, ge=10, le=5000),
    year: Optional[int] = Query(None, description="Optional year filter e.g. 2020 or 2025")
):
    """Serve the complete harmonized data bundle matching the frontend DemoEnvelope contract.
    
    Returns:
    - cells: raw detections + harmonised grid cells
    - calendar: raw daily series + harmonised daily series
    - clusters: key-value dictionary of clusters with member detections
    - provenance: datasets, parameters, run_id, git_sha
    """
    conn = get_duckdb_conn()
    try:
        # 1. Calendar
        where_year = f"WHERE year = {int(year)}" if year else ""
        daily_df = conn.execute(f"""
            SELECT date, raw_event_count, harmonized_event_count, interval_lo, interval_hi
            FROM daily_aggregates {where_year}
            ORDER BY date ASC
        """).df()
        
        cal_raw = [
            {"date": str(r["date"]), "count": int(r["raw_event_count"])}
            for _, r in daily_df.iterrows()
        ]
        cal_harm = [
            {
                "date": str(r["date"]),
                "count": int(r["harmonized_event_count"]),
                "lo": int(r["interval_lo"]) if r["interval_lo"] is not None else None,
                "hi": int(r["interval_hi"]) if r["interval_hi"] is not None else None
            }
            for _, r in daily_df.iterrows()
        ]
        
        # 2. Cells (Harmonized Grid Cells)
        where_cells_year = f"WHERE local_date LIKE '{int(year)}%'" if year else ""
        cells_df = conn.execute(f"""
            SELECT cell_id, centroid_lat, centroid_lon, event_count, corroborated_pct, max_frp, best_conf_label
            FROM grid_cells {where_cells_year}
            ORDER BY event_count DESC
            LIMIT {int(limit_clusters)}
        """).df()
        
        harmonised_cells = [
            {
                "cluster_id": str(r["cell_id"]),
                "centroid_lat": float(r["centroid_lat"]),
                "centroid_lon": float(r["centroid_lon"]),
                "event_count": int(r["event_count"]),
                "corroborated_pct": float(r["corroborated_pct"]),
                "max_frp": float(r["max_frp"]),
                "best_conf_class": str(r["best_conf_label"]).lower()
            }
            for _, r in cells_df.iterrows()
        ]
        
        # 3. Raw Detections
        where_det_year = f"WHERE local_date LIKE '{int(year)}%'" if year else ""
        det_df = conn.execute(f"""
            SELECT det_id, latitude, longitude, sensor_family, confidence_label, frp, ts_utc, cluster_id
            FROM canonical_detections {where_det_year}
            ORDER BY frp DESC
            LIMIT {int(limit_detections)}
        """).df()
        
        raw_detections = [
            {
                "det_id": str(r["det_id"]),
                "lat": float(r["latitude"]),
                "lon": float(r["longitude"]),
                "sensor_family": str(r["sensor_family"]),
                "conf_class": str(r["confidence_label"]).lower(),
                "frp_mw": float(r["frp"]),
                "ts_utc": str(r["ts_utc"]),
                "cluster_id": str(r["cluster_id"]) if r["cluster_id"] else ""
            }
            for _, r in det_df.iterrows()
        ]
        
        # 4. Clusters with member evidence
        where_clust_year = f"WHERE local_date LIKE '{int(year)}%'" if year else ""
        clust_df = conn.execute(f"""
            SELECT cluster_id, local_date, centroid_lat, centroid_lon, corroborated, event_score,
                   n_modis, n_viirs, max_frp, members_json
            FROM fire_clusters {where_clust_year}
            ORDER BY event_score DESC, max_frp DESC
            LIMIT {int(limit_clusters)}
        """).df()
        
        clusters_dict = {}
        for _, r in clust_df.iterrows():
            cid = str(r["cluster_id"])
            members_raw = json.loads(r.get("members_json") or "[]")
            formatted_members = [
                {
                    "det_id": str(m.get("det_id", "")),
                    "sensor": str(m.get("sensor") or m.get("sensor_family") or ""),
                    "platform": str(m.get("platform") or m.get("satellite") or ""),
                    "frp": float(m.get("frp", 0.0)),
                    "conf_class": {2: "high", 1: "nominal", 0: "low"}.get(m.get("conf_class"), str(m.get("conf_label", "nominal"))).lower(),
                    "ts_utc": str(m.get("ts_utc", ""))
                }
                for m in members_raw
            ]
            clusters_dict[cid] = {
                "cluster_id": cid,
                "local_date": str(r["local_date"]),
                "centroid": {"lat": float(r["centroid_lat"]), "lon": float(r["centroid_lon"])},
                "corroborated": bool(r["corroborated"]),
                "event_score": round(float(r["event_score"]), 3),
                "summary": {
                    "n_modis": int(r["n_modis"]),
                    "n_viirs": int(r["n_viirs"]),
                    "max_frp": round(float(r["max_frp"]), 1)
                },
                "members": formatted_members
            }
            
        # 5. Provenance
        meta_rows = conn.execute("SELECT run_id, parameters_json FROM pipeline_metadata ORDER BY created_at DESC LIMIT 1").fetchall()
        if meta_rows:
            run_id = meta_rows[0][0]
            git_sha = "main"
            params = json.loads(meta_rows[0][1])
        else:
            run_id = "initial"
            git_sha = "main"
            params = {"eps_km": "1.5", "timezone": "Asia/Dhaka"}

        return {
            "status": "ok",
            "data": {
                "cells": {
                    "raw": raw_detections,
                    "harmonised": harmonised_cells
                },
                "calendar": {
                    "raw": cal_raw,
                    "harmonised": cal_harm
                },
                "clusters": clusters_dict
            },
            "error": None,
            "provenance": {
                "datasets": ["MODIS_C6.1", "VIIRS_SNPP_C2", "VIIRS_NOAA20_C2", "VIIRS_NOAA21_C2"],
                "parameters": {str(k): str(v) for k, v in params.items()},
                "run_id": str(run_id),
                "git_sha": str(git_sha)
            }
        }
    finally:
        conn.close()
