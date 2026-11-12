# FireFusion Backend API (`apps/api`)

FastAPI backend service for FireFusion — NASA Space Apps Challenge 2026: **Harmonization of MODIS and VIIRS Hot Spots**.

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

### Add Environment Configuration
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Ensure your NASA FIRMS `MAP_KEY` is configured in `.env`.

### Fetch Sample FIRMS Hotspot Data
```powershell
uv run python fetch_firms.py
```
This retrieves active fire detections from MODIS and VIIRS for the configured AOI and normalizes them into `data/hotspots.csv`.

### Start the API Development Server
```powershell
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
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
- **Hotspots (Filterable by bbox, date, sensor)**: [http://127.0.0.1:8000/api/v1/hotspots](http://127.0.0.1:8000/api/v1/hotspots)
- **Summary Statistics**: [http://127.0.0.1:8000/api/v1/summary](http://127.0.0.1:8000/api/v1/summary)
- **Calendar Counts**: [http://127.0.0.1:8000/api/v1/calendar](http://127.0.0.1:8000/api/v1/calendar)
- **Seasonal Anomalies**: [http://127.0.0.1:8000/api/v1/anomalies](http://127.0.0.1:8000/api/v1/anomalies)
- **CSV Downloads**:
  - Hotspots: `/api/v1/download/hotspots.csv`
  - Calendar: `/api/v1/download/calendar.csv`

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
