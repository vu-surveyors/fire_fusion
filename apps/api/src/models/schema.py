from typing import Optional
from sqlmodel import SQLModel, Field

class CanonicalDetection(SQLModel, table=True):
    __tablename__ = "canonical_detections"

    det_id: str = Field(primary_key=True, index=True)
    source_file: str
    product: str
    satellite: str
    sensor_family: str = Field(index=True)  # "MODIS" or "VIIRS"
    instrument: str
    acq_date: str = Field(index=True)       # "YYYY-MM-DD"
    acq_time: str
    ts_utc: str                             # ISO UTC timestamp
    local_date: str = Field(index=True)     # Asia/Dhaka local date "YYYY-MM-DD"
    latitude: float
    longitude: float
    scan: float
    track: float
    footprint_km2: float
    brightness: float
    bright_t31: Optional[float] = None
    frp: float
    confidence_raw: str
    confidence_class: int = Field(index=True)  # 0=low, 1=nominal, 2=high
    confidence_label: str                      # "low", "nominal", "high"
    daynight: str
    type: int
    cluster_id: Optional[str] = Field(default=None, index=True)


class FireCluster(SQLModel, table=True):
    __tablename__ = "fire_clusters"

    cluster_id: str = Field(primary_key=True, index=True)  # e.g. "CL_2020-01-01_0001"
    local_date: str = Field(index=True)
    centroid_lat: float
    centroid_lon: float
    n_modis: int
    n_viirs: int
    n_total: int
    corroborated: bool = Field(index=True)  # True if both MODIS and VIIRS observed
    n_platforms: int
    platforms: str                          # Comma-separated list
    first_ts_utc: str
    last_ts_utc: str
    duration_hours: float
    max_frp: float
    sum_frp: float
    mean_frp: float
    best_conf_class: int
    best_conf_label: str                    # "low", "nominal", "high"
    event_score: float                      # 0.0 to 1.0 composite score
    members_json: str                       # JSON array of member detections


class DailyAggregate(SQLModel, table=True):
    __tablename__ = "daily_aggregates"

    date: str = Field(primary_key=True, index=True)  # "YYYY-MM-DD"
    year: int = Field(index=True)
    day_of_year: int
    raw_event_count: int
    raw_modis_count: int
    raw_viirs_count: int
    harmonized_event_count: int
    interval_lo: int
    interval_hi: int
    total_frp_mw: float
    max_frp: float
    mean_frp: float
    n_corroborated: int
    corroborated_pct: float
    baseline_median: Optional[float] = None
    baseline_p90: Optional[float] = None
    anomaly_percentile: Optional[float] = None
    is_anomaly: bool = False
    source: str = "FIRMS Harmonized (MODIS C6.1 + VIIRS C2)"


class GridCell(SQLModel, table=True):
    __tablename__ = "grid_cells"

    cell_id: str = Field(primary_key=True, index=True)
    local_date: str = Field(index=True)
    centroid_lat: float
    centroid_lon: float
    event_count: int
    corroborated_pct: float
    max_frp: float
    best_conf_class: int
    best_conf_label: str


class ValidationMetric(SQLModel, table=True):
    __tablename__ = "validation_metrics"

    id: str = Field(primary_key=True)
    category: str
    metric_name: str
    value_raw: float
    value_harmonized: float
    improvement_pct: float
    details_json: str


class PipelineMetadata(SQLModel, table=True):
    __tablename__ = "pipeline_metadata"

    run_id: str = Field(primary_key=True)
    created_at: str
    records_raw: int
    records_canonical: int
    records_clusters: int
    records_daily: int
    parameters_json: str

