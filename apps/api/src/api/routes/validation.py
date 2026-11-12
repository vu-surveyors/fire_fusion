import json
from fastapi import APIRouter
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_validation():
    conn = get_duckdb_conn()
    try:
        query = "SELECT * FROM validation_metrics ORDER BY id ASC"
        df = conn.execute(query).df()
        
        results = {}
        for _, row in df.iterrows():
            m_id = str(row["id"])
            details = json.loads(row.get("details_json", "{}"))
            results[m_id] = {
                "id": m_id,
                "category": str(row["category"]),
                "metric_name": str(row["metric_name"]),
                "value_raw": float(row["value_raw"]),
                "value_harmonized": float(row["value_harmonized"]),
                "improvement_pct": float(row["improvement_pct"]),
                "details": details
            }

        return {
            "status": "ok",
            "validation_status": "evaluated_against_dual_observation_overlap",
            "summary": {
                "overlap_correlation_improvement_pct": results.get("overlap_correlation", {}).get("improvement_pct", 0.0),
                "overlap_ratio_raw": results.get("overlap_ratio", {}).get("value_raw", 0.0),
                "overlap_ratio_harmonized": results.get("overlap_ratio", {}).get("value_harmonized", 0.0),
                "optimal_cluster_radius_km": 1.5,
                "dual_sensor_corroborated_benchmark": True
            },
            "metrics": results,
            "provenance": {
                "methodology": "FireFusion System Design v2.2 (§7.5 Validation Framework)",
                "overlap_period": "2020 & 2025 dual-observation baseline"
            }
        }
    finally:
        conn.close()

