import hashlib
import glob
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import numpy as np

EARTH_R_KM = 6371.0088

CONF_LABEL_MAP = {0: "low", 1: "nominal", 2: "high"}

def map_confidence(row, is_modis: bool) -> Tuple[int, str]:
    raw = row.get("confidence")
    if is_modis:
        try:
            val = float(raw)
            if val < 30:
                cls = 0
            elif val < 80:
                cls = 1
            else:
                cls = 2
        except (ValueError, TypeError):
            cls = 1
    else:
        s = str(raw).strip().lower()
        if s == "l":
            cls = 0
        elif s == "h":
            cls = 2
        else:
            cls = 1
    return cls, CONF_LABEL_MAP[cls]


def generate_det_id(row) -> str:
    seed = f"{row.get('satellite')}_{row.get('latitude'):.5f}_{row.get('longitude'):.5f}_{row.get('acq_date')}_{str(row.get('acq_time')).zfill(4)}_{row.get('frp')}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def detect_product_and_sensor(filepath: Path, df: pd.DataFrame) -> Tuple[str, str, str]:
    fname = filepath.name.lower()
    if "m-c61" in fname or "modis" in fname:
        product = "MODIS_C6.1"
        sensor_family = "MODIS"
        instrument = "MODIS"
    elif "j1v" in fname or "noaa20" in fname:
        product = "VIIRS_NOAA20_C2"
        sensor_family = "VIIRS"
        instrument = "VIIRS"
    elif "j2v" in fname or "noaa21" in fname:
        product = "VIIRS_NOAA21_C2"
        sensor_family = "VIIRS"
        instrument = "VIIRS"
    elif "sv-c2" in fname or "snpp" in fname:
        product = "VIIRS_SNPP_C2"
        sensor_family = "VIIRS"
        instrument = "VIIRS"
    else:
        # Fallback inspection
        sat = str(df["satellite"].iloc[0]).lower() if "satellite" in df.columns else ""
        if "aqua" in sat or "terra" in sat:
            product = "MODIS_C6.1"
            sensor_family = "MODIS"
            instrument = "MODIS"
        else:
            product = "VIIRS_GENERIC"
            sensor_family = "VIIRS"
            instrument = "VIIRS"
    return product, sensor_family, instrument


def normalise_single_file(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    if df.empty:
        return pd.DataFrame()

    product, sensor_family, instrument = detect_product_and_sensor(filepath, df)
    is_modis = sensor_family == "MODIS"

    # Datetime handling: Parse UTC and convert to Asia/Dhaka local date
    acq_times = df["acq_time"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)
    dt_str = df["acq_date"].astype(str) + " " + acq_times
    ts_utc = pd.to_datetime(dt_str, format="%Y-%m-%d %H%M", utc=True, errors="coerce")
    ts_local = ts_utc.dt.tz_convert("Asia/Dhaka")

    clean_df = pd.DataFrame(index=df.index)
    clean_df["source_file"] = filepath.name
    clean_df["product"] = product
    clean_df["satellite"] = df["satellite"].astype(str)
    clean_df["sensor_family"] = sensor_family
    clean_df["instrument"] = instrument
    clean_df["acq_date"] = df["acq_date"].astype(str)
    clean_df["acq_time"] = acq_times
    clean_df["ts_utc"] = ts_utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    clean_df["local_date"] = ts_local.dt.strftime("%Y-%m-%d")
    clean_df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    clean_df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    clean_df["scan"] = pd.to_numeric(df.get("scan", 1.0), errors="coerce").fillna(1.0)
    clean_df["track"] = pd.to_numeric(df.get("track", 1.0), errors="coerce").fillna(1.0)
    clean_df["footprint_km2"] = (clean_df["scan"] * clean_df["track"]).round(3)
    clean_df["brightness"] = pd.to_numeric(df.get("brightness", 0.0), errors="coerce").fillna(0.0)
    clean_df["bright_t31"] = pd.to_numeric(df.get("bright_t31", np.nan), errors="coerce")
    clean_df["frp"] = pd.to_numeric(df.get("frp", 0.0), errors="coerce").fillna(0.0)
    clean_df["confidence_raw"] = df["confidence"].astype(str)

    # Confidence classification (0=low, 1=nominal, 2=high)
    conf_tuples = [map_confidence({"confidence": c}, is_modis) for c in df["confidence"]]
    clean_df["confidence_class"] = [t[0] for t in conf_tuples]
    clean_df["confidence_label"] = [t[1] for t in conf_tuples]

    clean_df["daynight"] = df.get("daynight", "D").astype(str).str.upper()
    clean_df["type"] = pd.to_numeric(df.get("type", 0), errors="coerce").fillna(0).astype(int)
    clean_df["cluster_id"] = None

    # Compute deterministic det_id
    clean_df["det_id"] = [generate_det_id(row) for _, row in clean_df.iterrows()]

    # Filter invalid records
    valid_mask = (
        clean_df["latitude"].between(-90, 90) &
        clean_df["longitude"].between(-180, 180) &
        clean_df["ts_utc"].notna() &
        (clean_df["type"] != 2)  # Exclude persistent static land/industrial thermal sources
    )
    return clean_df[valid_mask].reset_index(drop=True)


def run_canonical_normalisation(data_dir: Path) -> pd.DataFrame:
    """Reads all 2020 and 2025 raw CSV files and returns the canonical DataFrame."""
    patterns = [
        str(data_dir / "DATA 2020" / "*.csv"),
        str(data_dir / "DATA 2025" / "*.csv"),
    ]
    all_files = []
    for pattern in patterns:
        all_files.extend([Path(p) for p in glob.glob(pattern)])

    frames = []
    for f in all_files:
        df_norm = normalise_single_file(f)
        frames.append(df_norm)

    if not frames:
        raise ValueError(f"No CSV data files found in {data_dir}")

    total_df = pd.concat(frames, ignore_index=True)
    # Deduplicate in case overlapping acquisitions exist
    total_df = total_df.drop_duplicates(subset=["det_id"]).reset_index(drop=True)
    return total_df
