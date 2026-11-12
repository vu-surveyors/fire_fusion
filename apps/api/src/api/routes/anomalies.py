from typing import Optional
from fastapi import APIRouter, Query
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_anomalies(
    min_percentile: float = Query(85.0, description="Minimum anomaly percentile (0-100)"),
    year: Optional[int] = Query(None, description="Filter by year (2020 or 2025)"),
    limit: int = Query(100, ge=1, le=500)
):
    conn = get_duckdb_conn()
    try:
        where_clauses = [f"anomaly_percentile >= {float(min_percentile)}"]
        if year is not None:
            where_clauses.append(f"year = {int(year)}")

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT 
                date,
                year,
                day_of_year,
                raw_event_count,
                harmonized_event_count,
                baseline_median,
                baseline_p90,
                anomaly_percentile,
                is_anomaly,
                max_frp,
                total_frp_mw
            FROM daily_aggregates
            WHERE {where_sql}
            ORDER BY anomaly_percentile DESC, harmonized_event_count DESC
            LIMIT {int(limit)}
        """
        df = conn.execute(query).df()
        records = df.to_dict(orient="records")

        return {
            "status": "ok",
            "count": len(records),
            "baseline_method": "rolling_window_median_and_p90",
            "data": records,
            "disclaimer": "Thermal anomalies indicate statistical historical rarity only. This is not a tactical wildfire spread forecast."
        }
    finally:
        conn.close()


@router.get("/baseline")
def get_baseline():
    conn = get_duckdb_conn()
    try:
        query = """
            SELECT 
                day_of_year,
                AVG(baseline_median) as baseline_median,
                AVG(baseline_p90) as baseline_p90,
                AVG(harmonized_event_count) as avg_harmonized_count
            FROM daily_aggregates
            GROUP BY day_of_year
            ORDER BY day_of_year ASC
        """
        df = conn.execute(query).df()
        records = df.to_dict(orient="records")
        for r in records:
            r["baseline_median"] = round(float(r["baseline_median"]), 2)
            r["baseline_p90"] = round(float(r["baseline_p90"]), 2)
            r["avg_harmonized_count"] = round(float(r["avg_harmonized_count"]), 2)

        return {
            "status": "ok",
            "count": len(records),
            "data": records
        }
    finally:
        conn.close()

