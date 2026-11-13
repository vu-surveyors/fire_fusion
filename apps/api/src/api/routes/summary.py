from typing import Optional
from fastapi import APIRouter, Query
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_summary(
    year: Optional[int] = Query(None, description="Filter by year (2020 or 2025)"),
    west: Optional[float] = None,
    south: Optional[float] = None,
    east: Optional[float] = None,
    north: Optional[float] = None
):
    conn = get_duckdb_conn()
    try:
        where_clauses = ["1=1"]
        if year is not None:
            where_clauses.append(f"local_date LIKE '{int(year)}%'")
        if west is not None:
            where_clauses.append(f"longitude >= {float(west)}")
        if east is not None:
            where_clauses.append(f"longitude <= {float(east)}")
        if south is not None:
            where_clauses.append(f"latitude >= {float(south)}")
        if north is not None:
            where_clauses.append(f"latitude <= {float(north)}")

        where_sql = " AND ".join(where_clauses)
        
        # Detection level metrics
        query_det = f"""
            SELECT 
                COUNT(*) as total_detections,
                SUM(frp) as total_frp,
                AVG(frp) as avg_frp,
                MIN(local_date) as start_date,
                MAX(local_date) as end_date
            FROM canonical_detections
            WHERE {where_sql}
        """
        det_stats = conn.execute(query_det).fetchall()[0]

        query_sources = f"""
            SELECT product, COUNT(*) as cnt
            FROM canonical_detections
            WHERE {where_sql}
            GROUP BY product
        """
        sources = {row[0]: row[1] for row in conn.execute(query_sources).fetchall()}

        query_sensors = f"""
            SELECT sensor_family, COUNT(*) as cnt
            FROM canonical_detections
            WHERE {where_sql}
            GROUP BY sensor_family
        """
        sensors = {row[0]: row[1] for row in conn.execute(query_sensors).fetchall()}

        # Cluster level metrics
        c_where = ["1=1"]
        if year is not None:
            c_where.append(f"local_date LIKE '{int(year)}%'")
        if west is not None:
            c_where.append(f"centroid_lon >= {float(west)}")
        if east is not None:
            c_where.append(f"centroid_lon <= {float(east)}")
        if south is not None:
            c_where.append(f"centroid_lat >= {float(south)}")
        if north is not None:
            c_where.append(f"centroid_lat <= {float(north)}")
        
        c_where_sql = " AND ".join(c_where)
        query_clust = f"""
            SELECT 
                COUNT(*) as total_clusters,
                SUM(CASE WHEN corroborated THEN 1 ELSE 0 END) as corroborated_clusters,
                AVG(event_score) as avg_score
            FROM fire_clusters
            WHERE {c_where_sql}
        """
        clust_stats = conn.execute(query_clust).fetchall()[0]

        tot_det = int(det_stats[0]) if det_stats and det_stats[0] else 0
        tot_clust = int(clust_stats[0]) if clust_stats and clust_stats[0] else 0
        corr_clust = int(clust_stats[1]) if clust_stats and clust_stats[1] else 0

        compression_ratio = round(tot_det / max(1, tot_clust), 2) if tot_clust > 0 else 1.0

        return {
            "status": "ok",
            "year": year,
            "total_detections": tot_det,
            "total_harmonized_clusters": tot_clust,
            "corroborated_clusters": corr_clust,
            "corroborated_rate_pct": round((corr_clust / max(1, tot_clust)) * 100.0, 1) if tot_clust > 0 else 0.0,
            "spatial_duplication_reduction_ratio": f"{compression_ratio}x",
            "total_frp_mw": round(float(det_stats[1]), 2) if det_stats and det_stats[1] else 0.0,
            "average_frp_mw": round(float(det_stats[2]), 2) if det_stats and det_stats[2] else 0.0,
            "sensors": sensors,
            "products": sources,
            "date_range": {
                "start": str(det_stats[3]) if det_stats and det_stats[3] else None,
                "end": str(det_stats[4]) if det_stats and det_stats[4] else None
            },
            "data_status": "harmonized_dual_year_archive"
        }
    finally:
        conn.close()

