import json
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_R_KM = 6371.0088
CONF_LABEL_MAP = {0: "low", 1: "nominal", 2: "high"}

def compute_event_score(
    best_conf_class: int,
    corroborated: bool,
    max_frp: float,
    duration_hours: float,
    n_platforms: int
) -> float:
    """
    Composite confidence-aware event score (System Design §7.3):
    - Confidence class (0.30)
    - Corroboration across sensor families (0.25)
    - Log-scaled FRP strength (0.20)
    - Temporal spread / persistence (0.15)
    - Platform diversity (0.10)
    """
    s_conf = 0.30 * (best_conf_class / 2.0)
    s_corr = 0.25 * (1.0 if corroborated else 0.0)
    s_frp = 0.20 * min(1.0, float(np.log1p(max(0.0, max_frp)) / np.log1p(100.0)))
    s_dur = 0.15 * min(1.0, float(max(0.0, duration_hours) / 12.0))
    s_plat = 0.10 * min(1.0, float(n_platforms / 3.0))
    return round(float(s_conf + s_corr + s_frp + s_dur + s_plat), 3)


def cluster_detections(df: pd.DataFrame, eps_km: float = 1.5) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clusters detections per local_date using DBSCAN with haversine metric.
    High-performance vector implementation.
    """
    if df.empty:
        return df, pd.DataFrame()

    df_out = df.copy()
    n_rows = len(df_out)
    cluster_id_arr = np.empty(n_rows, dtype=object)

    eps_rad = eps_km / EARTH_R_KM
    cluster_records: List[Dict[str, Any]] = []

    # Pre-extract numpy/dict views for speed
    det_ids = df_out["det_id"].to_numpy()
    sensors = df_out["sensor_family"].to_numpy()
    satellites = df_out["satellite"].to_numpy()
    frps = df_out["frp"].to_numpy()
    conf_classes = df_out["confidence_class"].to_numpy()
    ts_utcs = df_out["ts_utc"].to_numpy()
    lats = df_out["latitude"].to_numpy()
    lons = df_out["longitude"].to_numpy()
    local_dates = df_out["local_date"].to_numpy()

    # Fast group indices by local_date
    date_indices: Dict[str, List[int]] = {}
    for idx, d in enumerate(local_dates):
        if d not in date_indices:
            date_indices[d] = []
        date_indices[d].append(idx)

    for local_date, idx_list in date_indices.items():
        indices = np.array(idx_list)
        sub_lats = lats[indices]
        sub_lons = lons[indices]

        # Coordinates in radians: [lat, lon]
        coords_rad = np.radians(np.column_stack([sub_lats, sub_lons]))

        # DBSCAN clustering
        db = DBSCAN(eps=eps_rad, min_samples=1, metric="haversine", algorithm="ball_tree")
        labels = db.fit_predict(coords_rad)

        unique_labels = np.unique(labels)
        for label in unique_labels:
            mask = (labels == label)
            sub_idx = indices[mask]

            cluster_id = f"CL_{local_date}_{label:04d}"
            cluster_id_arr[sub_idx] = cluster_id

            c_sensors = sensors[sub_idx]
            n_modis = int(np.sum(c_sensors == "MODIS"))
            n_viirs = int(np.sum(c_sensors == "VIIRS"))
            n_total = len(sub_idx)
            corroborated = bool(n_modis > 0 and n_viirs > 0)

            c_plats = satellites[sub_idx]
            unique_plats = sorted(list(set(c_plats)))
            platforms_str = ",".join(unique_plats)
            n_platforms = len(unique_plats)

            c_frps = frps[sub_idx]
            sum_frp = float(np.sum(c_frps))
            max_frp = round(float(np.max(c_frps)), 2)
            mean_frp = round(float(np.mean(c_frps)), 2)
            sum_frp = round(sum_frp, 2)

            if sum_frp > 0:
                weights = c_frps / sum_frp
                c_lat = float(np.sum(sub_lats[mask] * weights))
                c_lon = float(np.sum(sub_lons[mask] * weights))
            else:
                c_lat = float(np.mean(sub_lats[mask]))
                c_lon = float(np.mean(sub_lons[mask]))

            c_ts = ts_utcs[sub_idx]
            first_ts = str(np.min(c_ts))
            last_ts = str(np.max(c_ts))

            try:
                t0 = pd.to_datetime(first_ts)
                t1 = pd.to_datetime(last_ts)
                duration_hours = max(0.0, (t1 - t0).total_seconds() / 3600.0)
            except Exception:
                duration_hours = 0.0

            c_conf = conf_classes[sub_idx]
            best_conf_class = int(np.max(c_conf))
            best_conf_label = CONF_LABEL_MAP.get(best_conf_class, "nominal")

            event_score = compute_event_score(
                best_conf_class=best_conf_class,
                corroborated=corroborated,
                max_frp=max_frp,
                duration_hours=duration_hours,
                n_platforms=n_platforms
            )

            # Store compact member metadata
            members = []
            for i in sub_idx:
                members.append({
                    "det_id": str(det_ids[i]),
                    "sensor": str(sensors[i]),
                    "platform": str(satellites[i]),
                    "frp": round(float(frps[i]), 2),
                    "conf_class": int(conf_classes[i]),
                    "ts_utc": str(ts_utcs[i]),
                    "lat": round(float(lats[i]), 4),
                    "lon": round(float(lons[i]), 4)
                })

            cluster_records.append({
                "cluster_id": cluster_id,
                "local_date": str(local_date),
                "centroid_lat": round(c_lat, 5),
                "centroid_lon": round(c_lon, 5),
                "n_modis": n_modis,
                "n_viirs": n_viirs,
                "n_total": n_total,
                "corroborated": corroborated,
                "n_platforms": n_platforms,
                "platforms": platforms_str,
                "first_ts_utc": first_ts,
                "last_ts_utc": last_ts,
                "duration_hours": round(duration_hours, 2),
                "max_frp": max_frp,
                "sum_frp": sum_frp,
                "mean_frp": mean_frp,
                "best_conf_class": best_conf_class,
                "best_conf_label": best_conf_label,
                "event_score": event_score,
                "members_json": json.dumps(members)
            })

    df_out["cluster_id"] = cluster_id_arr
    df_clusters = pd.DataFrame(cluster_records)
    return df_out, df_clusters
