# Security Analysis — African Intelligence Cloud

**Review date:** 2026-06-25  
**Framework:** OWASP Top 10 (2021)  
**Status:** Sprint 1 critical issues resolved; medium-risk items tracked for Sprint 2/3

---

## OWASP A01 — Broken Access Control

### Finding (Critical — Fixed)

`RegisterRequest` included a `role` field accepted from the JSON body:

```python
# BEFORE (vulnerable)
class RegisterRequest(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.VIEWER  # attacker could send SUPER_ADMIN
```

Any unauthenticated user could POST `{"role": "SUPER_ADMIN"}` and register as a platform administrator.

### Fix Applied

Removed `role` from `RegisterRequest`. The `auth.py` router now always assigns `UserRole.VIEWER` at registration time — the role is not user-controllable at any endpoint.

```python
# AFTER (fixed)
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
```

### Remaining Risk

- No endpoint for privileged role assignment exists yet; Sprint 2 will add an admin-only `PATCH /users/{id}/role` endpoint gated behind `SUPER_ADMIN` or `ORG_ADMIN` check.
- Data isolation between organisations (tenant-scoping on queries) is not yet enforced — Sprint 3 item.

---

## OWASP A02 — Cryptographic Failures

### Status: Acceptable

- Passwords hashed with `bcrypt` via `passlib[bcrypt]` — industry standard, salted
- JWT signed with `HS256` using a configurable `secret_key` (not hardcoded)
- `secret_key` must be loaded from Secret Manager in production — never from a committed `.env`

### Hardening Checklist (Sprint 2)

- [ ] Enforce minimum `secret_key` length (32 bytes) in `Settings` validator
- [ ] Add `HTTPS-only` cookie flag if token is ever stored in a cookie
- [ ] Set JWT `aud` and `iss` claims for additional validation

---

## OWASP A03 — Injection

### Status: Acceptable

- All DB queries use SQLAlchemy ORM with parameterised bindings — no raw SQL string concatenation
- Pydantic v2 validates all request bodies before they reach service code
- No use of `eval`, `exec`, or `subprocess` with user input

### Action Required (Sprint 2)

- [ ] Add input length limits to Pydantic schemas (e.g., `email: EmailStr`, `password: str = Field(min_length=8, max_length=128)`)

---

## OWASP A04 — Insecure Design

### Status: Partially Mitigated

- RBAC enum (`SUPER_ADMIN`, `ORG_ADMIN`, `ANALYST`, `VIEWER`) is defined but not enforced on endpoints yet
- No rate limiting on authentication endpoints — brute-force is possible

### Action Required (Sprint 2)

- [ ] Add `slowapi` rate limiter to `POST /auth/login` (e.g., 10 requests/minute per IP)
- [ ] Enforce role checks via a `require_role(min_role: UserRole)` dependency
- [ ] Account lockout after N failed login attempts

---

## OWASP A05 — Security Misconfiguration

### Finding 1: CORS Wildcard (Fixed)

```python
# BEFORE (broken — *.run.app is not valid CORS syntax)
allow_origins=["https://*.run.app", "http://localhost:3000"]

# AFTER (fixed — environment-driven list)
allow_origins=settings.allowed_origins.split(",")
```

### Finding 2: Docker Running as Root (Fixed)

```dockerfile
# BEFORE — process ran as root inside the container
CMD ["uvicorn", ...]

# AFTER — dedicated non-root user
RUN useradd -m appuser
USER appuser
CMD ["uvicorn", ...]
```

### Remaining Items (Sprint 2)

- [ ] Add `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` response headers
- [ ] Add `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] Set `WORKDIR` in Dockerfile to a directory the `appuser` owns (currently `/app` may be root-owned)
- [ ] Remove `--reload` from uvicorn CMD (not set, but verify in docker-compose)
- [ ] Disable debug endpoints and stack trace exposure in production (`ENVIRONMENT=production` guard)

---

## OWASP A06 — Vulnerable and Outdated Components

### Finding: `datetime.utcnow()` Deprecated (Fixed)

Python 3.12 deprecates `datetime.utcnow()` (returns a naive datetime that is ambiguous). All usages replaced with `datetime.now(timezone.utc)` which returns a timezone-aware datetime.

### Dependency Currency (Sprint 2)

All pinned versions as of Sprint 1:

| Package | Version | Latest Known | Risk |
|---------|---------|--------------|------|
| `fastapi` | 0.111.0 | 0.111.x | Low |
| `pydantic` | 2.7.1 | 2.7.x | Low |
| `sqlalchemy` | 2.0.30 | 2.0.x | Low |
| `python-jose` | 3.3.0 | 3.3.0 | Medium — unmaintained; consider `authlib` |
| `passlib` | 1.7.4 | 1.7.4 | Low — stable |
| `psycopg2-binary` | 2.9.9 | 2.9.x | Low |

**Action (Sprint 2):** Evaluate replacing `python-jose` with `authlib` or `PyJWT` (both actively maintained).

---

## OWASP A07 — Identification and Authentication Failures

### Status: Partially Mitigated

- JWT expiry is enforced (`access_token_expire_minutes = 30`)
- `HTTPBearer` returns 403 for missing tokens (not 422)
- 401 interceptor in frontend clears stale tokens

### Action Required (Sprint 2)

- [ ] Implement refresh token endpoint (`POST /auth/refresh`)
- [ ] Token blacklisting on logout (store JTI in Redis or DB)
- [ ] `POST /auth/logout` endpoint that invalidates the current token

---

## OWASP A08 — Software and Data Integrity Failures

### Status: No Issues Found

- No deserialization of untrusted data
- `requirements.txt` pins exact versions — supply chain risk is low
- Docker base image is `python:3.12-slim` (official image)

### Hardening (Sprint 2)

- [ ] Add `pip hash` verification or use `pip-audit` in CI to detect known vulnerabilities in dependencies

---

## OWASP A09 — Security Logging and Monitoring Failures

### Finding: Background Task DB Session Bug (Fixed)

The original background task for World Bank sync received a request-scoped `db` session. After the HTTP response was sent the session closed, causing the background task to operate on a closed connection and fail silently.

**Fix:** `_sync_with_own_session()` creates its own `SessionLocal()`, commits, and closes it independently of the request lifecycle.

### Remaining Items

- [ ] `AuditLog` writes are modelled but not yet wired to login/logout events
- [ ] No alerting on repeated authentication failures
- [ ] `structlog` added to `requirements.txt` — wire it up in Sprint 2 (`structlog.configure(...)` in `main.py`)

---

## OWASP A10 — Server-Side Request Forgery (SSRF)

### Status: No Issues Found

- The only outbound HTTP call is `worldbank_connector.py` → `https://api.worldbank.org`
- The target URL is hardcoded in the service layer, not user-controllable
- No URL parameters from user input are forwarded to external services

---

## Hardening Checklist Summary

### Sprint 1 — Completed

- [x] Removed self-elevation via `RegisterRequest.role` (A01)
- [x] bcrypt password hashing + parameterised queries (A02, A03)
- [x] CORS wildcard replaced with env-driven list (A05)
- [x] Docker non-root user added (A05)
- [x] `datetime.now(timezone.utc)` replacing `utcnow()` (A06)
- [x] JWT expiry + HTTPBearer 403 on missing token (A07)
- [x] Background task session isolation (A09)
- [x] Typed exception handling in `worldbank_connector` (A09)

### Sprint 2 — Required Before Production

- [ ] `slowapi` rate limiting on `/auth/login`
- [ ] Role enforcement dependency (`require_role`)
- [ ] Security response headers middleware
- [ ] Refresh token + logout endpoint
- [ ] Minimum password length enforced in schema
- [ ] `pip-audit` in CI pipeline
- [ ] `structlog` wired to application root logger
- [ ] Evaluate replacing `python-jose`

### Sprint 3 — Pre-Multi-Tenant Launch

- [ ] Tenant-scoped queries (all data reads filtered by `organization_id`)
- [ ] Audit log writes on authentication events
- [ ] Alerting on N failed logins per IP/user
- [ ] Penetration test against staging environment
