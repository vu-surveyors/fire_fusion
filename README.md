# FireFusion · NASA Space Apps Challenge 2026

<div align="center">

**Harmonization of MODIS and VIIRS Hot Spots**  
*Global Thermal Sensing & Wildfire Continuity Across 25 Years of Earth Observations*

[![Challenge: Harmonization of MODIS and VIIRS Hot Spots](https://img.shields.io/badge/NASA%20Space%20Apps%202026-Challenge%20%2309-blue.svg)](https://www.spaceappschallenge.org/)
[![Track](https://img.shields.io/badge/Theme-The%20Next%20Frontier-0B5FD9.svg)](#)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.3-black.svg?logo=next.js)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19.2-61DAFB.svg?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.2-FFF000.svg?logo=duckdb)](https://duckdb.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python)](https://python.org/)
[![Turborepo](https://img.shields.io/badge/Turborepo-2.11-EF4444.svg?logo=turborepo)](https://turbo.build/)
[![Bun](https://img.shields.io/badge/Bun-1.2.21-F472B6.svg?logo=bun)](https://bun.sh/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

</div>

---

## Executive Summary

As NASA transitions away from the historic **MODIS** sensors (scheduled for decommissioning in late 2026) and data access models for **Suomi-NPP** evolve, global wildfire science faces an urgent data continuity crisis. 

The Visible Infrared Imaging Radiometer Suite (**VIIRS**) offers a sharp 375 m pixel resolution, whereas the Moderate Resolution Imaging Spectroradiometer (**MODIS**) records at 1 km. Because the finer VIIRS sensor detects significantly smaller and cooler thermal anomalies, naive counts create an **artificial ~3× surge** at the sensor handover point. This jump is an instrument artifact—not an actual surge in fires.

**FireFusion** solves this challenge by delivering an open-source spatio-temporal harmonization engine and interactive exploration platform. By clustering detections onto a standardized common grid, modeling cross-sensor detectability, and computing rolling seasonal baselines, FireFusion bridges 25 years of NASA Earth observation data into a unified, scientifically sound record.

> [!IMPORTANT]
> **Safety & Science Disclaimer:** FireFusion is an exploratory analytical platform developed for satellite thermal anomaly research and trend analysis. It is not an operational tactical wildfire prediction tool or real-time evacuation system.

---

## The Killer Demonstration: Raw vs. Harmonized

In raw active fire series across South Asia and global hotspots, the 2012+ sensor transition appears to show fire frequency tripling overnight.

- **With Raw Data**: The handover creates an uncalibrated step-change artifact, corrupting multi-decadal climate analysis and trend statistics.
- **With FireFusion Harmonization**: Same-day detections within uniform 5.5 km grid cells are collapsed, eliminating sensor-resolution inflation while preserving true physical fire signals and revealing long-term climate dynamics.

---

## Key Capabilities

1. **Interactive Hotspot & Activity Map (`/map`)**:
   - Spatial visualization of NASA FIRMS thermal anomaly markers with sensor layer filtering (MODIS Terra/Aqua vs. VIIRS NOAA-20/21/S-NPP).
   - Granular inspection of cluster boundaries, Fire Radiative Power (FRP), and confidence classifications.

2. **Burning Activity Calendar Heatmap (`/calendar`)**:
   - Year-by-day matrix visualizing annual burning seasons, seasonal agricultural fire peaks, and fire frequency shifts.

3. **Cluster Evidence Explorer (`/evidence` & `/evidence/[clusterId]`)**:
   - DBSCAN spatio-temporal clustering breakdown detailing detection counts, sensor agreement rates, peak radiative power, and timeline progression.

4. **Cross-Sensor Validation Suite (`/validation`)**:
   - Quantitative evaluation during concurrent dual-observation overlap periods.
   - Directly measures and reports the correlation improvement between raw cross-sensor series and harmonized cross-sensor series.

5. **Seasonal Baseline & Anomaly Engine**:
   - Evaluates: *"Is current thermal activity unusual for this region and time of year?"*
   - Computes historical percentile distributions (e.g. 90th percentile) against a rolling day-of-year window.

6. **Scientific Methodology & Guardrails (`/methods`)**:
   - Transparent documentation of formulas, grid cell thresholds, uncertainty models, and observational constraints.

---

## Harmonization Methodology: 5-Stage Pipeline

FireFusion implements a deterministic 5-stage harmonization workflow:

```text
┌───────────────────────┐
│  01. ACQUISITION      │ ──► NASA FIRMS MODIS (1 km) + VIIRS (375 m NOAA-20/21/S-NPP)
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  02. NORMALIZATION    │ ──► Canonical schema mapping; filter confidence >= 50
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  03. CLUSTERING       │ ──► Spatio-temporal DBSCAN & 5.5 km common grid binning
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  04. CALIBRATION      │ ──► Poisson GLM cross-sensor detectability adjustment
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  05. AGGREGATION      │ ──► Continuous harmonized daily & seasonal time-series
└───────────────────────┘
```

### Grid Binning Logic

```python
# Collapse same-day detections onto a standard grid (e.g., 5.5 km ~ 0.05°)
# A single cell-day with one or multiple detections counts as one active fire footprint.
deg = cell_km / 111.0
cell_x = floor(longitude / deg)
cell_y = floor(latitude  / deg)
```

### Scientific Honesty Guardrails

- **Hotspots are Detections, Not Perimeters**: Thermal anomaly markers indicate active combustion within a pixel, not perimeter polygons or total burned area.
- **Categorical Confidence**: Detections are grouped into mapped confidence tiers rather than over-interpreting raw confidence floats.
- **Traceable Provenance**: Every metric displays its underlying sensor source, satellite platform, and processing parameters.
- **Offline Reliability**: The platform bundles offline data fixtures to ensure robust demonstration even in zero-connectivity environments.

---

## NASA Datasets Used & Cited

FireFusion directly utilizes and cites the following NASA Earth Science data products:

| Dataset / Product | Platform / Sensor | Spatial Resolution | Provider |
| :--- | :--- | :--- | :--- |
| **MCD14DL (Active Fire)** | Terra & Aqua (MODIS) | 1 km | NASA FIRMS / LANCE |
| **VNP14IMGTDL (Active Fire)** | Suomi-NPP (VIIRS) | 375 m | NASA FIRMS / LANCE |
| **VJ114IMGTDL (Active Fire)** | NOAA-20 & NOAA-21 (VIIRS) | 375 m | NASA FIRMS / LANCE |
| **NASA POWER API** | Surface Meteorology (Wind, Temp, RH) | Gridded 0.5° | NASA POWER Project |
| **Overlap Validation Cohort** | Dual-Sensor Concurrent Acquisitions | Multi-sensor | NASA Earthdata |

---

## Monorepo Architecture

This project is built using a modern **Turborepo** monorepo managed with **Bun**:

```text
fire-fusion/
├── apps/
│   ├── api/                         # FastAPI & DuckDB spatio-temporal harmonization engine
│   │   ├── src/api/                 # REST endpoints (brief, bundle, clusters, calendar, validation)
│   │   ├── src/compute/             # 5-stage pipeline (normalize, cluster, calibrate, baseline)
│   │   ├── src/db/                  # DuckDB schema, connection pool & spatial indexes
│   │   ├── data/                    # NASA FIRMS 2020 & 2025 MODIS/VIIRS historical archives
│   │   └── tests/                   # 18/18 pytest validation & pipeline integration tests
│   └── web/                         # Next.js 16 App Router application
│       ├── app/                     # Route pages & screen layouts
│       ├── components/              # App UI components & layout frames
│       ├── config/                  # Navigation & metadata configurations
│       ├── content/                 # Scientific pipeline & guardrail definitions
│       ├── features/                # Domain modules (map, calendar, validation, methods)
│       └── public/                  # Static assets & hydrated desktop prototype
├── packages/
│   ├── ui/                          # Shared UI package with 50+ Shadcn UI components
│   │   ├── src/components/ui/       # Radix UI primitives & styled components
│   │   ├── src/hooks/               # Shared hooks (use-toast, use-mobile)
│   │   ├── src/lib/utils.ts         # Tailwind class merging (cn utility)
│   │   └── tailwind.config.ts       # Central theme & semantic CSS variables
│   ├── typescript-config/           # Monorepo TypeScript base configs
│   └── eslint-config/               # Shared ESLint rules
├── docker-compose.yml               # Production container configuration
├── docker-compose-development.yml   # Multi-service development setup (DuckDB container)
├── docker-compose-local.yml         # Local OpenTelemetry observability stack
├── Dockerfile                       # Multi-stage container build (Bun + Node 20 Alpine)
├── LICENSE                          # Apache-2.0 open-source license
└── turbo.json                       # Turborepo task pipeline
```

---

## Available Application Routes & Endpoints

### Frontend Routes (`apps/web` on `:3000`)
| Path | Screen | Purpose |
| :--- | :--- | :--- |
| `/` | **Overview** | System summary, mission objective, and navigation hub |
| `/map` | **Fire Activity Map** | Interactive geospatial hotspot exploration and filtering |
| `/calendar` | **Burning Calendar** | Matrix calendar of daily active fire counts and seasonality |
| `/evidence` | **Cluster Evidence** | In-depth cluster details, sensor agreement, and FRP trends |
| `/evidence/[clusterId]` | **Cluster Deep Dive** | Specific evidence records for a targeted detection cluster |
| `/validation` | **Model Validation** | Quantitative cross-sensor correlation and benchmark controls |
| `/methods` | **Methods & Guardrails**| Scientific equations, pipeline stages, and sensor limits |

### Backend REST Endpoints (`apps/api` on `:8000`)
| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/docs` | `GET` | Interactive Swagger / OpenAPI documentation |
| `/api/v1/health` | `GET` | Service & DuckDB database connectivity healthcheck |
| `/api/v1/brief` | `GET` | Daily harmonized active fire summary & sensor counts |
| `/api/v1/clusters` | `GET` | Spatial cluster list, bounding boxes, and FRP stats |
| `/api/v1/bundle` | `GET` | Full evidence bundle for a specific spatial cluster |
| `/api/v1/calendar` | `GET` | Multi-year daily fire counts matrix (2020–2025) |
| `/api/v1/anomalies` | `GET` | Rolling day-of-year seasonal anomaly calculations |
| `/api/v1/validation` | `GET` | Cross-sensor correlation improvement metrics |
| `/api/v1/pipeline/run` | `POST` | Trigger background re-run of the 5-stage pipeline |

---

## Quickstart & Local Setup

### Prerequisites

- **Bun**: `v1.2.21` or higher ([Install Bun](https://bun.sh))
- **Node.js**: `>= 20.9`
- **Python**: `>= 3.12` and [**uv**](https://docs.astral.sh/uv/) (for `apps/api`)
- **Docker**: (optional, for DuckDB container or containerized deployments)

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/Redemption4254/fire_fusion.git
cd fire_fusion
bun install --frozen-lockfile
```

### 2. Configure Backend & Run Pipeline

```bash
# Setup Python virtual environment with uv
cd apps/api
uv sync

# Run the 5-stage harmonization pipeline (processes bundled NASA FIRMS data into DuckDB)
uv run python -m src.compute.pipeline
cd ../..
```

### 3. Start the Development Servers

```bash
# Start all workspaces concurrently (Next.js frontend + FastAPI backend via Turborepo)
bun run dev

# Or run services individually:
bun run dev --filter=web    # Frontend on http://localhost:3000
bun run dev --filter=api    # Backend on http://localhost:8000
```

### 4. Quality & Verification Scripts

```bash
# Static TypeScript validation across all workspaces
bun run check-types

# ESLint inspection
bun run lint

# Backend pytest suite (18/18 tests)
bun run --cwd apps/api test
# or: uv run --directory apps/api pytest

# Monorepo production build
bun run build
```

---

## Container Deployment

The application includes a production-ready, multi-stage [`Dockerfile`](./Dockerfile) and [`docker-compose.yml`](./docker-compose.yml) configured for standalone execution.

```bash
# Build and run container
docker compose up --build -d

# View application logs
docker compose logs -f web

# Stop container
docker compose down
```

The container runs with non-root security (`nextjs:nodejs`), pre-configured health checks (`wget http://127.0.0.1:3000/`), and minimal standalone traces (~100MB image).

---

## Local Observability Stack

For monitoring build pipelines and telemetry metrics during development, an OpenTelemetry stack is provided in [`docker-compose-local.yml`](./docker-compose-local.yml):

```bash
# Start OTEL Collector, Prometheus, and Grafana
docker compose -f docker-compose-local.yml up -d

# Stop telemetry stack
docker compose -f docker-compose-local.yml down
```

- **Grafana Dashboard**: [http://localhost:3005](http://localhost:3005) (Anonymous viewer access enabled)
- **Prometheus UI**: [http://localhost:9090](http://localhost:9090)

---

## NASA Space Apps Challenge Alignment

| Judging Criteria | FireFusion Implementation |
| :--- | :--- |
| **Relevance** | Built directly on NASA FIRMS MODIS & VIIRS active fire data; addresses the real-world 2026 MODIS instrument retirement challenge. |
| **Impact** | Unlocks 25 years of continuous thermal anomaly trends for researchers, climate modelers, and disaster responders without sensor bias. |
| **Validity** | Implements transparent grid-collapsing algorithms, DBSCAN spatio-temporal clustering, and dual-observation overlap correlation verification. |
| **Creativity** | Provides an intuitive dual-series toggle, interactive calendar heatmaps, and clear "is this unusual for this place" seasonal anomaly indicators. |
| **Execution** | Fully typed Turborepo monorepo, zero type/lint errors, Next.js 16 standalone Docker builds, and complete offline capability. |

---

## License

This project is licensed under the **Apache License 2.0** in accordance with NASA Space Apps Challenge guidelines. See the [LICENSE](./LICENSE) file for details.
