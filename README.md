# African Intelligence Cloud (AIC)

AI-powered platform for African macrodata, microdata, dashboards, policy clinics, econometric analysis, and forecasting.

---

## Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Frontend   | Next.js 14, React, Tailwind CSS, Recharts       |
| Backend    | Python FastAPI                                  |
| Database   | PostgreSQL                                      |
| Analytics  | Pandas, NumPy, Statsmodels, Scikit-learn        |
| Cloud      | Docker, Google Cloud Run, Cloud SQL, BigQuery   |

---

## Project Structure

```
african-intelligence-cloud/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings from environment
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/              # ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API route handlers
│   │   └── services/            # Business logic + connectors
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # Reusable components
│   │   └── lib/                 # API client
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Quick Start (Local)

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Clone and configure
```bash
cd african-intelligence-cloud
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Backend  | http://localhost:8000      |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000      |
| DB       | localhost:5432             |

### 3. Run backend locally (without Docker)
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Run frontend locally
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

### Auth (Sprint 1)

| Method | Endpoint              | Auth | Description          |
|--------|-----------------------|------|----------------------|
| POST   | /api/v1/auth/register | —    | Register user        |
| POST   | /api/v1/auth/login    | —    | Login, returns JWT   |
| GET    | /api/v1/auth/profile  | JWT  | Current user profile |

### Macrodata (Sprint 1)

| Method | Endpoint                       | Auth | Description     |
|--------|--------------------------------|------|-----------------|
| GET    | /api/v1/countries              | —    | List countries  |
| GET    | /api/v1/indicators             | —    | List indicators |
| GET    | /api/v1/macro-data?country=NGA | —    | Country data    |
| GET    | /api/v1/health                 | —    | Health check    |

### DataHub — Datasets (Sprint 2)

| Method | Endpoint                        | Auth | Description                          |
|--------|---------------------------------|------|--------------------------------------|
| POST   | /api/v1/datasets/upload         | JWT  | Upload a dataset file                |
| GET    | /api/v1/datasets                | JWT  | List accessible datasets (paginated) |
| GET    | /api/v1/datasets/{id}           | JWT  | Dataset detail + profile + columns   |
| POST   | /api/v1/datasets/{id}/profile   | JWT  | Trigger background profiling job     |
| DELETE | /api/v1/datasets/{id}           | JWT  | Delete dataset (uploader only)       |

Supported upload formats: `csv`, `xlsx`, `xls`, `json`, `parquet` — up to 50 MB.

Privacy levels: `private` (owner only) · `organization` (org members) · `public` (anyone).

Dataset statuses: `uploaded` → `profiling` → `profiled` | `failed`.

---

## Frontend Routes (Sprint 2)

| Route              | Description                                        |
|--------------------|----------------------------------------------------|
| /datasets          | Dataset list with status, size, row count, tags    |
| /datasets/upload   | Drag-and-drop upload form                          |
| /datasets/[id]     | Detail page: profile summary, column stats, delete |

---

## Dataset Storage

Files are stored locally under `storage/uploads/` by default.

```
african-intelligence-cloud/
└── storage/
    └── uploads/          # local file storage (git-ignored except .gitkeep)
```

To switch to Google Cloud Storage, set `STORAGE_BACKEND=gcs` and provide `GCS_BUCKET_NAME`. The GCS backend is stubbed — it raises `NotImplementedError` until live credentials are wired.

---

## Environment Variables (Sprint 2 additions)

| Variable           | Default           | Description                        |
|--------------------|-------------------|------------------------------------|
| STORAGE_BACKEND    | `local`           | `local` or `gcs`                   |
| UPLOAD_DIR         | `storage/uploads` | Local upload directory             |
| MAX_UPLOAD_SIZE_MB | `50`              | Maximum upload size in MB          |
| GCS_BUCKET_NAME    | _(empty)_         | GCS bucket name (gcs backend only) |

Full variable reference: `backend/.env.example`

---

## Run Tests
```bash
cd backend
pytest tests/ -v
```

Sprint 2 adds 26 tests covering upload, list, detail, profiling, and delete endpoints.

---

## Project Structure (Sprint 2)

```
african-intelligence-cloud/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── dataset.py           # UploadedDataset, DatasetColumn, DatasetProfile, AnalysisJob
│   │   ├── schemas/
│   │   │   └── dataset.py           # Pydantic v2 response schemas
│   │   ├── routers/
│   │   │   └── datasets.py          # 5 dataset endpoints
│   │   └── services/
│   │       ├── storage_service.py   # Local + GCS (stub) file storage
│   │       ├── profiling_service.py # pandas-based data profiling
│   │       └── dataset_service.py   # Orchestration layer
│   └── tests/
│       └── test_datasets.py         # 26 endpoint tests
├── frontend/
│   └── src/
│       └── app/
│           └── datasets/
│               ├── page.tsx          # Dataset list
│               ├── upload/page.tsx   # Upload form with drag-and-drop
│               └── [id]/page.tsx     # Detail + profile summary + delete
└── storage/
    └── uploads/                      # Local file storage
```

---

## Sprint Roadmap

| Sprint | Focus                                                     | Status   |
|--------|-----------------------------------------------------------|----------|
| 1      | Foundation: auth, models, World Bank connector, dashboard | Complete |
| 2      | DataHub: dataset upload, storage, profiling, metadata     | Complete |
| 3      | Econometric analysis engine + forecasting API             | Planned  |
| 4      | Policy brief AI generator                                 | Planned  |
| 5      | Big data pipeline + BigQuery integration                  | Planned  |
| 6      | Multi-tenant org management + billing                     | Planned  |
| 7      | Google Cloud Run deployment + CI/CD                       | Planned  |
