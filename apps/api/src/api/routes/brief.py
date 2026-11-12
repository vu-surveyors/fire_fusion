from typing import Optional
from fastapi import APIRouter, Query
from src.db.session import get_duckdb_conn

router = APIRouter()

@router.get("")
@router.get("/")
def get_analyst_brief(
    year: Optional[int] = Query(None, description="Year filter (2020 or 2025)"),
    date: Optional[str] = Query(None, description="Specific local date YYYY-MM-DD")
):
    """Generate an evidence-backed scientific analyst brief adhering to §7.6.
    
    The brief synthesizes raw observations, harmonized clusters, corroboration rates,
    and statistical anomaly rankings without hallucination, strictly adhering to
    scientific honesty guardrails.
    """
    conn = get_duckdb_conn()
    try:
        where_det = ["1=1"]
        where_clust = ["1=1"]
        where_daily = ["1=1"]
        
        if year:
            where_det.append(f"local_date LIKE '{int(year)}%'")
            where_clust.append(f"local_date LIKE '{int(year)}%'")
            where_daily.append(f"year = {int(year)}")
        if date:
            where_det.append(f"local_date = '{date}'")
            where_clust.append(f"local_date = '{date}'")
            where_daily.append(f"date = '{date}'")
            
        w_det_sql = " AND ".join(where_det)
        w_clust_sql = " AND ".join(where_clust)
        w_daily_sql = " AND ".join(where_daily)
        
        # Aggregate detections
        det_row = conn.execute(f"""
            SELECT COUNT(*), SUM(frp), AVG(frp), MIN(local_date), MAX(local_date)
            FROM canonical_detections WHERE {w_det_sql}
        """).fetchall()[0]
        
        # Sensor counts
        sensor_rows = conn.execute(f"""
            SELECT sensor_family, COUNT(*) FROM canonical_detections 
            WHERE {w_det_sql} GROUP BY sensor_family
        """).fetchall()
        sensor_counts = {r[0]: r[1] for r in sensor_rows}
        n_modis = sensor_counts.get("MODIS", 0)
        n_viirs = sensor_counts.get("VIIRS", 0)
        
        # Cluster counts
        clust_row = conn.execute(f"""
            SELECT COUNT(*), SUM(CASE WHEN corroborated THEN 1 ELSE 0 END), AVG(event_score), MAX(max_frp)
            FROM fire_clusters WHERE {w_clust_sql}
        """).fetchall()[0]
        
        n_clusters = int(clust_row[0]) if clust_row[0] else 0
        n_corroborated = int(clust_row[1]) if clust_row[1] else 0
        corroborated_pct = round((n_corroborated / max(1, n_clusters)) * 100, 1)
        avg_score = round(float(clust_row[2]), 3) if clust_row[2] else 0.0
        max_frp = round(float(clust_row[3]), 1) if clust_row[3] else 0.0
        
        # Daily anomaly stats
        daily_rows = conn.execute(f"""
            SELECT date, harmonized_event_count, raw_event_count, anomaly_percentile, is_anomaly
            FROM daily_aggregates WHERE {w_daily_sql} AND is_anomaly = true
            ORDER BY anomaly_percentile DESC LIMIT 3
        """).fetchall()
        top_anomalies = [
            {"date": str(r[0]), "harmonized": int(r[1]), "raw": int(r[2]), "percentile": float(r[3])}
            for r in daily_rows
        ]
        
        tot_det = int(det_row[0]) if det_row[0] else 0
        compression = round(tot_det / max(1, n_clusters), 2)
        ratio_str = f"{round(n_viirs / max(1, n_modis), 2)}:1" if n_modis > 0 else "N/A"
        
        timeframe_desc = f"date {date}" if date else (f"year {year}" if year else "dual-year archive (2020 & 2025)")
        
        # Synthesize scientific narrative
        headline = f"Harmonization Analysis for {timeframe_desc}: {tot_det:,} raw detections condensed to {n_clusters:,} discrete fire events ({compression}x spatial reduction)."
        
        summary_paragraphs = [
            (
                f"During the analyzed period ({timeframe_desc}), NASA FIRMS sensors registered {tot_det:,} active fire hot spot detections "
                f"({n_viirs:,} VIIRS across SNPP/NOAA-20/NOAA-21 and {n_modis:,} MODIS across Terra/Aqua). "
                f"The unadjusted VIIRS to MODIS observation ratio is {ratio_str}, reflecting the 375m spatial resolution sensitivity advantage of VIIRS over MODIS 1km."
            ),
            (
                f"Applying DBSCAN spatio-temporal clustering with a 1.5 km haversine kernel resolved the dataset into {n_clusters:,} discrete fire events. "
                f"Of these events, {n_corroborated:,} ({corroborated_pct}%) are dual-sensor corroborated where both MODIS and VIIRS independently confirmed active burning within the same spatio-temporal envelope. "
                f"The average cluster confidence score is {avg_score} (on a 0.0-1.0 scale), and peak fire radiative power reached {max_frp} MW."
            )
        ]
        
        if top_anomalies:
            anomaly_dates = ", ".join([f"{a['date']} ({a['harmonized']} events, {a['percentile']:.1f}th %ile)" for a in top_anomalies])
            summary_paragraphs.append(
                f"Rolling ±7-day seasonal baseline analysis identified significant statistical thermal anomalies on: {anomaly_dates}. "
                "These dates exhibited fire event activity exceeding the 90th percentile of seasonal expectations."
            )
        
        return {
            "status": "ok",
            "timeframe": timeframe_desc,
            "headline": headline,
            "summary_text": "\n\n".join(summary_paragraphs),
            "metrics": {
                "total_raw_detections": tot_det,
                "viirs_detections": n_viirs,
                "modis_detections": n_modis,
                "raw_ratio_viirs_to_modis": ratio_str,
                "harmonized_clusters": n_clusters,
                "corroborated_clusters": n_corroborated,
                "corroborated_rate_pct": corroborated_pct,
                "spatial_compression_factor": f"{compression}x",
                "max_frp_mw": max_frp,
                "top_seasonal_anomalies": top_anomalies
            },
            "guardrails": {
                "disclaimer": "Thermal anomalies indicate statistical historical rarity only. This is not a tactical wildfire spread forecast or perimeter boundary.",
                "confidence_mapping": "Confidence values are normalized into 3 standard tiers (low, nominal, high) rather than 1:1 numeric equivalencies.",
                "model_role": "Deterministic template generation — no probabilistic LLM hallucination in quantitative statistics."
            }
        }
    finally:
        conn.close()

