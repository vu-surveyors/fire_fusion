import json
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Path
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_clusters(
    date: Optional[str] = Query(None, description="Local date YYYY-MM-DD"),
    west: Optional[float] = None,
    south: Optional[float] = None,
    east: Optional[float] = None,
    north: Optional[float] = None,
    corroborated_only: bool = Query(False, description="Filter for corroborated dual-sensor events"),
    min_score: float = Query(0.0, description="Minimum event score (0.0 to 1.0)"),
    limit: int = Query(5000, ge=1, le=20000)
):
    conn = get_duckdb_conn()
    try:
        where_clauses = [f"event_score >= {float(min_score)}"]
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
        if corroborated_only:
            where_clauses.append("corroborated = true")

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT 
                cluster_id,
                local_date,
                centroid_lat,
                centroid_lon,
                n_modis,
                n_viirs,
                n_total,
                corroborated,
                n_platforms,
                platforms,
                first_ts_utc,
                last_ts_utc,
                duration_hours,
                max_frp,
                sum_frp,
                mean_frp,
                best_conf_class,
                best_conf_label,
                event_score
            FROM fire_clusters
            WHERE {where_sql}
            ORDER BY event_score DESC, max_frp DESC
            LIMIT {int(limit)}
        """
        df = conn.execute(query).df()
        records = df.to_dict(orient="records")
        for r in records:
            r["centroid"] = {"lat": r["centroid_lat"], "lon": r["centroid_lon"]}

        return {
            "status": "ok",
            "count": len(records),
            "date": date,
            "data": records
        }
    finally:
        conn.close()


@router.get("/{cluster_id}")
def get_cluster_by_id(cluster_id: str = Path(..., description="Unique cluster ID")):
    conn = get_duckdb_conn()
    try:
        query = f"""
            SELECT * FROM fire_clusters WHERE cluster_id = '{cluster_id}' LIMIT 1
        """
        df = conn.execute(query).df()
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found.")

        row = df.iloc[0].to_dict()
        members = json.loads(row.get("members_json", "[]"))
        row.pop("members_json", None)
        row["centroid"] = {"lat": row["centroid_lat"], "lon": row["centroid_lon"]}
        row["members"] = members
        row["summary"] = {
            "n_modis": int(row["n_modis"]),
            "n_viirs": int(row["n_viirs"]),
            "n_total": int(row["n_total"]),
            "max_frp": float(row["max_frp"]),
            "corroborated": bool(row["corroborated"])
        }

        return {
            "status": "ok",
            "cluster_id": cluster_id,
            "data": row
        }
    finally:
        conn.close()

