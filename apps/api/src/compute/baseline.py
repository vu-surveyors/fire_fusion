from typing import Dict, Any, List
import numpy as np
import pandas as pd

def compute_seasonal_baselines(df_daily: pd.DataFrame, window_days: int = 7) -> pd.DataFrame:
    """
    Computes rolling seasonal baseline across available years (System Design §7.4).
    For each day of year (1-366), samples daily harmonised counts within a ±window_days window,
    calculates empirical median, p90, and evaluates anomaly percentiles.
    """
    if df_daily.empty:
        return df_daily

    df = df_daily.copy()

    # Pre-build lookup of day_of_year -> harmonized counts
    doy_to_counts: Dict[int, List[int]] = {}
    for doy in range(1, 367):
        doy_to_counts[doy] = []

    for _, row in df.iterrows():
        doy = int(row["day_of_year"])
        cnt = int(row["harmonized_event_count"])
        doy_to_counts[doy].append(cnt)

    # For each DOY, collect all counts within ±window_days (handling circular wrap-around at year ends)
    doy_baseline_stats: Dict[int, Dict[str, float]] = {}
    for doy in range(1, 367):
        window_counts = []
        for offset in range(-window_days, window_days + 1):
            target_doy = doy + offset
            if target_doy < 1:
                target_doy += 365
            elif target_doy > 365:
                target_doy -= 365
            window_counts.extend(doy_to_counts.get(target_doy, []))

        if window_counts:
            arr = np.array(window_counts, dtype=float)
            med = float(np.median(arr))
            p90 = float(np.percentile(arr, 90))
            p95 = float(np.percentile(arr, 95))
            doy_baseline_stats[doy] = {
                "samples": window_counts,
                "median": round(med, 2),
                "p90": round(p90, 2),
                "p95": round(p95, 2)
            }
        else:
            doy_baseline_stats[doy] = {
                "samples": [0],
                "median": 0.0,
                "p90": 0.0,
                "p95": 0.0
            }

    # Assign baselines and compute empirical percentile for each date
    baseline_medians = []
    baseline_p90s = []
    anomaly_percentiles = []
    is_anomalies = []

    for _, row in df.iterrows():
        doy = int(row["day_of_year"])
        observed = float(row["harmonized_event_count"])
        stats = doy_baseline_stats.get(doy, {"samples": [0], "median": 0.0, "p90": 0.0})

        med = stats["median"]
        p90 = stats["p90"]
        samples = np.array(stats["samples"], dtype=float)

        # Mid-rank empirical percentile
        less = np.sum(samples < observed)
        equal = np.sum(samples == observed)
        total = len(samples)
        percentile = float(((less + 0.5 * equal) / max(1, total)) * 100.0)

        is_anom = bool(observed > p90 and observed > 5)

        baseline_medians.append(med)
        baseline_p90s.append(p90)
        anomaly_percentiles.append(round(percentile, 1))
        is_anomalies.append(is_anom)

    df["baseline_median"] = baseline_medians
    df["baseline_p90"] = baseline_p90s
    df["anomaly_percentile"] = anomaly_percentiles
    df["is_anomaly"] = is_anomalies

    return df

