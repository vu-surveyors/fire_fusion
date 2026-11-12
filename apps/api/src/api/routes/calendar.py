from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_calendar(
    year: Optional[int] = Query(None, description="Filter by year (e.g. 2020 or 2025)"),
    mode: str = Query("harmonised", description="'raw' or 'harmonised'"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    conn = get_duckdb_conn()
    try:
        where_clauses = ["1=1"]
        if year is not None:
            where_clauses.append(f"year = {int(year)}")
        if start_date:
            where_clauses.append(f"date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"date <= '{end_date}'")

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT 
                date,
                year,
                day_of_year,
                raw_event_count,
                raw_modis_count,
                raw_viirs_count,
                harmonized_event_count,
                interval_lo,
                interval_hi,
                total_frp_mw,
                max_frp,
                mean_frp,
                n_corroborated,
                corroborated_pct,
                baseline_median,
                baseline_p90,
                anomaly_percentile,
                is_anomaly,
                source
            FROM daily_aggregates
            WHERE {where_sql}
            ORDER BY date ASC
        """
        df = conn.execute(query).df()
        
        is_raw = mode.lower() == "raw"
        records = []
        for _, row in df.iterrows():
            cnt = int(row["raw_event_count"]) if is_raw else int(row["harmonized_event_count"])
            records.append({
                "date": str(row["date"]),
                "count": cnt,
                "lo": int(row["interval_lo"]) if not is_raw else None,
                "hi": int(row["interval_hi"]) if not is_raw else None,
                "raw_event_count": int(row["raw_event_count"]),
                "harmonized_event_count": int(row["harmonized_event_count"]),
                "raw_modis_count": int(row["raw_modis_count"]),
                "raw_viirs_count": int(row["raw_viirs_count"]),
                "max_frp": round(float(row["max_frp"]), 2),
                "is_anomaly": bool(row["is_anomaly"]),
                "anomaly_percentile": float(row["anomaly_percentile"]) if row["anomaly_percentile"] is not None else None,
                "source": str(row["source"])
            })

        return {
            "status": "ok",
            "mode": mode,
            "year": year,
            "count": len(records),
            "data": records,
            "provenance": {
                "datasets": ["MODIS_C6.1", "VIIRS_SNPP_C2", "VIIRS_NOAA20_C2", "VIIRS_NOAA21_C2"],
                "parameters": {"eps_km": 1.5, "timezone": "Asia/Dhaka"},
                "engine": "DuckDB Analytics Engine"
            }
        }
    finally:
        conn.close()

