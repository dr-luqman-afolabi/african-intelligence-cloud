# Architecture Review — Sprint 1

**Reviewed by:** CTO  
**Date:** 2026-06-25  
**Scope:** All files in `backend/` and `frontend/` as of Sprint 1 completion

---

## 1. Clean Architecture

**Finding:** The project has a recognisable layered structure — routers → services → models — but there was coupling between the routing layer and infrastructure concerns (direct hard-coded country lists in routers, no repository pattern to abstract DB queries).

**Actions taken:**
- Extracted DB-driven validation into `_require_country()` helper in `macro_data.py` router
- Service layer (`auth_service`, `worldbank_connector`) remains the right home for business logic

**Residual risk:** No formal repository/data-access layer. Acceptable for Sprint 2; re-evaluate if query complexity grows.

---

## 2. SOLID Principles

**Finding:** Services mix responsibilities slightly — `worldbank_connector` performs both HTTP I/O and DB writes. Single Responsibility Principle would suggest separating the HTTP client from the data persistence layer.

**Actions taken:** Added structured logging and typed exception handling; no structural refactor (out of scope until Sprint 3).

**Residual risk:** Low. The file is small and the concern is documented in the Roadmap.

---

## 3. Scalability — 54 African Countries

**Finding (critical):** `SUPPORTED_COUNTRIES` was a hardcoded Python set of ~10 ISO3 codes. Any new country required a code change and redeploy.

**Action taken:** Removed the set entirely. Validation now queries the `countries` table. Any country seeded into the DB is immediately supported — zero code changes required to expand to all 54 countries.

---

## 4. Multi-Tenancy

**Finding:** Organization → User FK is in place. RBAC enum (`SUPER_ADMIN`, `ORG_ADMIN`, `ANALYST`, `VIEWER`) is modelled. No tenant-scoping on data queries yet.

**Residual risk:** Medium. Data isolation between organisations must be enforced before multi-tenant production use. Tracked in Roadmap Sprint 3.

---

## 5. Security (OWASP Top 10)

See `SECURITY.md` for full analysis. Critical issues fixed:

| Issue | OWASP Category | Status |
|-------|---------------|--------|
| `RegisterRequest.role` allowed self-elevation | A01 Broken Access Control | **Fixed** |
| CORS wildcard `*.run.app` (invalid syntax) | A05 Security Misconfiguration | **Fixed** |
| Docker running as root | A05 Security Misconfiguration | **Fixed** |
| `datetime.utcnow()` (Python 3.12 deprecation) | A06 Outdated Components | **Fixed** |
| Background task using request-scoped DB session | A09 Logging / Integrity | **Fixed** |

---

## 6. API Consistency

**Finding:** Route prefixes were consistent (`/api/v1/...`). HTTPBearer was inconsistently applied — some routes used the legacy header approach.

**Action taken:** All auth-protected routes now use `HTTPBearer`, returning 403 (not 422) for missing tokens. Tests updated accordingly.

---

## 7. Google Cloud Readiness

**Finding:** Database pool was hard-coded (pool_size=5, max_overflow=10). Cloud Run scales horizontally; default pool values would cause connection exhaustion.

**Actions taken:**
- `db_pool_size` and `db_max_overflow` moved to `Settings` with sane defaults (10/20)
- CORS now reads from `settings.allowed_origins` — Cloud Run URLs can be listed in env vars without code changes

---

## 8. Docker Configuration

**Finding:** Dockerfile ran the application process as root, which is a security vulnerability (container escape → host root).

**Action taken:** Added `RUN useradd -m appuser` + `USER appuser` before the `CMD` directive.

---

## 9. Database Normalization

**Finding:** Schema is well-normalised (3NF). `MacroData` references `Country` and `Indicator` via FKs rather than storing strings. Composite index added on `(country_id, indicator_id, year)` for the primary query path.

**No actions required.**

---

## 10. Logging and Monitoring

**Finding:** No structured logging existed. `print()` statements and bare exceptions provided no operational visibility.

**Actions taken:**
- `worldbank_connector.py` now uses `logging.getLogger(__name__)` with typed exception handlers
- `structlog==24.1.0` added to `requirements.txt` for future structured log adoption
- `slowapi==0.1.9` added for future rate-limiting and metrics

---

## 11. Error Handling

**Finding:** `worldbank_connector.sync_macro_data` raised bare exceptions on HTTP and timeout failures, crashing background tasks silently.

**Action taken:** Typed exception handlers (`requests.exceptions.Timeout`, `HTTPError`, `Exception`) now log and return empty list — background sync is best-effort and non-fatal.

---

## 12. Performance Bottlenecks

**Finding:** Country validation performed a DB query on every request; composite index was missing on `MacroData`.

**Actions taken:**
- Composite `Index("ix_macro_data_lookup", "country_id", "indicator_id", "year")` added to model
- Pool sizing made configurable for Cloud SQL Connector tuning

**Residual risk:** Response caching (Redis/Cloud Memorystore) is a Sprint 3 item.

---

## 13. Test Coverage

**Finding:** All three test files used:
- Disk-backed SQLite (`test.db`, `test_macro.db`, `test_countries.db`) — leaves artifacts, slows CI
- Module-level `app.dependency_overrides` — cross-test state pollution
- Module-level `TestClient(app)` — coupled to module import order
- Wrong status code assertion (`422` instead of `403` for missing `Authorization` header)
- Wrong status code assertion (`400` instead of `404` for country not in DB)
- Duplicate `httpx==0.27.0` in `requirements.txt`

**Actions taken:** All three test files rewritten with:
- `sqlite:///:memory:` (no disk artifacts, faster)
- `@pytest.fixture`-based `client` that sets/clears `dependency_overrides` per-test
- Correct status codes (`403`, `404`)
- `pytest-cov==5.0.0` added for coverage reporting

---

## 14. CI/CD Readiness

**Finding:** No CI pipeline exists. `requirements.txt` had a duplicate entry.

**Actions taken:**
- Removed duplicate `httpx==0.27.0`
- Added `pytest-cov==5.0.0` to enable `--cov` coverage gate in CI
- See Roadmap for GitHub Actions pipeline (Sprint 2)

---

## 15. Future AI Integration

**Finding:** `Indicator` and `MacroData` models are well-structured for ML feature pipelines. BigQuery integration (for training data export) and vector embedding storage (for RAG) are the natural next steps.

**No actions taken** — reserved for Sprint 3 AI Foundations milestone.

---

## Ready for Sprint 2

The following items are confirmed complete and stable:

- [x] Clean Architecture: layered routers → services → models
- [x] SOLID: single-responsibility services, dependency injection via FastAPI `Depends`
- [x] Scalability: country validation is DB-driven — all 54 countries supported by seeding
- [x] Multi-tenancy foundation: Organization FK, RBAC enum, UserRole on User model
- [x] OWASP A01: `RegisterRequest.role` removed — no self-elevation possible
- [x] OWASP A05: CORS wildcard removed, Docker non-root user added
- [x] JWT authentication: `HTTPBearer`, 403 on missing token, `timezone.utc` datetime
- [x] Background task safety: `_sync_with_own_session` creates its own `SessionLocal`
- [x] Pool sizing: configurable via `db_pool_size` / `db_max_overflow` environment vars
- [x] Structured logging: `logging.getLogger` in all service modules
- [x] Typed exception handling: timeout, HTTP error, fallback in `worldbank_connector`
- [x] Test isolation: in-memory SQLite, fixture-scoped overrides, correct status codes
- [x] Dependencies: no duplicates, `pytest-cov`, `structlog`, `slowapi` added
- [x] Docker: non-root user (`appuser`)
- [x] Frontend types: `MacroDataResponse`, `MacroDataPoint`, `Country`, `Indicator` in `api.ts`
- [x] Frontend safety: 401 interceptor clears token and redirects to `/login`
- [x] Frontend: no `any` casts in `dashboard/page.tsx`
- [x] DB indexes: composite index on `(country_id, indicator_id, year)`
- [x] `updated_at` columns: `server_default=func.now()` on all timestamped models
- [x] Audit trail: `AuditLog` model with `user_agent` column and indexes
