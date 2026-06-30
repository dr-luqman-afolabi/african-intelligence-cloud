# Architecture — African Intelligence Cloud

## Overview

African Intelligence Cloud (AIC) is a multi-tenant SaaS platform surfacing macroeconomic data for all 54 African countries. It is designed to run on Google Cloud Platform with Cloud Run for compute, Cloud SQL (PostgreSQL 16) for OLTP storage, and BigQuery for analytics and future AI workloads.

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Tier                          │
│  Next.js 14 (App Router)  ·  Tailwind CSS  ·  shadcn/ui    │
│  Recharts  ·  Axios with 401 interceptor                    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / JSON
┌────────────────────────────▼────────────────────────────────┐
│                       API Tier (Cloud Run)                   │
│  FastAPI 0.111  ·  Uvicorn  ·  Python 3.12                  │
│                                                             │
│  /api/v1/auth        →  auth_service                        │
│  /api/v1/macro-data  →  worldbank_connector                 │
│  /api/v1/countries   →  Country model                       │
│  /api/v1/indicators  →  Indicator model                     │
└──────────┬──────────────────────────┬───────────────────────┘
           │ SQLAlchemy 2.0           │ requests / HTTP
┌──────────▼──────────┐   ┌──────────▼──────────────────────┐
│  Database Tier       │   │    External Data Source         │
│  Cloud SQL           │   │    World Bank API               │
│  PostgreSQL 16       │   │    (sync via BackgroundTasks)   │
│                      │   └─────────────────────────────────┘
│  organizations       │
│  users               │
│  countries           │
│  indicators          │
│  macro_data          │
│  audit_logs          │
└──────────────────────┘
```

---

## Data Flow

### User Registration
1. `POST /auth/register` → `auth_service.register_user()`
2. Password hashed with bcrypt (passlib)
3. User inserted with role `VIEWER` by default
4. `UserProfile` returned (no token on register — explicit login required)

### Authentication
1. `POST /auth/login` → `auth_service.authenticate_user()`
2. bcrypt verify → `create_access_token()` → JWT (HS256, 30-min expiry)
3. Client stores token in `localStorage` as `aic_token`
4. All subsequent requests: `Authorization: Bearer <token>` via Axios interceptor

### Macro Data Request
1. `GET /macro-data?country=NGA`
2. Validate ISO3 against `countries` table (`_require_country`)
3. Query `macro_data JOIN indicator WHERE country_id = ? ORDER BY year`
4. Return `MacroDataResponse` with typed `MacroDataPoint[]`

### Background Sync
1. `POST /macro-data/sync/{iso3}`
2. `BackgroundTasks.add_task(_sync_with_own_session, iso3)`
3. `_sync_with_own_session` creates own `SessionLocal()` — independent of request lifecycle
4. `worldbank_connector.sync_macro_data()` fetches World Bank API → upserts `MacroData` rows

---

## Database Schema

```sql
organizations
  id          UUID PK
  name        VARCHAR NOT NULL
  slug        VARCHAR UNIQUE NOT NULL
  country     VARCHAR(3)
  created_at  TIMESTAMPTZ DEFAULT now()

users
  id              UUID PK
  organization_id UUID FK → organizations
  email           VARCHAR UNIQUE NOT NULL
  full_name       VARCHAR NOT NULL
  hashed_password VARCHAR NOT NULL
  role            ENUM(SUPER_ADMIN, ORG_ADMIN, ANALYST, VIEWER) DEFAULT VIEWER
  is_active       BOOLEAN DEFAULT true
  created_at      TIMESTAMPTZ DEFAULT now()
  updated_at      TIMESTAMPTZ DEFAULT now()

countries
  id        UUID PK
  iso3      CHAR(3) UNIQUE NOT NULL
  iso2      CHAR(2) NOT NULL
  name      VARCHAR NOT NULL
  region    VARCHAR NOT NULL
  is_active BOOLEAN DEFAULT true

indicators
  id          UUID PK
  code        VARCHAR UNIQUE NOT NULL   -- World Bank indicator code
  name        VARCHAR NOT NULL
  unit        VARCHAR NOT NULL
  category    VARCHAR NOT NULL

macro_data
  id            UUID PK
  country_id    UUID FK → countries
  indicator_id  UUID FK → indicators
  year          INTEGER NOT NULL
  value         NUMERIC(20,6)
  data_source   VARCHAR DEFAULT 'world_bank'
  created_at    TIMESTAMPTZ DEFAULT now()
  updated_at    TIMESTAMPTZ DEFAULT now()
  UNIQUE (country_id, indicator_id, year)
  INDEX ix_macro_data_lookup (country_id, indicator_id, year)

audit_logs
  id          UUID PK
  user_id     UUID FK → users (nullable)
  action      VARCHAR NOT NULL
  resource    VARCHAR
  ip_address  VARCHAR
  user_agent  VARCHAR
  created_at  TIMESTAMPTZ DEFAULT now()
  INDEX ix_audit_logs_user_id (user_id)
  INDEX ix_audit_logs_created_at (created_at)
```

---

## GCP Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Artifact Registry                                      │
│  docker push africa-intelligence-cloud/api:v1.x.x       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Cloud Build (CI/CD)                                    │
│  build → test → push → deploy                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Cloud Run (API)                                        │
│  Min instances: 1  ·  Max instances: 10                 │
│  Memory: 512Mi  ·  CPU: 1                               │
│  Concurrency: 80                                        │
│  Env vars from Secret Manager                           │
└────┬───────────────────────────────────────┬────────────┘
     │ Cloud SQL Auth Proxy (sidecar)        │
┌────▼────────────────────┐  ┌──────────────▼───────────┐
│  Cloud SQL              │  │  Cloud Scheduler         │
│  PostgreSQL 16          │  │  Daily sync trigger       │
│  private IP             │  │  → Cloud Run /sync/all   │
│  automated backups      │  └──────────────────────────┘
└─────────────────────────┘
```

### Secret Manager Secrets

| Secret Name | Content |
|-------------|---------|
| `aic-database-url` | `postgresql://...` connection string |
| `aic-secret-key` | JWT signing key |
| `aic-allowed-origins` | Comma-separated CORS origins |

---

## Frontend Architecture

```
frontend/
  src/
    app/              # Next.js App Router pages
      dashboard/      # Macro data visualisation
      login/          # JWT authentication
    components/
      MacroChart/     # Recharts line chart wrapper
    lib/
      api.ts          # Axios instance + typed interfaces + interceptors
```

Key design decisions:
- `MacroDataResponse`, `MacroDataPoint`, `Country`, `Indicator` interfaces defined in `api.ts` — single source of truth for API contract
- 401 interceptor clears `aic_token` and redirects to `/login` — no stale token leakage
- `COUNTRIES` list in `dashboard/page.tsx` is a UI convenience; actual validation lives server-side

---

## Configuration Model

All runtime configuration flows through `app/config.py` via `pydantic_settings.BaseSettings` + `lru_cache`. No environment variables are read ad-hoc in application code.

| Setting | Default | Notes |
|---------|---------|-------|
| `database_url` | — | Required; loaded from Secret Manager in GCP |
| `secret_key` | — | Required; JWT signing key |
| `db_pool_size` | 10 | Cloud SQL connections per instance |
| `db_max_overflow` | 20 | Burst headroom |
| `allowed_origins` | `http://localhost:3000` | Comma-separated; overridden in GCP |
| `access_token_expire_minutes` | 30 | JWT TTL |
