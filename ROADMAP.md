# Product Roadmap — African Intelligence Cloud

**Current state:** Sprint 1 complete — architecture hardened, all critical security issues resolved  
**Target:** African Decision Intelligence Platform covering all 54 countries

---

## Sprint 1 — Foundation (Complete)

**Theme:** Data infrastructure, authentication, security baseline

### Backend
- [x] FastAPI application with Clean Architecture (routers → services → models)
- [x] PostgreSQL 16 schema: `organizations`, `users`, `countries`, `indicators`, `macro_data`, `audit_logs`
- [x] JWT authentication (bcrypt + HS256, 30-min expiry, HTTPBearer)
- [x] RBAC model: `SUPER_ADMIN`, `ORG_ADMIN`, `ANALYST`, `VIEWER`
- [x] World Bank API connector with background task sync
- [x] DB-driven country validation (supports all 54 African countries via seeding)
- [x] Composite index on `macro_data(country_id, indicator_id, year)`
- [x] Configurable connection pool (`db_pool_size`, `db_max_overflow`)

### Security
- [x] OWASP A01: Removed `role` from `RegisterRequest`
- [x] OWASP A05: CORS env-driven list, Docker non-root user
- [x] Background task session isolation (`_sync_with_own_session`)
- [x] `datetime.now(timezone.utc)` replacing deprecated `utcnow()`

### Testing
- [x] In-memory SQLite test database (no disk artifacts)
- [x] Fixture-scoped dependency overrides (no cross-test pollution)
- [x] `pytest-cov` for coverage reporting

### Frontend
- [x] Next.js 14 App Router + Tailwind CSS + shadcn/ui
- [x] Typed API layer: `MacroDataResponse`, `MacroDataPoint`, `Country`, `Indicator`
- [x] 401 interceptor with auto-redirect to `/login`
- [x] Recharts line chart for historical macro data
- [x] Country and indicator dropdowns

---

## Sprint 2 — Production Hardening (Next)

**Theme:** Security hardening, observability, CI/CD, rate limiting  
**Target duration:** 2 weeks

### Security (Required before production)
- [ ] `slowapi` rate limiting on `POST /auth/login` (10 req/min per IP)
- [ ] `require_role(min_role: UserRole)` FastAPI dependency
- [ ] Refresh token endpoint (`POST /auth/refresh`)
- [ ] Logout endpoint + token blacklisting (Redis or `jti` blocklist table)
- [ ] Security response headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)
- [ ] Minimum password length enforced in `RegisterRequest` schema
- [ ] Evaluate replacing `python-jose` with `PyJWT` or `authlib`

### Observability
- [ ] Wire `structlog` to application root logger (JSON structured output)
- [ ] Request correlation ID middleware (propagate `X-Request-ID` through logs)
- [ ] `AuditLog` writes on login, logout, and sync events
- [ ] Cloud Logging integration (GCP log sink)
- [ ] Basic alerting: repeated login failures, sync failures

### CI/CD
- [ ] GitHub Actions pipeline:
  - `pytest --cov=app --cov-fail-under=70` gate
  - `pip-audit` dependency vulnerability check
  - Docker build + push to Artifact Registry on `main`
  - Cloud Run deployment on tagged release
- [ ] Alembic migration workflow (automated `alembic upgrade head` on deploy)
- [ ] `.env.example` with all required environment variable names (no values)

### API Improvements
- [ ] `PATCH /users/{id}/role` endpoint (admin-only, role elevation/demotion)
- [ ] `POST /auth/logout` endpoint
- [ ] Pagination on `GET /macro-data` (cursor or offset-based)
- [ ] `POST /macro-data/sync/all` bulk sync endpoint (for Cloud Scheduler)
- [ ] OpenAPI tag groups for cleaner Swagger UI

### Frontend
- [ ] Fetch country list from `GET /api/v1/countries` (replace hardcoded `COUNTRIES` array)
- [ ] Fetch indicator list from `GET /api/v1/indicators`
- [ ] Login form validation (min length, email format)
- [ ] Toast notifications for sync success/failure
- [ ] Loading skeleton states

---

## Sprint 3 — Multi-Tenancy & AI Foundations

**Theme:** Organisation isolation, BigQuery integration, first AI features  
**Target duration:** 3 weeks

### Multi-Tenancy
- [ ] Tenant-scoped DB queries — all reads filtered by `organization_id`
- [ ] Organisation registration flow
- [ ] Admin dashboard for org management
- [ ] Penetration test against staging environment
- [ ] Data isolation audit (all endpoints verified against org boundary)

### BigQuery Integration
- [ ] Export `macro_data` to BigQuery on sync (streaming insert or scheduled export)
- [ ] BigQuery dataset per organisation (data isolation at analytics layer)
- [ ] Scheduled daily export via Cloud Scheduler → Cloud Run

### AI Foundations
- [ ] Structured `Indicator` tagging (economic domain, polarity, seasonality)
- [ ] Feature pipeline: `macro_data` → pandas DataFrame → BigQuery ML or Vertex AI
- [ ] First ML model: GDP per Capita 12-month forecast per country
- [ ] Anomaly detection on inflation and unemployment time series
- [ ] Forecast API endpoint: `GET /forecasts/{country}/{indicator}`

### Response Caching
- [ ] Redis (Cloud Memorystore) for `GET /macro-data` responses (TTL 1 hour)
- [ ] Cache invalidation on sync completion

---

## Sprint 4 — Decision Intelligence Layer

**Theme:** Natural language querying, comparative analytics, embedding search  
**Target duration:** 3 weeks

### Natural Language Interface
- [ ] RAG pipeline: World Bank data + country economic reports embedded in Vertex AI Vector Search
- [ ] `POST /intelligence/query` endpoint — natural language → structured answer
- [ ] Source citation in responses (report title, page, date)
- [ ] Conversation history per user session

### Comparative Analytics
- [ ] Regional peer comparison API (`GET /analytics/peer-compare?country=NGA&region=Sub-Saharan Africa`)
- [ ] Composite index tracker (custom weighted basket of indicators)
- [ ] Rankings: GDP growth, inflation, debt-to-GDP across 54 countries

### Frontend
- [ ] Intelligence chat panel (sidebar in dashboard)
- [ ] Peer comparison chart (multi-country overlay)
- [ ] Country scorecard PDF export

---

## Sprint 5 — Scale & Enterprise

**Theme:** Enterprise features, white-labelling, SLA  
**Target duration:** 4 weeks

### Enterprise
- [ ] SSO via SAML 2.0 / OAuth 2.0 (Google Workspace, Microsoft 365)
- [ ] Organisation-level data upload (custom indicators via CSV)
- [ ] Webhook notifications on data updates
- [ ] Audit log export (CSV/JSON for compliance)
- [ ] 99.9% uptime SLA with Cloud Run min-instances and Cloud SQL HA

### White-Label
- [ ] Per-organisation branding (logo, primary colour, domain)
- [ ] Custom indicator sets per organisation

### Data Expansion
- [ ] African Development Bank (AfDB) data connector
- [ ] IMF World Economic Outlook connector
- [ ] UN Human Development Index connector
- [ ] 54-country full data coverage validation (all indicators for all countries)

---

## Sprint 6+ — Platform Ecosystem

**Theme:** Developer platform, marketplace, mobile  
**Target duration:** Ongoing

- [ ] Public API with API key management and usage billing
- [ ] Developer documentation site (Mintlify or Docusaurus)
- [ ] Partner data connector marketplace (pluggable connector interface)
- [ ] Mobile app (React Native) — offline-capable dashboard
- [ ] Embeddable chart widgets (iframe or JS SDK) for media and think tanks
- [ ] AIC Data Lab: self-service Jupyter-style environment on Vertex AI Workbench

---

## Technical Debt Log

| Item | Priority | Sprint |
|------|----------|--------|
| No repository/data-access layer — queries in routers | Low | 3 |
| `worldbank_connector` mixes HTTP I/O and DB writes | Low | 3 |
| `COUNTRIES` dropdown hardcoded in `dashboard/page.tsx` | Medium | 2 |
| No pagination on macro data list endpoint | Medium | 2 |
| `python-jose` unmaintained — replace with `PyJWT` | Medium | 2 |
| No token blacklisting on logout | High | 2 |
| No response caching (every request hits DB) | Medium | 3 |
| Tenant data isolation not enforced at query layer | High | 3 |
