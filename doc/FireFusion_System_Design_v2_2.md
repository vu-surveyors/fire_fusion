# FireFusion — System Design Document

**VU_Surveyors | NASA Space Apps Challenge 2026 | Challenge 9**

**Harmonization of MODIS and VIIRS Hot Spots**
Confidence-Aware, Sensor-Harmonized Wildfire Intelligence Platform

| Detail | Information |
|---|---|
| Team | VU_Surveyors |
| Challenge | #9 — Harmonization of MODIS and VIIRS Hot Spots |
| Document scope | System design, backend architecture, AI/ML pipeline, data engineering |
| Prepared for | Developer role: system design, backend, AI/ML |
| Version | 2.0 — Detailed Implementation Design |
| Document date | 30 September 2026 |
| Event window | 13–15 November 2026 (confirm locally) |
| Classification | Team Internal — NASA Space Apps 2026 |

---

## Table of Contents

1. Executive Summary
2. Problem Analysis & Scientific Foundation
   - 2.1 The Harmonization Problem
   - 2.2 Sensor Comparison Matrix
   - 2.3 Two Effects That Must Be Separated
3. Product Concept & Scope
   - 3.1 Product Vision — FireFusion
   - 3.2 Functional Requirements
   - 3.3 Non-Functional Requirements
   - 3.4 Pilot Scope & Non-Goals
4. System Architecture
   - 4.1 High-Level Architecture Diagram
   - 4.2 Component Responsibilities
   - 4.3 Data Flow Pipeline
   - 4.4 Offline-First Design
5. Data Model & Schema Design
   - 5.1 Entity-Relationship Overview
   - 5.2 Detection (Canonical) Table
   - 5.3 Cluster (Fire Event) Table
   - 5.4 Aggregate Tables
   - 5.5 Metadata & Provenance Table
6. Backend API Design (FastAPI)
   - 6.1 API Endpoint Specification
   - 6.2 Request/Response Schemas
   - 6.3 Error Handling & Middleware
7. Harmonization Engine & AI/ML Pipeline
   - 7.1 Stage 1: Normalisation
   - 7.2 Stage 2: Spatio-Temporal Clustering
   - 7.3 Stage 3: Calibration (ML Core)
   - 7.4 Stage 4: Seasonal Baseline & Anomaly Detection
   - 7.5 Stage 5: Validation Framework
   - 7.6 LLM/Agent Integration
8. Data Acquisition Pipeline
   - 8.1 NASA FIRMS Integration
   - 8.2 Supporting Data Sources
   - 8.3 Caching & Fixture Strategy
9. Technology Stack
10. Repository Structure
11. Testing & Validation Strategy
12. Deployment Architecture
13. 48-Hour Hackathon Execution Plan
    - 12.1 Key Dates & Deadlines
    - 12.2 Pre-Event Preparation
    - 12.3 Day 1 & Day 2 Task Breakdown
    - 12.4 Cut Order
14. Judging Alignment Strategy
15. Risks & Mitigations
16. Suggested Project Topic & Pitch
    - 15.1 Three Topic Framings
    - 15.2 Recommended Narrative (240s Video)
    - 15.3 Hackathon-Level Advice
17. Open Questions
18. Review of Provided Resources
19. Appendix: Code Samples & Pseudocode

> Note: section numbers in the sub-headings of sections 13 and 16 follow the original document, where they are offset from the parent numbers (e.g. section 13 contains 12.x).

---

## 01 Executive Summary

Challenge 9 — Harmonization of MODIS and VIIRS Hot Spots — asks teams to build a web application that merges two satellite fire-detection datasets (NASA MODIS and VIIRS) into a single, trustworthy "burning activity calendar." The core difficulty is not simply overlaying two datasets on a map; it is creating a scientifically defensible cross-sensor harmonization layer that reconciles fundamentally different sensor characteristics.

This is a strong pick for a developer-led team. NASA FIRMS data is openly accessible, the work is primarily data engineering plus statistics, and a compelling demo — a raw-versus-harmonised toggle over a burning-activity calendar that visibly removes a sensor artefact — is achievable within 48 hours.

> **WHY NOW:** Suomi-NPP data delivery ends 1 November 2026 and the MODIS instruments on Terra and Aqua are being retired over 2026–27. Continuity between the two sensor families is now a practical problem, not an academic one.

### Core Recommendation

Treat harmonisation quality as the product. The judges' stated definition of success is an accurate, time-based map of when and where fires occurred that reconciles MODIS and VIIRS. Analyst briefs, priority scores and LLM text are nice extras, but they only score if the reconciled series is defensible and its validation is visible on screen.

### Four Critical Corrections to Existing Plans

- **Do not filter on one confidence number.** MODIS confidence is numeric (0–100) while VIIRS is categorical (low/nominal/high). Map both to a common three-class scale first.
- **Grid-collapsing alone will not remove the sensor artefact.** VIIRS also detects smaller fires MODIS cannot see. A second step — detectability matching plus a fitted sensor factor — is needed.
- **Use local dates for the calendar.** FIRMS timestamps are UTC; night passes over Bangladesh fall on the previous UTC date. Store UTC, build the calendar on Asia/Dhaka date.
- **Verify the killer-demo claim before promising it.** "Counts triple at the transition" is illustrative — measure it on real data and let the measured number go into the pitch.

---

## 02 Problem Analysis & Scientific Foundation

### 2.1 The Harmonization Problem

A harmonisation design is only as good as the list of differences it handles. MODIS and VIIRS are not equivalent sensors. They fly on different platforms, have different spatial resolutions, different detection sensitivities, and use different confidence metrics. When you naïvely stitch them together, you create a false discontinuity in the fire record.

The build guide frames the central issue: a single burning area may produce one MODIS detection but 5–7 VIIRS detections due to the finer spatial resolution. If you naïvely count detections, you could incorrectly conclude that fire activity increased sevenfold, when what actually happened is that the higher-resolution sensor resolved one burning area into multiple detections.

> **KEY:** Harmonization, rather than simple merging, is the core scientific problem. The goal is to make the combined record tell a consistent story across the sensor transition.

### 2.2 Sensor Comparison Matrix

| Dimension | MODIS (Terra, Aqua) | VIIRS 375 m (S-NPP, NOAA-20/21) |
|---|---|---|
| Nominal pixel | 1 km at nadir, grows toward scan edge | 375 m at nadir (I-band), smaller growth |
| Record start (FIRMS) | Terra Nov 2000, Aqua Jul 2002 | S-NPP 2012; NOAA-20/21 later |
| Overpass (local solar) | Terra ~10:30/22:30; Aqua ~13:30/01:30 | ~13:30/01:30 (afternoon orbit) |
| Confidence | Numeric 0–100 | Categorical: low / nominal / high |
| Intensity fields | brightness (band 21), bright_t31, FRP | bright_ti4, bright_ti5, FRP |
| Footprint fields | scan, track (km) | scan, track (km) — much smaller |
| Sensitivity | Misses many small/cool fires | Detects smaller, cooler fires |
| Timestamp | acq_date + acq_time in UTC | Same format, UTC |
| Continuity | Being retired 2026–27 | S-NPP ends 1 Nov 2026; NOAA-20/21 continue |

### 2.3 Two Effects That Must Be Separated

> **SCIENCE:** Two different effects are mixed in a raw count series and must be separated:
>
> **(a) Resolution / duplication:** One real fire produces several VIIRS pixels but one or two MODIS pixels. *Fix:* cluster detections into events.
>
> **(b) Sensitivity:** VIIRS detects fires that MODIS cannot. Clustering does not remove this. *Fix:* detectability matching + estimate a residual sensor factor on the overlap period, with uncertainty.

#### Observation vs. Event — The Key Distinction

Your system should distinguish two concepts clearly:

| Concept | What It Is | Rule |
|---|---|---|
| **Observation** | A raw satellite detection from FIRMS | Evidence — never destroy it; keep the original record intact |
| **Harmonized Fire Event** | Your derived representation of burning activity | Interpretation — cluster observations, apply calibration, carry uncertainty |

---

## 03 Product Concept & Scope

### 3.1 Product Vision — FireFusion

FireFusion is a web platform that ingests MODIS and VIIRS hotspot records for a chosen area, produces a harmonised, source-preserving burning-activity series, and shows it as a calendar heatmap and map with a raw-versus-harmonised toggle, cluster-level evidence and an explicit uncertainty display.

The system answers five fundamental questions:

1. Where is fire activity happening?
2. When is it happening?
3. How much of the apparent increase is real versus sensor-related?
4. Are multiple sensors observing the same likely burning event?
5. Is today's activity unusual compared with the historical baseline for that place and season?

> **PRODUCT:** FireFusion is sensor-aware wildfire intelligence — not wildfire prediction AI. It harmonizes observations, validates the harmonization, detects anomalies, and explains evidence. It never claims to predict fire spread or danger.

### 3.2 Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| F1 | Ingest FIRMS MODIS and VIIRS records for a configurable bounding box and date range; cache to Parquet | Must |
| F2 | Canonical schema: sensor family, platform, UTC timestamp, local date, confidence class, FRP, footprint | Must |
| F3 | Cluster detections into fire events (DBSCAN haversine); keep source sensor on every record | Must |
| F4 | Produce raw and harmonised daily series for any selected area | Must |
| F5 | Calendar heatmap (year × day) with raw / harmonised toggle | Must |
| F6 | Overlap-period validation shown in the interface (correlation and ratio, raw vs harmonised) | Must |
| F7 | Cluster evidence panel (which sensors, times, FRP, confidence) | Should |
| F8 | Seasonal baseline and anomaly percentile for a chosen date and area | Should |
| F9 | Uncertainty bands (bootstrap intervals) on harmonised series | Should |
| F10 | Template-based analyst brief with source citations (LLM optional) | Could |
| F11 | Methods and limitations page ("what this means / does not mean") | Must |
| F12 | Confidence-aware event scoring with transparent, configurable weights | Should |

### 3.3 Non-Functional Requirements

- **Offline-first:** the demo reads only from local cache; `OFFLINE=1` forces fixture mode; a recorded fallback video exists
- **Reproducible:** one command rebuilds every derived file from raw downloads; fixed random seeds; pinned dependencies
- **Transparent:** every number on screen traces to a dataset ID, product name, date range and parameter set
- **Fast:** any API call for the pilot region returns in well under one second from pre-aggregated tables
- **Compliant:** open-source licence (Apache-2.0), AI-use disclosure in `docs/AI_USE.md`, no likeness of anyone under 18 in video
- **Testable:** deterministic synthetic test cases for every compute function; fixed seeds for any stochastic step

### 3.4 Pilot Scope & Non-Goals

#### Scope

- **Area:** Bangladesh-centred bounding box (lon 88–93, lat 20–27); configurable for wider South Asia
- **Time range:** Full overlap period (2012–present) for model; MODIS-only years back to 2000 for long calendar
- **Quality filter:** nominal-or-high confidence class after mapping; low class kept in raw layer
- **Optional secondary region:** Australian bushfire zone or Amazon basin for contrast

#### Non-Goals

- Fire-perimeter mapping or fire-spread simulation
- Evacuation guidance or real-time emergency alerts
- Weather prediction or wind modelling
- Mobile app (web is sufficient)
- Complex microservices or Kubernetes orchestration
- LLM-based fire prediction (scientifically indefensible)

---

## 04 System Architecture

### 4.1 High-Level Architecture Diagram

The design follows the guide's layer rule: the frontend never calls NASA directly, the API never calls NASA during a demo, and acquisition runs before the event. Storage is a chain of Parquet files queried with DuckDB, so the whole system runs on a laptop without a database server.

**FireFusion — system architecture (VU_Surveyors, Challenge 9) — data flows upward**

*(Diagram transcribed as text, top layer first.)*

```
┌─ PRESENTATION (static, offline-capable) ────────────────────────────────────┐
│ MapLibre GL map │ Calendar heatmap │ Raw <-> Harmonised │ Cluster evidence │ │
│ cells / clusters│ year x day       │ toggle             │ panel            │ │
│                                          Methods, limits & source citations │
└──────────────────────────────────────────▲──────────────────────────────────┘
┌─ APP API (FastAPI, reads local cache only) ─────────────────────────────────┐
│ /calendar  /cells  /clusters/{id}  /validation  /anomaly  /brief            │
└──────────────────────────────────────────▲──────────────────────────────────┘
┌─ HARMONISATION + AI/ML CORE (deterministic code, src/compute) ──────────────┐
│ 1 Normalise      2 Cluster          3 Calibrate           4 Baseline &      │
│ schema, UTC,     spatio-temporal    detectability match + anomaly           │
│ local date,      DBSCAN (haversine) Poisson sensor factor day-of-year       │
│ confidence                                                percentiles       │
│ classes                             5 Validate                              │
│                                     overlap correlation, step-change test   │
└──────────────────────────────────────────▲──────────────────────────────────┘
┌─ STORAGE ───────────────────────────────────────────────────────────────────┐
│ Parquet: raw -> canonical -> clusters -> aggregates                         │
│ DuckDB (spatial ext.)  |  optional PostGIS                                  │
└──────────────────────────────────────────▲──────────────────────────────────┘
┌─ ACQUISITION (pre-event, cached; live only when network allows) ────────────┐
│ NASA FIRMS: MODIS C6.1, VIIRS NOAA-20/21, S-NPP archive                     │
│ NASA GIBS tiles (context basemap) │ NASA POWER (weather context)            │
│ Optional: MCD64A1 burned area (cross-check)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Responsibilities

| Layer | Component | Responsibility | Technology |
|---|---|---|---|
| Data | Acquisition | Bulk FIRMS archive download; area-API for latest days; GIBS tiles; NASA POWER; retry + caching + fixture fallback | Python, requests, pandas |
| Data | Normalisation | Map product-specific columns to canonical schema; parse UTC; derive local date; map confidence classes; flag static sources | pandas / DuckDB, pydantic |
| Compute | Clustering | Group same-day detections across sensors into fire events; store member IDs for evidence panel | scikit-learn DBSCAN (haversine) |
| Compute | Calibration | Detectability matching; Poisson GLM sensor factor estimation on overlap period with confidence intervals | statsmodels, scipy, LightGBM |
| Compute | Analytics | Daily series (raw + harmonised), day-of-year baseline, anomaly percentile, aggregates | DuckDB SQL, numpy |
| Compute | Validation | Overlap correlation, ratio, step-change test, sensitivity analysis, unit tests | pytest, scipy |
| API | FastAPI Server | Read-only endpoints: calendar, cells, clusters, validation, anomaly, brief, meta | FastAPI, uvicorn, orjson |
| Frontend | Web Client | Map, calendar heatmap, toggle, evidence panel, methods panel (teammate responsibility) | MapLibre GL, D3 / Observable Plot |
| Optional | Explainer Agent | Turns structured numbers into a brief with citations; never computes; template fallback | Claude API, Jinja2 templates |

### 4.3 Data Flow Pipeline

Data flows through five deterministic stages, each producing a Parquet artifact that can be inspected and validated independently:

| Stage | Input | Output | Key Operation |
|---|---|---|---|
| 1. Acquire | NASA FIRMS API / archive | `raw/*.parquet` (unmodified FIRMS columns) | Download, validate, cache |
| 2. Normalise | `raw/*.parquet` | `canonical/*.parquet` | Schema mapping, UTC→local, confidence class |
| 3. Cluster | `canonical/*.parquet` | `clusters/*.parquet` + detections with `cluster_id` | DBSCAN per `local_date` (haversine) |
| 4. Calibrate | `clusters/*.parquet` (overlap period) | `calibration.json` (sensor factor + intervals) | Poisson GLM; detectability matching |
| 5. Aggregate | clusters + calibration | `agg_daily.parquet`, `agg_cells.parquet` | Pre-compute daily counts per area + per cell |

### 4.4 Offline-First Design

This is not optional for the project. The guide explicitly recommends pre-caching all data and having every live request fall back to cached/fixture data.

| Mode | Behaviour |
|---|---|
| `OFFLINE=0` (default) | API reads from pre-computed Parquet cache; acquisition can refresh recent days if network allows |
| `OFFLINE=1` (demo) | API reads only from fixtures in `cache/demo_fixtures/`; no outbound network calls at all |
| Fallback video | A pre-recorded screen recording exists as last resort if the live demo fails |

> **TIP:** During the hackathon demo, `OFFLINE=1` means no network dependency. If the demo wifi fails, your product still works. This is extremely valuable.

---

## 05 Data Model & Schema Design

### 5.1 Entity-Relationship Overview

The data model has four main entities, each stored as Parquet files queryable via DuckDB. The ER relationships are: Detection → belongs to → Cluster; Cluster → aggregated into → Daily Aggregate; all linked to Metadata/Provenance records.

| Entity | Granularity | Key Fields | Relations |
|---|---|---|---|
| Detection | One satellite pixel | det_id, sensor_family, platform, ts_utc, lat, lon, frp, conf_class | Many-to-one → Cluster |
| Cluster (Fire Event) | One spatial-temporal group per day | cluster_id, local_date, centroid, n_modis, n_viirs, corroborated | One-to-many → Detections |
| Daily Aggregate | One row per (area, date, mode) | date, area_id, raw_count, harmonised_count, interval_lo, interval_hi | Derived from Clusters |
| Provenance | One per dataset/pipeline run | run_id, datasets[], parameters, git_sha, timestamp | Links to all derived tables |

### 5.2 Detection (Canonical) Table

One canonical table for all detections. The original FIRMS columns are preserved in the raw layer so output can always be traced back to the source record.

| Field | Type | Notes |
|---|---|---|
| det_id | string | Stable hash of product, lat, lon, timestamp — globally unique |
| sensor_family | enum | MODIS or VIIRS (use this for corroboration, not platform) |
| platform | enum | Terra, Aqua, S-NPP, NOAA-20, NOAA-21 |
| product | string | FIRMS product name and collection, for citation |
| ts_utc | timestamp | From acq_date + acq_time (UTC) |
| local_date | date | ts_utc converted to Asia/Dhaka; used for calendar |
| lat | float | WGS84 latitude as delivered |
| lon | float | WGS84 longitude as delivered |
| footprint_km2 | float | scan × track (pixel area) |
| frp_mw | float | Fire Radiative Power; cross-sensor comparability is limited |
| conf_class | int (0,1,2) | low/nominal/high after mapping; raw confidence in raw layer |
| daynight | enum | Day or night flag |
| static_flag | bool | Known persistent thermal source (e.g., industrial sites) |
| cluster_id | string | Assigned by clustering stage; nullable before clustering |

### 5.3 Cluster (Fire Event) Table

| Field | Type | Notes |
|---|---|---|
| cluster_id | string | Unique ID: `{local_date}_{cell}_{seq}` |
| local_date | date | The day this fire event was observed |
| centroid_lat | float | Weighted centroid of member detections |
| centroid_lon | float | Weighted centroid of member detections |
| n_modis | int | Number of MODIS detections in this cluster |
| n_viirs | int | Number of VIIRS detections in this cluster |
| n_platforms | int | Distinct platforms that saw this event |
| corroborated | bool | True if both MODIS and VIIRS detected it |
| first_ts_utc | timestamp | Earliest detection timestamp |
| last_ts_utc | timestamp | Latest detection timestamp |
| max_frp | float | Maximum FRP across all member detections |
| median_frp | float | Median FRP across all member detections |
| best_conf_class | int | Highest confidence class among members |
| event_score | float | Composite confidence-aware score (Section 7.3) |

### 5.4 Aggregate Tables

Pre-computed to keep API responses fast. Two aggregate tables serve the calendar and map views:

- **agg_daily:** one row per (area, local_date, mode). Columns: `raw_event_count`, `harmonised_event_count`, `interval_lo`, `interval_hi`, `n_corroborated`, `mean_frp`, `max_frp`
- **agg_cells:** one row per (cell_id, local_date, mode). Columns: `centroid_lat`, `centroid_lon`, `event_count`, `corroborated_pct`, `max_frp`, `best_conf_class`

### 5.5 Metadata & Provenance Table

Every result carries provenance. This is a first-class feature, not an afterthought.

| Field | Type | Notes |
|---|---|---|
| run_id | string | UUID for this pipeline execution |
| git_sha | string | Commit hash of the code that produced this output |
| datasets | array[string] | List of FIRMS product names and date ranges used |
| parameters | json | Cluster radius, confidence thresholds, overlap window, etc. |
| timestamp | datetime | When this pipeline run completed |
| row_counts | json | Count of detections, clusters, aggregates produced |

---

## 06 Backend API Design (FastAPI)

### 6.1 API Endpoint Specification

All endpoints are read-only (GET). The API reads only from pre-computed Parquet/DuckDB cache — no live NASA calls during the demo. All responses include a provenance object.

| Endpoint | Parameters | Returns |
|---|---|---|
| `GET /calendar` | bbox, start, end, mode=raw\|harmonised | Daily values for calendar heatmap with interval bounds in harmonised mode |
| `GET /cells` | date, bbox, mode | Grid/H3 cells with event counts for the map layer |
| `GET /clusters/{id}` | — | Members, sensors, times, FRP, confidence (evidence panel) |
| `GET /clusters/search` | bbox, date, min_score | List of clusters matching spatial-temporal query |
| `GET /validation` | bbox | Overlap-period correlations, ratio (raw vs harmonised), step-change test, parameter set |
| `GET /anomaly` | bbox, date | Percentile against day-of-year baseline, baseline window, sample size |
| `GET /baseline` | bbox, doy | Day-of-year percentile distribution (p10, p50, p90, p95) |
| `GET /brief` | bbox, date | Structured numbers object + generated/templated text with source citations |
| `GET /meta` | — | Datasets, product names, date ranges, limitations, licence (feeds methods panel) |
| `GET /health` | — | Service status, cache freshness, data coverage dates |

### 6.2 Request/Response Schemas

#### Example: `GET /calendar` Response

```json
{
  "bbox": [88.0, 20.0, 93.0, 27.0],
  "start": "2003-01-01", "end": "2026-09-01",
  "mode": "harmonised",
  "data": [
    { "date": "2003-01-01", "count": 12, "lo": 10, "hi": 15 },
    { "date": "2003-01-02", "count": 8, "lo": 6, "hi": 11 },
    ...
  ],
  "provenance": {
    "datasets": ["MODIS_C6.1", "VIIRS_SNPP_NRT"],
    "parameters": { "cluster_eps_km": 1.5, "conf_filter": ">=nominal" },
    "run_id": "abc123", "git_sha": "def456"
  }
}
```

#### Example: `GET /clusters/{id}` Response

```json
{
  "cluster_id": "2024-03-15_h3_8823_001",
  "local_date": "2024-03-15",
  "centroid": [24.123, 90.456],
  "corroborated": true,
  "event_score": 0.87,
  "members": [
    { "det_id": "...", "sensor": "MODIS", "platform": "Aqua",
      "frp": 45.2, "conf_class": 2, "ts_utc": "2024-03-15T07:30Z" },
    { "det_id": "...", "sensor": "VIIRS", "platform": "NOAA-20",
      "frp": 38.1, "conf_class": 2, "ts_utc": "2024-03-15T07:45Z" }
  ],
  "summary": { "n_modis": 2, "n_viirs": 5, "max_frp": 52.3 }
}
```

### 6.3 Error Handling & Middleware

- All responses wrapped in a standard envelope: `{ status, data, error, provenance }`
- 400 for invalid bbox/date; 404 for unknown cluster_id; 503 if cache is stale beyond threshold
- CORS enabled for the static frontend origin
- Request logging with structured JSON (timestamp, endpoint, params, duration_ms)
- Rate limiting not needed for hackathon; placeholder for production

---

## 07 Harmonization Engine & AI/ML Pipeline

> **RULE:** Deterministic code does the science. Models estimate and explain, and every estimate is validated. The ML components are small, testable and have clear fallbacks, so a failure in one never blocks the demo.

### 7.1 Stage 1: Normalisation

Convert all raw FIRMS data to a common canonical schema. This is where sensor-specific quirks are resolved:

| Step | What It Does | Implementation Detail |
|---|---|---|
| Parse timestamp | Combine acq_date + acq_time into a proper UTC timestamp | `pd.to_datetime` with `format='%Y-%m-%d %H%M'`, `utc=True` |
| Derive local date | Convert UTC to Asia/Dhaka timezone for calendar display | `ts.dt.tz_convert('Asia/Dhaka').dt.date` |
| Map confidence | MODIS 0–100 → three classes; VIIRS l/n/h → same classes | MODIS: 0–29→low, 30–79→nominal, 80–100→high (verify in FIRMS docs) |
| Compute footprint | Calculate pixel area from scan × track | `footprint_km2 = scan * track` |
| Tag sensor family | Assign MODIS or VIIRS based on product name | Use `sensor_family` column, not platform |
| Generate det_id | Stable hash for deduplication | SHA-256 of (product, lat, lon, ts_utc) |

#### Normalisation Code

```python
CONF_VIIRS = {"l": 0, "n": 1, "h": 2}  # low / nominal / high

def to_canonical(df, product):
    is_modis = product.startswith("MODIS")
    ts = pd.to_datetime(df.acq_date.astype(str) + " " +
                        df.acq_time.astype(str).str.zfill(4),
                        format="%Y-%m-%d %H%M", utc=True)
    if is_modis:
        conf = pd.cut(pd.to_numeric(df.confidence),
                      [-1, 29, 79, 100],
                      labels=[0, 1, 2]).astype("Int8")
    else:
        conf = df.confidence.map(CONF_VIIRS).astype("Int8")
    return pd.DataFrame({
        "sensor_family": "MODIS" if is_modis else "VIIRS",
        "platform": df.satellite, "product": product,
        "ts_utc": ts,
        "local_date": ts.dt.tz_convert("Asia/Dhaka").dt.date,
        "lat": df.latitude, "lon": df.longitude,
        "footprint_km2": df.scan * df.track,
        "frp_mw": df.frp,
        "conf_class": conf, "daynight": df.daynight
    })
```

### 7.2 Stage 2: Spatio-Temporal Clustering (Fire Events)

Baseline method: the guide's grid collapse (simple, explainable, good fallback). Main method: DBSCAN with haversine metric run per local date across both sensor families.

| Parameter | Default | Rationale |
|---|---|---|
| eps_km | 1.5 | Reflects geolocation uncertainty of MODIS (coarser sensor); start 1–2 km |
| min_samples | 1 | Every detection matters; no noise rejection at this stage |
| metric | haversine | Proper great-circle distance on the sphere |
| grouping key | local_date | One clustering pass per calendar day (Asia/Dhaka time) |

#### Clustering Code

```python
from sklearn.cluster import DBSCAN

EARTH_R_KM = 6371.0088

def cluster_day(g: pd.DataFrame, eps_km: float = 1.5) -> np.ndarray:
    X = np.radians(g[["lat", "lon"]].to_numpy())
    return DBSCAN(
        eps=eps_km / EARTH_R_KM, min_samples=1,
        metric="haversine", algorithm="ball_tree"
    ).fit_predict(X)

# Run per local_date:
#   labels -> cluster_id = f"{local_date}_{label}"
#   Aggregate: n_modis, n_viirs, corroborated, max_frp, best_conf
```

**Sensitivity analysis:** run clustering at `eps_km` = 0.75, 1.0, 1.5, 2.0, 3.0 km and report a sensitivity table. Choose the value that maximises overlap agreement without merging distant fires.

### 7.3 Stage 3: Calibration (The ML Core)

After clustering, the remaining discrepancy is sensitivity — VIIRS sees fires MODIS cannot. Three layers, from simple to ambitious, shipped in order:

| Layer | Method | Output & Validation |
|---|---|---|
| **A. Detectability Matching (MVP)** | Restrict VIIRS clusters to those a MODIS-class sensor could plausibly detect: aggregate VIIRS detections to a MODIS-like footprint and apply an FRP threshold chosen on the overlap period to maximise agreement. | A "MODIS-equivalent VIIRS" series. Choose threshold by leave-one-year-out cross-validation; report threshold and agreement metric. |
| **B. Sensor Factor (Should)** | Poisson (or quasi-Poisson) GLM on overlap-period daily event counts per district: `n ~ sensor + month + district`, with robust standard errors (HC1). | A multiplicative factor with confidence interval. Apply to convert between sensors; carry interval into plots. Season-specific version if ratio varies by month. |
| **C. Learned Co-Detection (Stretch)** | LightGBM classifier predicting whether a MODIS event is also seen by VIIRS, from FRP, brightness, conf_class, footprint, day/night, local density, month. Calibrated probabilities (isotonic). | Detection-probability surface. Evaluate with spatial-block cross-validation, AUC, calibration curve. Weight events by 1/p. Only ship if it beats Layer B. |

#### Sensor Factor Estimation Code (Layer B)

```python
import statsmodels.api as sm, statsmodels.formula.api as smf

# overlap_df: one row per (district, local_date, sensor_family), n_events
m = smf.glm(
    "n_events ~ C(sensor_family) + C(month) + C(district)",
    data=overlap_df,
    family=sm.families.Poisson()
).fit(cov_type="HC1")

ratio = np.exp(m.params["C(sensor_family)[T.VIIRS]"])
lo, hi = np.exp(m.conf_int().loc["C(sensor_family)[T.VIIRS]"])

# Divide VIIRS-era counts by ratio for MODIS-equivalent;
# carry [lo, hi] into plotted uncertainty band
```

#### Confidence-Aware Event Score

Instead of just counting events, create a composite score with transparent, configurable components:

| Component | Weight (default) | Source |
|---|---|---|
| Confidence class | 0.30 | Best confidence among member detections (mapped to 0–1) |
| Corroboration | 0.25 | Binary: both sensor families present? (0 or 1) |
| FRP strength | 0.20 | Log-scaled max FRP, normalised to [0, 1] |
| Temporal spread | 0.15 | Hours between first and last detection (persistence signal) |
| Platform diversity | 0.10 | Distinct platforms / max possible platforms |

> **NOTE:** Do not arbitrarily invent scientific coefficients. Make weights configurable and show all components to the user. This gives transparent harmonization instead of black-box fire prediction.

### 7.4 Stage 4: Seasonal Baseline & Anomaly Detection

- **Baseline:** for a chosen area and day-of-year, collect harmonised daily counts within a ±7-day window across baseline years; store selected percentiles (p10, p50, p90, p95)
- **Anomaly:** empirical percentile of the observed value in that distribution, with window and sample size displayed. Use mid-rank percentile to handle ties (many days have zero fires)
- **Optional:** STL decomposition or Poisson tail probability for trend-adjusted view. Keep empirical percentile as headline because it is easy to explain
- **Language rule:** say "unusual for this place and time of year" — never "will spread" or "danger"

### 7.5 Stage 5: Validation Framework

This is the evidence judges will look for. Validation is not a nice-to-have — it is the core of the Validity score.

| Test | What It Shows | Success Criterion |
|---|---|---|
| Overlap correlation | On the period both sensors observed, compute correlation of raw MODIS vs raw VIIRS, then harmonised vs harmonised | Harmonised correlation is higher than raw |
| Overlap ratio | Mean daily count ratio between sensors, raw vs harmonised | Harmonised ratio is closer to 1.0 |
| Step-change test | Segmented regression or CUSUM at sensor handover on stitched long record | Raw shows significant shift; harmonised does not (or shift is within interval) |
| Parameter sensitivity | Results across cluster radius, confidence filter, cell size | Result is stable across reasonable parameter choices |
| Bootstrap intervals | Block bootstrap over days/weeks for ratio and harmonised series | Intervals are narrow enough to be useful; reported honestly |
| Independent cross-check | Compare harmonised seasonal shape with MCD64A1 burned-area timing | Timing agreement (not proof, but supportive evidence) |
| Unit tests | Synthetic cases: fire seen by both sensors, VIIRS-only small fire, boundary cases | All deterministic tests pass |

> **RULE — Honesty guardrails (also good for the Validity score):**
>
> - State on screen that hotspots are detections, not fire perimeters
> - Show that MODIS and VIIRS confidence values are mapped to classes, not 1:1
> - Show the interval, not only the point estimate
> - If the sensor factor differs by season or land type, say so

### 7.6 LLM/Agent Integration

The language model is optional and confined to explanation. Architecture:

| Rule | Description |
|---|---|
| Input | A JSON object with area, dates, raw + harmonised counts, interval, percentile, validation numbers, dataset names |
| Output | A short brief that may only quote numbers present in that input JSON |
| Fallback | A Jinja2 template produces the same brief without any model call (offline-safe) |
| Constraint | The LLM never computes statistics, geometry or physics itself |
| Disclosure | Record the tool, model name, and key prompts in `docs/AI_USE.md` |

---

## 08 Data Acquisition Pipeline

### 8.1 NASA FIRMS Integration

| Source | Endpoint / Method | Use Case |
|---|---|---|
| FIRMS Bulk Archive | Download CSV/SHP from FIRMS archive page | Multi-year historical data for MODIS and VIIRS; do this before the event |
| FIRMS Area API | `GET https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{source}/{bbox}/{days}` | Recent days (last 10) to supplement archive; rate-limited to 5000 tx / 10 min |
| Earthdata Login | OAuth2 for data access | Required for FIRMS MAP_KEY and bulk downloads |

### 8.2 Supporting Data Sources

| Source | What | Purpose |
|---|---|---|
| NASA GIBS | Web Map Tile Service imagery | Context basemap (true-colour, fire RGB) for the map view |
| NASA POWER | Surface meteorology (temperature, precipitation, wind) | Weather context for anomaly explanation |
| NASA MCD64A1 | MODIS Burned Area product | Independent cross-check of harmonised seasonal shape (optional) |
| Local data (optional) | Bangladesh Met Dept records | Partner dataset for NASA-data-usage score |

### 8.3 Caching & Fixture Strategy

- **Raw layer:** one Parquet file per product per year, unmodified FIRMS columns (git-ignored)
- **Demo fixtures:** a small subset (~30 days × pilot area) committed to the repo in `cache/demo_fixtures/`
- **GIBS tiles:** pre-download for the pilot region + date range; store as PNG/WebP in `cache/tiles/`
- **Acquisition script:** `make cache` downloads everything; `make demo` runs with `OFFLINE=1`
- **Retry logic:** exponential backoff with 3 retries; on failure, fall back to cached data silently

---

## 09 Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python >= 3.14 | Strongest data science + ML ecosystem; team familiarity |
| API Framework | FastAPI + uvicorn | Async, auto-docs (OpenAPI/Swagger), orjson serialisation |
| Data Processing | pandas, numpy, DuckDB | DuckDB gives SQL over Parquet without a server; spatial extension for geo queries |
| Geospatial | shapely, geopandas, h3-py (optional) | Spatial operations, bounding box filtering, optional H3 hexagonal indexing |
| ML — Clustering | scikit-learn (DBSCAN) | Haversine metric, no need to specify cluster count, well-tested |
| ML — Calibration | statsmodels (Poisson GLM), scipy | Standard statistical modelling with robust standard errors |
| ML — Stretch | LightGBM (gradient boosting) | Fast, handles mixed features, calibrated probabilities via isotonic regression |
| Validation | pytest, scipy.stats | Unit tests for deterministic functions; statistical tests for step-changes |
| Serialisation | orjson, Parquet (pyarrow) | Fast JSON for API; columnar Parquet for storage + analytics |
| Frontend (teammate) | MapLibre GL, D3.js / Observable Plot | Open-source map renderer; powerful charting for calendar heatmap |
| Optional: LLM | Claude API or OpenAI API | Explanation-only agent with template fallback |
| Optional: DB | PostgreSQL + PostGIS | Only if DuckDB is insufficient; not needed for hackathon MVP |

---

## 10 Repository Structure

```
firefusion/
├── LICENSE                 # Apache-2.0
├── README.md               # Project overview, setup, demo instructions
├── Makefile                # make cache, make pipeline, make demo, make test
├── pyproject.toml          # Dependencies, pinned versions
├── config/
│   └── aoi.yaml            # bbox, dates, cluster radius, quality filter, timezone
├── src/
│   ├── acquire/
│   │   ├── firms.py        # FIRMS bulk + area API download
│   │   ├── gibs.py         # GIBS tile pre-fetcher
│   │   ├── power.py        # NASA POWER weather context
│   │   └── safe.py         # Retry, fallback, offline wrapper
│   ├── compute/
│   │   ├── schema.py       # Canonical schema definition (pydantic)
│   │   ├── normalise.py    # FIRMS → canonical conversion
│   │   ├── cluster.py      # DBSCAN per-day clustering
│   │   ├── calibrate.py    # Detectability matching, Poisson GLM, LightGBM
│   │   ├── baseline.py     # Day-of-year baseline + anomaly percentile
│   │   ├── aggregate.py    # Pre-compute daily + cell aggregates
│   │   └── validate.py     # Overlap correlation, step-change, sensitivity
│   ├── api/
│   │   ├── main.py         # FastAPI app, CORS, startup
│   │   ├── routes/
│   │   │   ├── calendar.py     # /calendar endpoint
│   │   │   ├── cells.py        # /cells endpoint
│   │   │   ├── clusters.py     # /clusters/{id} + /clusters/search
│   │   │   ├── validation.py   # /validation endpoint
│   │   │   ├── anomaly.py      # /anomaly + /baseline endpoints
│   │   │   ├── brief.py        # /brief endpoint (template + optional LLM)
│   │   │   └── meta.py         # /meta + /health endpoints
│   │   └── models.py       # Pydantic response models
│   └── agents/
│       └── explain.py      # Optional LLM explainer (no computation)
├── cache/                  # Parquet files (git-ignored)
│   └── demo_fixtures/      # Small subset for offline demo (committed)
├── tests/
│   ├── test_normalise.py
│   ├── test_cluster.py
│   ├── test_calibrate.py
│   ├── test_validate.py
│   └── test_api.py
├── docs/
│   ├── AI_USE.md           # AI disclosure (required)
│   ├── METHODS.md          # Scientific methodology
│   └── LIMITATIONS.md      # What this does and does not mean
└── web/                    # Static frontend (teammate)
    ├── index.html
    ├── map.js
    └── calendar.js
```

---

## 11 Testing & Validation Strategy

| Test Category | What | Tool |
|---|---|---|
| Unit tests | Deterministic synthetic cases: a fire seen by both sensors counts once; VIIRS-only small fire counts once; cell-boundary cases; date-boundary cases for local time | pytest |
| Schema tests | Validate that normalised output matches canonical schema; check for nulls, type mismatches, invalid enum values | pytest + pydantic |
| Statistical tests | Step-change test (segmented regression or CUSUM); overlap correlation; bootstrap confidence intervals | scipy, statsmodels |
| Sensitivity tests | Run pipeline at multiple cluster radii (0.75, 1.0, 1.5, 2.0, 3.0 km) and report stability | Custom script |
| API tests | Endpoint contract tests: correct status codes, response shapes, provenance present, edge cases (empty bbox, invalid dates) | pytest + httpx |
| Integration test | Full pipeline from raw Parquet → API response → validate output matches expected fixtures | `make test-integration` |
| Offline test | Run with `OFFLINE=1` and verify all endpoints return valid data from fixtures | `make test-offline` |

---

## 12 Deployment Architecture

For a 48-hour hackathon, keep deployment simple. The system is designed to run entirely on a single machine.

| Component | Deployment | Notes |
|---|---|---|
| Backend (FastAPI) | uvicorn on localhost:8000 | Single process is sufficient for demo; production would use gunicorn with multiple workers |
| Frontend | Static files served by FastAPI or a simple HTTP server | No build step needed for vanilla HTML/JS; if using a framework, pre-build |
| Database | DuckDB (in-process, no server) | Reads from Parquet files; no installation needed |
| Data cache | Local filesystem (`cache/` directory) | Pre-populated before the event |
| Optional: Docker | `docker-compose.yml` with one service | Only if team wants portable demo; not required |

#### Production Architecture (If Advanced to Global)

Post-hackathon scaling path (for reference only, not built during the event):

- **Backend:** containerised FastAPI on a cloud platform (Fly.io, Railway, or AWS ECS)
- **Storage:** Parquet on S3 + DuckDB for queries; or PostgreSQL + PostGIS for multi-user access
- **Caching:** Redis for API response caching
- **CI/CD:** GitHub Actions for tests + deployment on push to main

---

## 13 48-Hour Hackathon Execution Plan

### 12.1 Key Dates & Deadlines

| Date | Milestone | Action |
|---|---|---|
| 1 Oct 2026 | 240-second prescreening video due (11:59 PM) | Record concept video from this document; no real results needed yet |
| 28 Oct 2026 | Full challenge statements + named datasets published | Re-check product names, AOI, any scope changes |
| 13 Nov 2026 | Detailed submission/judging guides; Bangladesh event start | Read submission guide that morning; final data refresh |
| 13–14 Nov (BD) / 14–15 Nov (global) | Hackathon weekend | Execute the plan below |

### 12.2 Pre-Event Preparation (Now to 12 Nov)

25. Register for Earthdata Login; get FIRMS MAP_KEY and NASA API key; test each with one call
26. Create public repository with licence, README skeleton, `docs/AI_USE.md`, and the layout from Section 10
27. Download multi-year FIRMS archives for MODIS and VIIRS over the AOI; write Parquet; record row counts
28. Implement and unit-test normalisation and grid-collapse baseline; produce first raw vs baseline-harmonised plot
29. Implement clustering; run the radius sensitivity table
30. Implement overlap validation and Poisson sensor factor; freeze metrics that go on screen
31. Cache GIBS tiles, POWER data, and fixtures; build `make cache` and `make demo` with `OFFLINE=1`
32. Agree API contract (Section 6) with frontend teammate; both work in parallel with mock JSON
33. Pre-record a fallback demo video as safety net

*(List numbering follows the original PDF.)*

### 12.3 Day 1 & Day 2 Task Breakdown (Developer Tasks)

| Block | Developer Tasks | Deliverable |
|---|---|---|
| Day 1 Morning | Re-verify data against 28 Oct statement; rebuild pipeline end-to-end; lock cluster radius and quality filter; publish first API endpoints | Pipeline runs green; API serves /calendar and /cells with real data |
| Day 1 Afternoon | Serve calendar and cells endpoints; make raw/harmonised toggle work against the API; help frontend integrate | Raw ↔ Harmonised toggle works; first visual on screen |
| Day 1 Evening | Baseline and anomaly endpoints; validation endpoint; help record local judging video with real numbers | Anomaly + validation endpoints live; judging video recorded |
| Day 2 Morning | Uncertainty bands; methods/validation panel data; template brief (LLM optional); performance + offline test | /brief endpoint; offline test passes; all "Should" items done |
| Day 2 Noon | Freeze code; tag release; verify repo opens in private window; complete project page + AI-use disclosure; submit | Tagged release; project page complete; submission confirmed |

### 12.4 Cut Order (If Behind)

Drop features in this order, protecting the core to the end:

34. Drop second demonstration region (keep Bangladesh only)
35. Reduce time range to 5 years instead of full 20+
36. Drop the anomaly engine (baseline + seasonal view)
37. Drop the learned co-detection model (Layer C)
38. Drop the LLM explainer (keep template brief)
39. **NEVER** drop: harmonisation, validation, or the raw/harmonised toggle

> **PROTECT:** Keep one memorable moment: the toggle where the artefact fades and the seasonal signal appears. Protect it above all other features.

---

## 14 Judging Alignment Strategy

| Criterion | Points | How This Design Earns It |
|---|---|---|
| Impact | (1–20) Target: 16+ | Continuity of fire record as MODIS retires; Bangladesh and neighbouring burning-season framing (crop residue, hill-region shifting cultivation, forest fire) with measured numbers |
| Creativity | (1–20) Target: 16+ | Raw/harmonised toggle that visibly removes a sensor artefact; cluster evidence panel showing which sensor saw what; confidence-aware scoring |
| Validity | (1–20) Target: 18+ | Overlap-period validation, step-change test, bootstrap confidence intervals, deterministic code with tests, methods panel with limitations |
| Relevance | (1–20) Target: 18+ | FIRMS MODIS + VIIRS are the core input, named on screen and on camera; GIBS context; NASA POWER weather data |
| Presentation | (1–20) Target: 15+ | One clear story in 240 seconds: problem → artefact → fix → proof → use |
| NASA Data Usage | (1–5) Target: 5 | FIRMS + NASA POWER + optionally MCD64A1 + a partner/local dataset |
| Free Points | (0/1 × 3) Target: 3/3 | Name the challenge, public repo that opens without login, complete project page |

---

## 15 Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Harmonised series still shows step at handover | Weakens core claim | Medium | Layers A+B together; show residual honestly with interval; test several radii |
| Data volume too large for time | Slow clustering, missed demo | Medium | Start with Bangladesh box; per-day parallel clustering; precomputed aggregates |
| FIRMS access or rate limits | Missing data at event time | Low | Bulk pre-download; fixtures; `OFFLINE=1` |
| Sensor start dates or field values differ from assumptions | Schema bugs | Medium | Inspect real files first; schema tests; keep raw layer untouched |
| Over-claiming (fire spread, evacuation) | Validity penalty, misuse risk | Low | Fixed wording rules; limitations page; no prediction of spread |
| UI clutter / poor UX | Lower presentation score | Medium | Simple date/region filters, one toggle, clear legend |
| Official statement changes scope on 28 Oct | Rework | Medium | Config-driven product names and AOI; re-read on release day |
| LLM invents numbers | Validity penalty | Medium | Numbers only from JSON object; template fallback; cite-check test |
| Demo wifi fails | Cannot show product | Medium | `OFFLINE=1` mode; pre-recorded fallback video |
| Team member unavailable | Lost capacity | Low | Pre-build as much as possible; documented API contract enables parallel work |

---

## 16 Suggested Project Topic & Pitch

### 15.1 Three Topic Framings

Three framings of the same technical core; they differ only in the story told to judges. Option A is recommended.

| Option | Title & Tagline | Why Choose It |
|---|---|---|
| **A (Recommended)** | **FireFusion: One Continuous Fire Record for South Asia** — Keeping 25 years of fire history comparable as MODIS retires and VIIRS takes over | Directly matches challenge text and sensor-retirement news; strongest Validity story (artefact removed, proof on screen); simplest to explain in 240 seconds |
| B | **Burn Calendar Bangladesh** — When and where the region burns, on one trustworthy calendar | Stronger local Impact and Bangladesh framing (crop residue, hill-region, forest burning); slightly less about the science, so keep validation visible |
| C | **Sensor Handover Watch** — An early-warning view that flags when a new sensor's counts differ from the old one's expectation | Creative twist for early warning; needs baseline + anomaly engine working, so higher risk in 48 hours |

### 15.2 Recommended Narrative for Option A (~240 seconds)

| Time | Content |
|---|---|
| 0:00–0:30 | Team VU_Surveyors, all members named. Fire history matters for responders and land managers; the satellite record is changing under our feet. |
| 0:30–1:15 | The problem: MODIS at 1 km and VIIRS at 375 m see fires differently; Suomi-NPP delivery ends 1 Nov 2026 and MODIS is being retired. Stitching creates a false jump. |
| 1:15–2:15 | Approach: FIRMS data → common schema → event clustering → detectability matching → sensor factor with interval. Name the datasets on camera. |
| 2:15–3:15 | Demo: toggle raw to harmonised over the pilot area; show validation numbers and the calendar; open one cluster to see both sensors' evidence. |
| 3:15–4:00 | Impact and honesty: what it means and does not mean; open-source, offline-capable; next steps (more regions, NOAA-21 continuity, MCD64A1 cross-check). |

### 15.3 Hackathon-Level Advice

- Secure the three free points first (challenge named, public repo, project page complete) and keep them safe
- Keep one memorable moment: the toggle where the artefact fades and the seasonal signal appears
- Write `docs/AI_USE.md` as you go; cite every dataset with an ID and URL
- If the team has any women members, the guide lists a +5% aggregate bonus on the score sheet
- For the prescreening video (concept only), use the narrative above without quoting result numbers you haven't measured yet

#### Additional Suggested Project Names

| Name | Tagline | Fit |
|---|---|---|
| FireFusion | Confidence-Aware Wildfire Intelligence | Best fit — fusing observations, not displaying them |
| FireSync | Harmonizing NASA Fire Observations | Clear and descriptive |
| ThermalBridge | Bridging MODIS and VIIRS Fire Records | Emphasises the transition problem |
| PyroFusion | Multi-Sensor Fire Activity Harmonization | More scientific feel |
| FireLens | NASA Fire Activity Intelligence | Broader scope, less specific |

---

## 17 Open Questions

40. Final pilot area: Bangladesh only, or Bangladesh plus neighbouring regions? (affects data volume and story)
41. Which record do we harmonise: MODIS-only until 2012 then VIIRS, or the combined MODIS + VIIRS record throughout? Decide and state it in the methods panel.
42. Which partner or local data will we add for the NASA-data-usage score (e.g., Bangladesh Meteorological Department records)?
43. Who owns the frontend, and can we agree the JSON contract this week?
44. Confirm event dates, local judging upload time, and video rules with the Local Lead.
45. Team name consistency: files say "Team Surveyors"; registration says "VU_Surveyors". Use one spelling everywhere.
46. PostGIS vs. offline-first: DuckDB with spatial extension gives both SQL and no server. Keep PostGIS optional.

---

## 18 Review of Provided Resources

| Resource | What It Is | How Useful It Is |
|---|---|---|
| Team strategy PDF (86 pages) | Guidebook covering all 14 challenges with strategy analysis, team ranking, and "FireFusion" proposal for challenge 9 | Useful for scope: recommends 7–30 day pilot window, common schema, UTC normalisation, spatio-temporal clustering, cluster evidence panel |
| Build guide (HTML) | Technical companion for Bangladesh local events: shared architecture, FIRMS endpoints, 48-hour plan, runnable harmonisation snippet, judging criteria, submission checklist | Most actionable of all files; this design builds on it directly |
| NASA Space Apps 2026 Guidebook | Overview of all 14 challenges with difficulty ratings, skills/tools, risks, AI agent roles, judging criteria | Confirms Challenge 9 as "MEDIUM" difficulty with strong data availability; validates our scope decisions |
| ChatGPT analysis | Detailed review of the problem with architecture recommendations, ML features, frontend views, demo script | Good starting point; this document corrects several issues (confidence filtering, sensitivity gap) and adds implementation detail |

### What Is Strong in the Existing Plans

- Clear success definition: accurate, time-based map reconciling MODIS (longer record) and VIIRS (higher resolution)
- Sound engineering: offline-first demo, deterministic science code, models only explain, every dataset cited
- Good scoping discipline: cut list protects the core (one region, five years, drop anomaly before harmonisation)
- Honest limitations: hotspots are not fire boundaries, confidence fields are not comparable, no fire-spread claims

### Issues Identified & Corrected in This Design

| # | Issue | Correction |
|---|---|---|
| 1 | Confidence filter not portable across sensors (sample SQL uses `confidence >= 50`) | Map both to common three-class scale before filtering |
| 2 | Grid-collapse alone won't equalise sensitivity | Added detectability matching + Poisson sensor factor (Section 7.3) |
| 3 | 'Sensors agreeing' counts platforms, not families | Use `sensor_family` column (MODIS/VIIRS), keep platform separately |
| 4 | UTC date vs local date | Calendar uses Asia/Dhaka local date; UTC kept for provenance |
| 5 | Unverified headline numbers ('counts triple') | Treat as hypothesis; measure on real data before pitching |
| 6 | Sensor end-of-life dates need citation | Say 'being retired' rather than one exact date; cite NASA pages |
| 7 | Datasets not final until 28 Oct | Config-driven product names and AOI; re-read on release day |
| 8 | Event date discrepancies between files | Confirm with Local Lead |
| 9 | Team name spelling inconsistency | Use 'VU_Surveyors' everywhere |
| 10 | PostGIS vs offline-first tension | DuckDB with spatial extension as default; PostGIS optional |

---

## 19 Appendix: Additional Code Samples

### A.1 Configuration File (`config/aoi.yaml`)

```yaml
# FireFusion configuration
aoi:
  name: "Bangladesh"
  bbox: [88.0, 20.0, 93.0, 27.0]   # [lon_min, lat_min, lon_max, lat_max]
  timezone: "Asia/Dhaka"
data:
  start_date: "2000-11-01"          # Terra MODIS start
  end_date: "2026-09-30"
  products:
    - "MODIS_C6.1"
    - "VIIRS_SNPP_NRT"
    - "VIIRS_NOAA20_NRT"
clustering:
  eps_km: 1.5
  min_samples: 1
  sensitivity_radii: [0.75, 1.0, 1.5, 2.0, 3.0]
quality:
  min_conf_class: 1                 # 0=low, 1=nominal, 2=high
  exclude_static: true
calibration:
  overlap_start: "2012-01-01"
  overlap_end: "2026-09-30"
  bootstrap_n: 1000
  random_seed: 42
```

### A.2 FastAPI Application Entry Point

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import calendar, cells, clusters, validation, anomaly, brief, meta

app = FastAPI(
    title="FireFusion API",
    description="Sensor-harmonised wildfire intelligence",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Restrict in production
    allow_methods=["GET"],
    allow_headers=["*"]
)

app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
app.include_router(cells.router, prefix="/cells", tags=["Cells"])
app.include_router(clusters.router, prefix="/clusters", tags=["Clusters"])
app.include_router(validation.router, prefix="/validation", tags=["Validation"])
app.include_router(anomaly.router, prefix="/anomaly", tags=["Anomaly"])
app.include_router(brief.router, prefix="/brief", tags=["Brief"])
app.include_router(meta.router, prefix="/meta", tags=["Metadata"])

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "offline" if OFFLINE else "live"}
```

### A.3 Makefile Commands

```makefile
.PHONY: cache pipeline demo test

cache:  # Download all data
	python -m src.acquire.firms
	python -m src.acquire.gibs
	python -m src.acquire.power

pipeline:  # Run full harmonisation pipeline
	python -m src.compute.normalise
	python -m src.compute.cluster
	python -m src.compute.calibrate
	python -m src.compute.baseline
	python -m src.compute.aggregate
	python -m src.compute.validate

demo:  # Start offline demo
	OFFLINE=1 uvicorn src.api.main:app --port 8000

test:  # Run all tests
	pytest tests/ -v --tb=short

test-offline:  # Verify offline mode works
	OFFLINE=1 pytest tests/test_api.py -v
```

### A.4 Team Role Split

| Role | Person | Owns |
|---|---|---|
| Backend + AI/ML (You) | Developer | Acquisition, schema, harmonisation engine, calibration, validation, API, tests, system design |
| Map / Frontend | Developer Teammate | MapLibre map, calendar heatmap, toggle, evidence panel; consumes mock JSON first |
| UI/UX | Designer Teammate | Legends, filter simplicity, uncertainty display, methods page |
| Science & Documentation | Teammate | Sensor facts, citations, METHODS.md, LIMITATIONS.md, project page text |
| Pitch & Submission | Teammate | Prescreening video, local + 30-second global videos, subtitles, final checklist |

### Sources Consulted

- NASA FIRMS MODIS active fire description (product coverage; Suomi-NPP delivery ends 1 Nov 2026)
- NASA Earthdata / LAADS DAAC pages on the MODIS to VIIRS transition
- NASA Earthdata page on the VIIRS I-band 375 m active fire product
- NASA Space Apps Challenge 2026 Team Guidebook
- NASA Space Apps Challenge 2026 Bangladesh Build Guide
- All 14 Problem Analysis and Selection (team document)

*Field-level details (thresholds, platform labels, start dates) should be checked against the current FIRMS attribute tables before the schema is frozen.*
