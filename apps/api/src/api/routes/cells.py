from typing import Optional
from fastapi import APIRouter, Query
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_cells(
    date: Optional[str] = Query(None, description="Local date YYYY-MM-DD"),
    west: Optional[float] = None,
    south: Optional[float] = None,
    east: Optional[float] = None,
    north: Optional[float] = None,
    limit: int = Query(5000, ge=1, le=20000)
):
    conn = get_duckdb_conn()
    try:
        where_clauses = ["1=1"]
        if date:
            where_clauses.append(f"local_date = '{date}'")
        if west is not None:
            where_clauses.append(f"centroid_lon >= {float(west)}")
        if east is not None:
            where_clauses.append(f"centroid_lon <= {float(east)}")
        if south is not None:
            where_clauses.append(f"centroid_lat >= {float(south)}")
        if north is not None:
            where_clauses.append(f"centroid_lat <= {float(north)}")

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT 
                cell_id,
                local_date,
                centroid_lat,
                centroid_lon,
                event_count,
                corroborated_pct,
                max_frp,
                best_conf_class,
                best_conf_label
            FROM grid_cells
            WHERE {where_sql}
            ORDER BY event_count DESC
            LIMIT {int(limit)}
        """
        df = conn.execute(query).df()
        records = df.to_dict(orient="records")
        return {
            "status": "ok",
            "count": len(records),
            "date": date,
            "data": records
        }
    finally:
        conn.close()

