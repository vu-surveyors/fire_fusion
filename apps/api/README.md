# FireFusion Backend API (`apps/api`)

FastAPI backend service and spatio-temporal harmonization engine for FireFusion — NASA Space Apps Challenge 2026: **Harmonization of MODIS and VIIRS Hot Spots**.

Managed with [**uv**](https://docs.astral.sh/uv/), the ultra-fast Python package and project manager.

---

## 1. Prerequisites

- Python 3.12+ (or let `uv` download and manage Python automatically)
- `uv` installed (`pip install uv` or `winget install astral-sh.uv`)

---

## 2. Quickstart with `uv`

Navigate to `apps/api` (or run via the monorepo root):

```powershell
cd apps/api
```

### Install / Sync Dependencies
```powershell
uv sync
```
This automatically configures the `.venv` environment and installs locked dependencies from `uv.lock`.

### Run the Harmonization Pipeline
Compute the 5-stage spatio-temporal harmonization pipeline across the bundled NASA FIRMS 2020 & 2025 datasets and populate the DuckDB database:
```powershell
uv run python -m src.compute.pipeline
# or via bun / npm:
bun run pipeline
```

### Run the Test Suite
```powershell
uv run pytest
# or via bun / npm:
bun run test
```

### Start the API Development Server
```powershell
uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
# or via bun / npm:
bun run dev
```

---

## 3. Monorepo Integration (Turborepo)

From the monorepo root (`fire_fusion-main`), Turborepo can orchestrate `apps/api` and `apps/web` together:

- **Run Dev (Frontend + API concurrently)**:
  ```powershell
  bun run dev
  # or
  turbo run dev
  ```
- **Run API only via Turborepo**:
  ```powershell
  turbo run dev --filter=api
  ```

---

## 4. API Endpoints & Documentation

- **Swagger / OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **Daily Harmonization Brief**: [http://127.0.0.1:8000/api/v1/brief?date=2025-03-25](http://127.0.0.1:8000/api/v1/brief?date=2025-03-25)
- **Clusters & Hotspots**: [http://127.0.0.1:8000/api/v1/clusters?date=2025-03-25](http://127.0.0.1:8000/api/v1/clusters?date=2025-03-25)
- **Cluster Evidence Bundle**: [http://127.0.0.1:8000/api/v1/bundle?cluster_id=CL_2025-03-25_0131](http://127.0.0.1:8000/api/v1/bundle?cluster_id=CL_2025-03-25_0131)
- **Multi-Year Calendar Matrix**: [http://127.0.0.1:8000/api/v1/calendar](http://127.0.0.1:8000/api/v1/calendar)
- **Rolling Seasonal Anomalies**: [http://127.0.0.1:8000/api/v1/anomalies](http://127.0.0.1:8000/api/v1/anomalies)
- **Cross-Sensor Validation Statistics**: [http://127.0.0.1:8000/api/v1/validation](http://127.0.0.1:8000/api/v1/validation)
- **Trigger Pipeline Recompute**: `POST /api/v1/pipeline/run`

---

## 5. Adding New Dependencies

To add Python packages to the backend using `uv`:
```powershell
uv add <package-name>
```
To add scientific or spatial computing libraries (e.g., `duckdb`, `scipy`, `geopandas`):
```powershell
uv add duckdb geopandas
```
