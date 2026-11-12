"""create_initial_schema

Revision ID: 750a1454af05
Revises: 
Create Date: 2026-11-12 21:57:30.800612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '750a1454af05'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "canonical_detections",
        sa.Column("det_id", sa.String(), primary_key=True),
        sa.Column("source_file", sa.String(), nullable=False),
        sa.Column("product", sa.String(), nullable=False),
        sa.Column("satellite", sa.String(), nullable=False),
        sa.Column("sensor_family", sa.String(), nullable=False),
        sa.Column("instrument", sa.String(), nullable=False),
        sa.Column("acq_date", sa.String(), nullable=False),
        sa.Column("acq_time", sa.String(), nullable=False),
        sa.Column("ts_utc", sa.String(), nullable=False),
        sa.Column("local_date", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("scan", sa.Float(), nullable=False),
        sa.Column("track", sa.Float(), nullable=False),
        sa.Column("footprint_km2", sa.Float(), nullable=False),
        sa.Column("brightness", sa.Float(), nullable=False),
        sa.Column("bright_t31", sa.Float(), nullable=True),
        sa.Column("frp", sa.Float(), nullable=False),
        sa.Column("confidence_raw", sa.String(), nullable=False),
        sa.Column("confidence_class", sa.Integer(), nullable=False),
        sa.Column("confidence_label", sa.String(), nullable=False),
        sa.Column("daynight", sa.String(), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("cluster_id", sa.String(), nullable=True),
    )

    op.create_table(
        "fire_clusters",
        sa.Column("cluster_id", sa.String(), primary_key=True),
        sa.Column("local_date", sa.String(), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=False),
        sa.Column("centroid_lon", sa.Float(), nullable=False),
        sa.Column("n_modis", sa.Integer(), nullable=False),
        sa.Column("n_viirs", sa.Integer(), nullable=False),
        sa.Column("n_total", sa.Integer(), nullable=False),
        sa.Column("corroborated", sa.Boolean(), nullable=False),
        sa.Column("n_platforms", sa.Integer(), nullable=False),
        sa.Column("platforms", sa.String(), nullable=False),
        sa.Column("first_ts_utc", sa.String(), nullable=False),
        sa.Column("last_ts_utc", sa.String(), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column("max_frp", sa.Float(), nullable=False),
        sa.Column("sum_frp", sa.Float(), nullable=False),
        sa.Column("mean_frp", sa.Float(), nullable=False),
        sa.Column("best_conf_class", sa.Integer(), nullable=False),
        sa.Column("best_conf_label", sa.String(), nullable=False),
        sa.Column("event_score", sa.Float(), nullable=False),
        sa.Column("members_json", sa.Text(), nullable=False),
    )

    op.create_table(
        "daily_aggregates",
        sa.Column("date", sa.String(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("day_of_year", sa.Integer(), nullable=False),
        sa.Column("raw_event_count", sa.Integer(), nullable=False),
        sa.Column("raw_modis_count", sa.Integer(), nullable=False),
        sa.Column("raw_viirs_count", sa.Integer(), nullable=False),
        sa.Column("harmonized_event_count", sa.Integer(), nullable=False),
        sa.Column("interval_lo", sa.Integer(), nullable=False),
        sa.Column("interval_hi", sa.Integer(), nullable=False),
        sa.Column("total_frp_mw", sa.Float(), nullable=False),
        sa.Column("max_frp", sa.Float(), nullable=False),
        sa.Column("mean_frp", sa.Float(), nullable=False),
        sa.Column("n_corroborated", sa.Integer(), nullable=False),
        sa.Column("corroborated_pct", sa.Float(), nullable=False),
        sa.Column("baseline_median", sa.Float(), nullable=True),
        sa.Column("baseline_p90", sa.Float(), nullable=True),
        sa.Column("anomaly_percentile", sa.Float(), nullable=True),
        sa.Column("is_anomaly", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
    )

    op.create_table(
        "grid_cells",
        sa.Column("cell_id", sa.String(), primary_key=True),
        sa.Column("local_date", sa.String(), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=False),
        sa.Column("centroid_lon", sa.Float(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("corroborated_pct", sa.Float(), nullable=False),
        sa.Column("max_frp", sa.Float(), nullable=False),
        sa.Column("best_conf_class", sa.Integer(), nullable=False),
        sa.Column("best_conf_label", sa.String(), nullable=False),
    )

    op.create_table(
        "validation_metrics",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("value_raw", sa.Float(), nullable=False),
        sa.Column("value_harmonized", sa.Float(), nullable=False),
        sa.Column("improvement_pct", sa.Float(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
    )

    op.create_table(
        "pipeline_metadata",
        sa.Column("run_id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("records_raw", sa.Integer(), nullable=False),
        sa.Column("records_canonical", sa.Integer(), nullable=False),
        sa.Column("records_clusters", sa.Integer(), nullable=False),
        sa.Column("records_daily", sa.Integer(), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pipeline_metadata")
    op.drop_table("validation_metrics")
    op.drop_table("grid_cells")
    op.drop_table("daily_aggregates")
    op.drop_table("fire_clusters")
    op.drop_table("canonical_detections")
