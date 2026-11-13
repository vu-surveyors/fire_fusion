import os
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import duckdb

from src.db.session import DB_PATH, init_db, get_duckdb_conn
from src.compute.normalise import run_canonical_normalisation
from src.compute.cluster import cluster_detections
from src.compute.calibrate import fit_sensor_calibration, compute_daily_aggregates, compute_grid_cells
from src.compute.baseline import compute_seasonal_baselines
from src.compute.validate import compute_validation_suite

def run_full_pipeline(data_dir: Path, eps_km: float = 1.5) -> Dict[str, Any]:
    """
    Executes the 5-stage FireFusion harmonisation pipeline:
    1. Canonical Normalisation
    2. Spatio-Temporal Clustering (DBSCAN)
    3. Calibration & Daily Aggregation
    4. Seasonal Baseline & Anomaly Engine
    5. Validation Suite
    Persists results directly into DuckDB and Parquet cache.
    """
    run_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    print(f"=== Starting FireFusion Harmonisation Pipeline (Run ID: {run_id}) ===")

    # 1. Canonical Normalisation
    print("[1/5] Running Canonical Normalisation on 2020 & 2025 datasets...")
    t0 = time.time()
    df_detections = run_canonical_normalisation(data_dir)
    print(f"      Normalized {len(df_detections)} detections in {time.time() - t0:.2f}s")

    # 2. Spatio-Temporal Clustering
    print(f"[2/5] Running Spatio-Temporal DBSCAN Clustering (eps={eps_km} km)...")
    t0 = time.time()
    df_detections, df_clusters = cluster_detections(df_detections, eps_km=eps_km)
    n_corroborated = int(df_clusters["corroborated"].sum()) if not df_clusters.empty else 0
    print(f"      Formed {len(df_clusters)} fire event clusters ({n_corroborated} corroborated) in {time.time() - t0:.2f}s")

    # 3. Calibration
    print("[3/5] Fitting Poisson GLM calibration & calculating daily/grid aggregates...")
    t0 = time.time()
    calibration = fit_sensor_calibration(df_clusters)
    df_daily = compute_daily_aggregates(df_detections, df_clusters, calibration)
    df_cells = compute_grid_cells(df_clusters, cell_size_deg=0.1)
    print(f"      Calculated {len(df_daily)} daily series and {len(df_cells)} grid cells in {time.time() - t0:.2f}s")

    # 4. Seasonal Baseline & Anomaly
    print("[4/5] Computing rolling seasonal baseline and anomaly percentiles...")
    t0 = time.time()
    df_daily = compute_seasonal_baselines(df_daily, window_days=7)
    anomalies_count = int(df_daily["is_anomaly"].sum())
    print(f"      Identified {anomalies_count} seasonal thermal anomalies in {time.time() - t0:.2f}s")

    # 5. Validation Suite
    print("[5/5] Generating cross-sensor validation metrics...")
    t0 = time.time()
    validation_records = compute_validation_suite(df_detections, df_clusters, df_daily)
    print(f"      Generated {len(validation_records)} validation benchmarks in {time.time() - t0:.2f}s")

    # 6. Database Storage in DuckDB
    print(f"[DB] Persisting all entities into DuckDB at: {DB_PATH}")
    t0 = time.time()
    
    # Ensure any connection pool is released before direct bulk insert
    from src.db.session import engine
    engine.dispose()

    conn = get_duckdb_conn(read_only=False)
    try:
        # Fast bulk ingestion into DuckDB tables using register / insert BY NAME
        conn.register("df_det_temp", df_detections)
        conn.execute("DELETE FROM canonical_detections")
        conn.execute("INSERT INTO canonical_detections BY NAME SELECT * FROM df_det_temp")
        conn.unregister("df_det_temp")

        conn.register("df_clust_temp", df_clusters)
        conn.execute("DELETE FROM fire_clusters")
        conn.execute("INSERT INTO fire_clusters BY NAME SELECT * FROM df_clust_temp")
        conn.unregister("df_clust_temp")

        conn.register("df_daily_temp", df_daily)
        conn.execute("DELETE FROM daily_aggregates")
        conn.execute("INSERT INTO daily_aggregates BY NAME SELECT * FROM df_daily_temp")
        conn.unregister("df_daily_temp")

        conn.register("df_cells_temp", df_cells)
        conn.execute("DELETE FROM grid_cells")
        conn.execute("INSERT INTO grid_cells BY NAME SELECT * FROM df_cells_temp")
        conn.unregister("df_cells_temp")

        df_val = pd.DataFrame(validation_records)
        conn.register("df_val_temp", df_val)
        conn.execute("DELETE FROM validation_metrics")
        conn.execute("INSERT INTO validation_metrics BY NAME SELECT * FROM df_val_temp")
        conn.unregister("df_val_temp")

        # Provenance metadata
        meta_record = {
            "run_id": run_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "records_raw": len(df_detections),
            "records_canonical": len(df_detections),
            "records_clusters": len(df_clusters),
            "records_daily": len(df_daily),
            "parameters_json": json.dumps({
                "eps_km": eps_km,
                "calibration": calibration,
                "area_bbox": [88.0, 20.0, 93.0, 27.0],
                "years": [2020, 2025]
            })
        }
        df_meta = pd.DataFrame([meta_record])
        conn.register("df_meta_temp", df_meta)
        conn.execute("DELETE FROM pipeline_metadata")
        conn.execute("INSERT INTO pipeline_metadata BY NAME SELECT * FROM df_meta_temp")
        conn.unregister("df_meta_temp")

        print(f"      DuckDB database successfully populated in {time.time() - t0:.2f}s")
    finally:
        conn.close()

    # 7. Write Parquet Cache for Offline Fast Delivery
    cache_dir = DB_PATH.parent.parent / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    df_clusters.to_parquet(cache_dir / "clusters.parquet", index=False)
    df_daily.to_parquet(cache_dir / "daily.parquet", index=False)
    df_cells.to_parquet(cache_dir / "cells.parquet", index=False)
    print(f"[Cache] Parquet caches written to {cache_dir}")

    total_time = round(time.time() - start_time, 2)
    print(f"=== Pipeline Complete in {total_time}s! ===")

    return {
        "status": "success",
        "run_id": run_id,
        "duration_seconds": total_time,
        "counts": {
            "detections": len(df_detections),
            "clusters": len(df_clusters),
            "corroborated_clusters": n_corroborated,
            "daily_series": len(df_daily),
            "grid_cells": len(df_cells),
            "anomalies": anomalies_count
        },
        "calibration": calibration
    }

def run_pipeline() -> Dict[str, Any]:
    """Convenience entrypoint for API and background task execution."""
    from src.db.session import BASE_DIR
    data_dir = BASE_DIR / "data"
    return run_full_pipeline(data_dir)


if __name__ == "__main__":
    from src.db.session import BASE_DIR
    data_dir = BASE_DIR / "data"
    res = run_full_pipeline(data_dir)
    print(json.dumps(res, indent=2))
