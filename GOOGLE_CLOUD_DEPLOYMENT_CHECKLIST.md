# Google Cloud Deployment Checklist — African Intelligence Cloud

> **Scope:** First-time deployment only. All commands assume `gcloud` is authenticated and the correct project is active.
> Replace `{PROJECT_ID}` with your GCP project ID throughout. Replace `{REGION}` with `us-central1` unless changed.

---

## A. Google Cloud Resources to Create Manually

These resources cannot be created by Terraform itself (state bucket) or require a one-time manual step before Terraform runs.

### A1. Terraform State Bucket (MUST exist before `terraform init`)

```bash
gcloud storage buckets create gs://{PROJECT_ID}-tf-state \
  --location=US \
  --uniform-bucket-level-access

gcloud storage buckets update gs://{PROJECT_ID}-tf-state \
  --versioning
```

> **Why manual:** Terraform's GCS backend (`terraform/versions.tf`) stores its own state in this bucket. Terraform cannot create the bucket it needs to exist before it can run.

### A2. Artifact Registry Repository (created by Terraform, but verify)

Terraform creates `aic-images` (DOCKER format) in `{REGION}`. If you need to create it manually:

```bash
gcloud artifacts repositories create aic-images \
  --repository-format=docker \
  --location={REGION} \
  --description="AIC Docker images"
```

### A3. All Other Resources (Terraform-managed)

The following are created by `terraform apply` — do NOT create manually:
- Cloud SQL instance (`aic-production-db`)
- Cloud SQL database (`aic_db`) and user (`aic_user`)
- GCS dataset bucket (`{PROJECT_ID}-aic-datasets`)
- BigQuery dataset (`aic_analytics`)
- Secret Manager secrets (shells only — values set in Section C)
- Cloud Run services (`aic-backend`, `aic-frontend`)
- Service accounts (`aic-production-runtime`, `aic-production-ci`)
- Workload Identity Pool and Provider

---

## B. APIs to Enable

All 10 APIs are enabled by Terraform (`terraform/main.tf`). If you need to enable them manually first (e.g., to run Terraform itself):

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com
```

> **Note:** `cloudresourcemanager.googleapis.com` must usually be enabled before you can enable the others via the API.

---

## C. Secret Manager Variables to Create

Terraform creates the Secret Manager secret **shells** (empty containers) but does NOT populate the values. You must add the secret versions manually after `terraform apply`.

### C1. Retrieve the database password from Terraform state

```bash
cd terraform/
terraform show -json | jq -r '.values.root_module.resources[] | select(.type=="google_sql_user" and .name=="aic") | .values.password'
```

If the above fails (state not local), reset the password:

```bash
gcloud sql users set-password aic_user \
  --instance=aic-production-db \
  --password=$(openssl rand -base64 32)
```

Store this password — you will need it for the DATABASE_URL below.

### C2. Populate `aic-database-url`

Format (Unix socket — Cloud SQL private IP only):

```
postgresql+psycopg2://aic_user:{DB_PASSWORD}@/aic_db?host=/cloudsql/{PROJECT_ID}:{REGION}:aic-production-db
```

```bash
echo -n "postgresql+psycopg2://aic_user:{DB_PASSWORD}@/aic_db?host=/cloudsql/{PROJECT_ID}:{REGION}:aic-production-db" | \
  gcloud secrets versions add aic-database-url --data-file=-
```

> **Critical:** Use the socket path format, not TCP. Cloud SQL is configured with `ipv4_enabled=false` (private IP only).

### C3. Populate `aic-secret-key`

Generate a secure random key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets versions add aic-secret-key --data-file=-
```

### C4. Verify both secrets are populated

```bash
gcloud secrets versions list aic-database-url
gcloud secrets versions list aic-secret-key
```

Both must show at least one version with state `ENABLED`.

---

## D. Storage Bucket Names

| Purpose | Bucket Name | Created By |
|---------|-------------|------------|
| Dataset uploads | `{PROJECT_ID}-aic-datasets` | Terraform |
| Terraform state | `{PROJECT_ID}-tf-state` | Manual (Section A1) |

**Dataset bucket configuration (set by Terraform):**
- Versioning: enabled
- Lifecycle: objects move to NEARLINE storage class after 365 days
- Uniform bucket-level access: enabled

**Environment variable required in Cloud Run backend:**
- `GCS_BUCKET_NAME={PROJECT_ID}-aic-datasets`
- `STORAGE_BACKEND=gcs`

---

## E. BigQuery Dataset Names

| Dataset ID | Location | Created By |
|------------|----------|------------|
| `aic_analytics` | `US` (multi-region) | Terraform |

> **Note:** Location is hardcoded to `"US"` in `terraform/main.tf` (not region-variable). All BigQuery data will reside in the US multi-region.

**Environment variable required in Cloud Run backend:**
- `BIGQUERY_DATASET=aic_analytics`

---

## F. Cloud SQL Setup

### F1. Instance details

| Field | Value |
|-------|-------|
| Instance name | `aic-production-db` |
| Database version | PostgreSQL 16 |
| Tier | `db-g1-small` |
| Region | `us-central1` |
| IP | Private IP only (`ipv4_enabled=false`) |
| Database name | `aic_db` |
| Database user | `aic_user` |
| Backups | Daily at 03:00 |
| Deletion protection | Enabled (must disable before `terraform destroy`) |
| Connection name format | `{PROJECT_ID}:{REGION}:aic-production-db` |

### F2. Connection method

Cloud Run connects via Cloud SQL Auth Proxy (Unix socket volume mount). The socket is mounted at `/cloudsql/{CONNECTION_NAME}`. The DATABASE_URL must use:

```
?host=/cloudsql/{PROJECT_ID}:{REGION}:aic-production-db
```

**Do NOT use a TCP host or port in the DATABASE_URL.**

### F3. Schema initialisation

Schema is created automatically on first startup via SQLAlchemy (`Base.metadata.create_all`). Seed data (countries, indicators) is also inserted on startup. No manual migration step required for initial deployment.

### F4. Verify Cloud SQL is reachable from Cloud Run

```bash
gcloud run services describe aic-backend --region={REGION} --format=json | \
  jq '.spec.template.metadata.annotations["run.googleapis.com/cloudsql-instances"]'
```

Should return `"{PROJECT_ID}:{REGION}:aic-production-db"`.

---

## G. Service Account Permissions

### G1. Runtime service account — `aic-production-runtime@{PROJECT_ID}.iam.gserviceaccount.com`

Used by Cloud Run services at runtime.

| Role | Purpose |
|------|---------|
| `roles/secretmanager.secretAccessor` | Read `aic-secret-key` and `aic-database-url` |
| `roles/bigquery.dataEditor` | Write analytics data |
| `roles/bigquery.jobUser` | Run BigQuery jobs |
| `roles/storage.objectAdmin` | Read/write GCS dataset bucket |
| `roles/cloudsql.client` | Connect to Cloud SQL via Auth Proxy |

All roles are granted by Terraform. Verify:

```bash
gcloud projects get-iam-policy {PROJECT_ID} \
  --flatten="bindings[].members" \
  --format="table(bindings.role,bindings.members)" \
  --filter="bindings.members:aic-production-runtime"
```

### G2. CI/CD service account — `aic-production-ci@{PROJECT_ID}.iam.gserviceaccount.com`

Used by GitHub Actions via Workload Identity Federation (no long-lived keys).

| Role | Purpose |
|------|---------|
| `roles/run.developer` | Deploy to Cloud Run |
| `roles/artifactregistry.writer` | Push Docker images |
| `roles/iam.serviceAccountTokenCreator` | Impersonate runtime SA during deploy |

### G3. Workload Identity Federation (GitHub Actions)

| Field | Value |
|-------|-------|
| Pool | `github-pool` |
| Provider | `github-provider` |
| Condition | `repo:{github_org}/african-intelligence-cloud:*` |

After `terraform apply`, set GitHub repository secrets and variables:

```bash
# Get the WIF provider resource name
terraform output wif_provider

# Get the CI service account email
terraform output wif_service_account
```

Then in your GitHub repository:
- **Secret** `WIF_PROVIDER` = value of `terraform output wif_provider`
- **Secret** `WIF_SERVICE_ACCOUNT` = value of `terraform output wif_service_account`
- **Variable** `GCP_PROJECT_ID` = `{PROJECT_ID}`
- **Variable** `API_URL` = backend Cloud Run URL (from `terraform output backend_url`)

---

## H. Cloud Run Deployment Commands

### H1. Manual deploy (after images are pushed to Artifact Registry)

**Backend:**

```bash
gcloud run deploy aic-backend \
  --image={REGION}-docker.pkg.dev/{PROJECT_ID}/aic-images/backend:latest \
  --region={REGION} \
  --service-account=aic-production-runtime@{PROJECT_ID}.iam.gserviceaccount.com \
  --add-cloudsql-instances={PROJECT_ID}:{REGION}:aic-production-db \
  --set-env-vars="APP_ENV=production,GCP_PROJECT_ID={PROJECT_ID},GCS_BUCKET_NAME={PROJECT_ID}-aic-datasets,BIGQUERY_DATASET=aic_analytics,STORAGE_BACKEND=gcs,USE_SECRET_MANAGER=true,CLOUD_SQL_CONNECTION_NAME={PROJECT_ID}:{REGION}:aic-production-db" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --allow-unauthenticated
```

**Frontend:**

```bash
gcloud run deploy aic-frontend \
  --image={REGION}-docker.pkg.dev/{PROJECT_ID}/aic-images/frontend:latest \
  --region={REGION} \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://aic-backend-{HASH}-uc.a.run.app" \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1 \
  --allow-unauthenticated
```

> **Note:** Replace `aic-backend-{HASH}-uc.a.run.app` with the actual backend URL from `terraform output backend_url` or `gcloud run services describe aic-backend --format="value(status.url)"`.

### H2. Update `_API_URL` in cloudbuild.yaml

The `cloudbuild.yaml` substitution `_API_URL` is a placeholder. After the first backend deploy, update it:

```yaml
# cloudbuild.yaml — update this line with actual URL
substitutions:
  _API_URL: https://aic-backend-ACTUAL-HASH-uc.a.run.app  # replace this
```

### H3. Update `ALLOWED_ORIGINS` for production

`backend/app/config.py` defaults `ALLOWED_ORIGINS` to `"http://localhost:3000"`. Add the production frontend URL to the Cloud Run backend environment:

```bash
gcloud run services update aic-backend \
  --region={REGION} \
  --update-env-vars="ALLOWED_ORIGINS=https://{FRONTEND_URL}"
```

---

## I. Cloud Build Command

### I1. Trigger a manual Cloud Build run

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION={REGION},_ARTIFACT_REPO=aic-images,_API_URL=https://aic-backend-{HASH}-uc.a.run.app \
  .
```

### I2. Cloud Build pipeline steps

| Step | Description |
|------|-------------|
| 1 | Run pytest (SQLite in-memory — no Cloud SQL needed) |
| 2 | Build backend Docker image |
| 3 | Push backend image tagged with `$SHORT_SHA` and `latest` |
| 4 | Build frontend Docker image (injects `NEXT_PUBLIC_API_URL`) |
| 5 | Push frontend image |
| 6 | Deploy backend to Cloud Run |
| 7 | Deploy frontend to Cloud Run |

### I3. GitHub Actions CI/CD (automated on push to `main`)

Push to `main` → GitHub Actions runs:
1. `backend-ci`: ruff lint + mypy + pytest
2. `frontend-ci`: type-check + lint + Next.js build
3. `deploy` (only if both CI jobs pass): builds + pushes both images + deploys to Cloud Run

Required GitHub Secrets: `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`
Required GitHub Variables: `GCP_PROJECT_ID`, `API_URL`

---

## J. How to Test Deployment

### J1. Health check — backend

```bash
BACKEND_URL=$(gcloud run services describe aic-backend --region={REGION} --format="value(status.url)")
curl -s "$BACKEND_URL/health" | jq .
```

Expected response:
```json
{"status": "ok", "version": "0.1.0", "service": "African Intelligence Cloud"}
```

### J2. Health check — frontend

```bash
FRONTEND_URL=$(gcloud run services describe aic-frontend --region={REGION} --format="value(status.url)")
curl -o /dev/null -s -w "%{http_code}\n" "$FRONTEND_URL"
```

Expected: `200`

### J3. API endpoint tests

```bash
# List data sources (connector registry)
curl -s "$BACKEND_URL/api/v1/sources" | jq '.total'

# List countries (seeded on startup)
curl -s "$BACKEND_URL/api/v1/countries" | jq '.[0].iso3'

# Metrics endpoint
curl -s "$BACKEND_URL/metrics"
```

### J4. Secret Manager integration test

```bash
# Check backend logs for secret bootstrap
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aic-backend AND textPayload:\"secret\"" \
  --limit=10 \
  --format="value(textPayload)"
```

No `WARNING` lines about `aic-secret-key` or `aic-database-url` = secrets loaded successfully.

### J5. Database connectivity test

```bash
# Check that startup seeding ran (countries and indicators are present)
curl -s "$BACKEND_URL/api/v1/countries" | jq 'length'
```

Expected: `6` (Nigeria, Rwanda, South Africa, Ghana, Kenya, Ethiopia)

### J6. GCS connectivity test

```bash
# Upload a test file via the API, then verify it appears in GCS
gcloud storage ls gs://{PROJECT_ID}-aic-datasets/
```

### J7. BigQuery connectivity test

```bash
bq ls --project_id={PROJECT_ID} aic_analytics
```

### J8. Cloud Build logs

```bash
gcloud builds list --limit=5
gcloud builds log {BUILD_ID}
```

---

## K. Common Errors and Fixes

### K1. `Error: failed to create backend: Failed to get existing workspaces`

**Symptom:** `terraform init` fails.
**Cause:** Terraform state bucket does not exist yet.
**Fix:** Create the bucket manually (Section A1), then re-run `terraform init -backend-config="bucket={PROJECT_ID}-tf-state"`.

---

### K2. `DEADLINE_EXCEEDED` or `could not connect to Cloud SQL`

**Symptom:** Backend Cloud Run service crashes or returns 500 on startup.
**Cause:** DATABASE_URL uses TCP (`localhost:5432`) instead of Unix socket.
**Fix:** Ensure DATABASE_URL uses socket path format:
```
postgresql+psycopg2://aic_user:{PW}@/aic_db?host=/cloudsql/{PROJECT_ID}:{REGION}:aic-production-db
```
Verify `aic-database-url` secret matches this format exactly (no TCP port, no IP address).

---

### K3. `SECRET_NOT_FOUND` or backend exits with `RuntimeError: GCP_PROJECT_ID must be set`

**Symptom:** Container starts then immediately exits; logs show secret bootstrap failure.
**Causes (check in order):**
1. `GCP_PROJECT_ID` env var not set on the Cloud Run service.
2. Secret value not added (only the shell was created by Terraform — populate per Section C).
3. Runtime service account missing `roles/secretmanager.secretAccessor`.

**Fix:**
```bash
# Check env var
gcloud run services describe aic-backend --region={REGION} | grep GCP_PROJECT_ID

# Check secret version exists
gcloud secrets versions list aic-database-url

# Grant role if missing
gcloud projects add-iam-policy-binding {PROJECT_ID} \
  --member="serviceAccount:aic-production-runtime@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### K4. `CORS error` in browser — frontend cannot reach backend

**Symptom:** Browser console shows `Access-Control-Allow-Origin` error.
**Cause:** `ALLOWED_ORIGINS` env var on backend defaults to `http://localhost:3000`.
**Fix:** Update the backend Cloud Run service (see Section H3):
```bash
gcloud run services update aic-backend \
  --region={REGION} \
  --update-env-vars="ALLOWED_ORIGINS=https://{FRONTEND_CLOUD_RUN_URL}"
```

---

### K5. Frontend returns `500` — `Cannot find module '../server.js'`

**Symptom:** Frontend Cloud Run container crashes immediately.
**Cause:** Next.js `output: 'standalone'` not set in `next.config.js`. The frontend Dockerfile copies `.next/standalone/` which only exists in standalone mode.
**Fix:** Verify `frontend/next.config.js` contains `output: 'standalone'`. Rebuild and redeploy.

---

### K6. `PERMISSION_DENIED: The caller does not have permission` — GitHub Actions deploy fails

**Symptom:** GitHub Actions `deploy` job fails when pushing images or deploying Cloud Run.
**Cause:** WIF provider or service account not configured correctly, or Terraform hasn't been applied yet.
**Fix:**
```bash
# Verify WIF is set up
terraform output wif_provider
terraform output wif_service_account

# Confirm GitHub secrets match exactly (no trailing whitespace/newline)
gh secret list  # requires gh CLI

# Re-grant roles if Terraform hasn't run
gcloud projects add-iam-policy-binding {PROJECT_ID} \
  --member="serviceAccount:aic-production-ci@{PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.developer"
```

---

### K7. `db_password` not available — cannot construct DATABASE_URL

**Symptom:** After `terraform apply`, the generated database password is not shown.
**Cause:** `terraform/main.tf` uses `random_password` resource but has no `terraform output` for `db_password` (intentional — avoids exposing it).
**Fix (preferred):** Retrieve from Terraform state (state is stored in GCS, access-controlled):
```bash
terraform show -json | jq -r '.values.root_module.resources[] | select(.type=="google_sql_user") | .values.password'
```

**Fix (alternative):** Reset the password and use the new value:
```bash
NEW_PW=$(openssl rand -base64 32)
gcloud sql users set-password aic_user \
  --instance=aic-production-db \
  --password="$NEW_PW"
echo "New password: $NEW_PW"
# Then populate the secret (Section C2) with this password
```

---

### K8. Cloud Build step 1 fails — pytest cannot import app modules

**Symptom:** `ModuleNotFoundError` in Cloud Build pytest step.
**Cause:** `PYTHONPATH` not set or `requirements.txt` out of date.
**Fix:** Cloud Build step 1 runs in `python:3.12-slim` with `DATABASE_URL=sqlite:///./test.db`. It installs from `backend/requirements.txt`. Ensure all app dependencies are listed there (not just in `pyproject.toml`).

---

### K9. `deletion_protection = true` blocks `terraform destroy`

**Symptom:** `terraform destroy` fails on Cloud SQL instance.
**Cause:** `terraform/main.tf` sets `deletion_protection=true` on the Cloud SQL instance.
**Fix (only when intentionally destroying the database):**
```bash
# Temporarily disable in Terraform state
terraform state show google_sql_database_instance.main
# Edit main.tf: set deletion_protection = false
terraform apply -target=google_sql_database_instance.main
terraform destroy
```

---

## Deployment Order Summary

```
1. Create Terraform state bucket manually (Section A1)
2. Enable APIs (Section B)  ← or let Terraform do it
3. terraform init -backend-config="bucket={PROJECT_ID}-tf-state"
4. terraform plan -var="project_id={PROJECT_ID}" -var="backend_image=..." -var="frontend_image=..." -var="github_org={YOUR_ORG}"
5. terraform apply
6. Populate secrets in Secret Manager (Section C)
7. Set GitHub Secrets + Variables (Section G3)
8. Push to main branch → GitHub Actions deploys automatically (Section I3)
   — OR — run Cloud Build manually (Section I1)
9. Run health checks (Section J)
```
