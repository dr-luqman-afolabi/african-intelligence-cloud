# African Intelligence Cloud — Google Cloud Deployment Guide

Sprint 2.5 "Cloud Foundation" · Production deployment on Google Cloud Run

---

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Google Cloud CLI | 470+ | https://cloud.google.com/sdk/docs/install |
| Terraform | 1.8+ | https://developer.hashicorp.com/terraform/install |
| Docker Desktop | 24+ | https://www.docker.com/products/docker-desktop |
| Git | 2.40+ | https://git-scm.com |

You need:
- A Google Cloud **Project** with billing enabled
- Owner or Editor + relevant IAM roles on that project
- A GitHub repository for the code (already set up)

---

## Step 1 — Authenticate to Google Cloud

```bash
# Log in with your account
gcloud auth login
gcloud auth application-default login

# Set the project you will deploy into
gcloud config set project YOUR_PROJECT_ID
```

Verify:
```bash
gcloud projects describe YOUR_PROJECT_ID
```

---

## Step 2 — Create the Terraform State Bucket

Terraform stores its state in GCS. Create this bucket once before any Terraform commands.

```bash
PROJECT_ID=$(gcloud config get project)
REGION=us-central1

gsutil mb -l $REGION gs://${PROJECT_ID}-tf-state
gsutil versioning set on gs://${PROJECT_ID}-tf-state
```

---

## Step 3 — Initialise Terraform

```bash
cd terraform

terraform init \
  -backend-config="bucket=${PROJECT_ID}-tf-state"
```

---

## Step 4 — Create a `terraform.tfvars` file

```hcl
# terraform/terraform.tfvars  — DO NOT COMMIT (add to .gitignore)

project_id     = "YOUR_PROJECT_ID"
region         = "us-central1"
environment    = "production"

# Placeholder images — updated in Step 8 after first push
backend_image  = "us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aic-images/backend:latest"
frontend_image = "us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aic-images/frontend:latest"

# GitHub Workload Identity
github_org     = "YOUR_GITHUB_ORG_OR_USERNAME"
github_repo    = "african-intelligence-cloud"

db_tier        = "db-g1-small"   # upgrade to db-n1-standard-2 for production load
```

Add to `.gitignore`:
```
terraform/terraform.tfvars
```

---

## Step 5 — Apply Terraform (infrastructure only)

```bash
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
```

This creates:
- Artifact Registry repository (`aic-images`)
- Cloud SQL PostgreSQL 16 instance
- GCS bucket for dataset uploads
- BigQuery dataset (`aic_analytics`)
- Secret Manager secrets (empty — you populate them in Step 6)
- Cloud Run services (backend + frontend) — they will fail to start until images exist
- Workload Identity pool + provider for GitHub Actions
- Service accounts and IAM bindings

Save the outputs — you will need them:
```bash
terraform output
```

---

## Step 6 — Populate Secret Manager

Terraform creates the secrets but not their values. You add the values manually (never in code).

### 6a — Generate a strong JWT secret key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Add it to Secret Manager:
```bash
echo -n "PASTE_SECRET_KEY_HERE" | \
  gcloud secrets versions add aic-secret-key --data-file=-
```

### 6b — Build the DATABASE_URL

Use the Cloud SQL socket connection (no IP needed from Cloud Run):

```
postgresql+psycopg2://aic_user:DB_PASSWORD@/aic_db?host=/cloudsql/CONNECTION_NAME
```

- `DB_PASSWORD` — retrieve from Terraform state:
  ```bash
  terraform output -raw db_password   # only if you added this output, otherwise check TF state
  ```
  Or reset it:
  ```bash
  gcloud sql users set-password aic_user \
    --instance=$(terraform output -raw db_connection_name | cut -d: -f3) \
    --password=NEW_STRONG_PASSWORD
  ```

- `CONNECTION_NAME` — from `terraform output db_connection_name`

```bash
echo -n "postgresql+psycopg2://aic_user:DB_PASSWORD@/aic_db?host=/cloudsql/CONNECTION_NAME" | \
  gcloud secrets versions add aic-database-url --data-file=-
```

---

## Step 7 — Configure GitHub Actions Secrets

In your GitHub repository → Settings → Secrets and variables → Actions, add:

| Secret name | Value (from `terraform output`) |
|-------------|--------------------------------|
| `WIF_PROVIDER` | `terraform output -raw wif_provider` |
| `WIF_SERVICE_ACCOUNT` | `terraform output -raw wif_service_account` |

In Variables (not Secrets — these are not sensitive):

| Variable name | Value |
|---------------|-------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `API_URL` | `terraform output -raw backend_url` |

---

## Step 8 — Build and Push the First Images

Configure Docker to push to Artifact Registry:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

Build and push backend:
```bash
REPO=$(terraform output -raw artifact_registry_repo)

docker build -t $REPO/backend:latest ./backend
docker push $REPO/backend:latest
```

Build and push frontend:
```bash
API_URL=$(terraform output -raw backend_url)

docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://$API_URL \
  -t $REPO/frontend:latest \
  ./frontend
docker push $REPO/frontend:latest
```

Update Terraform variables with the real image tags and re-apply:
```bash
# edit terraform.tfvars to set backend_image and frontend_image to the full image URLs
terraform apply
```

---

## Step 9 — Run Database Migrations

The backend uses SQLAlchemy `create_all`. It runs automatically on startup.
If you use Alembic in future, run migrations via Cloud Run Jobs:

```bash
gcloud run jobs create aic-migrate \
  --image=$REPO/backend:latest \
  --command="alembic" \
  --args="upgrade,head" \
  --region=us-central1 \
  --service-account=$(terraform output -raw service_account_email) \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},USE_SECRET_MANAGER=true"

gcloud run jobs execute aic-migrate --region=us-central1 --wait
```

---

## Step 10 — Verify the Deployment

```bash
BACKEND=$(terraform output -raw backend_url)
FRONTEND=$(terraform output -raw frontend_url)

# Health check
curl https://$BACKEND/health

# Expected response:
# {"status":"ok","version":"0.1.0","service":"African Intelligence Cloud"}

# Metrics endpoint
curl https://$BACKEND/metrics

# Frontend
open https://$FRONTEND
```

---

## Continuous Deployment (GitHub Actions)

Every push to `main` runs `.github/workflows/ci.yml`:

1. Backend Python tests (`pytest`)
2. Frontend type-check + lint + build
3. Build and push Docker images to Artifact Registry
4. Deploy backend to Cloud Run (`aic-backend`)
5. Deploy frontend to Cloud Run (`aic-frontend`)

Pull requests on `main` run CI only (no deploy).

### First-time GitHub Actions setup

The workflow uses Workload Identity Federation — no long-lived service account keys are stored in GitHub. The WIF pool was created by Terraform in Step 5 and the secrets were added in Step 7. After that, pushes to `main` deploy automatically.

---

## Cloud Build (alternative to GitHub Actions)

If you prefer GCP-native CI/CD, connect your GitHub repo in the Cloud Console and use `cloudbuild.yaml`:

```bash
# Manual trigger for testing
gcloud builds submit . \
  --config=cloudbuild.yaml \
  --substitutions=_REGION=us-central1
```

Set up an automatic trigger in the console: Cloud Build → Triggers → Connect Repository → select your repo → set branch filter to `^main$` and config file to `cloudbuild.yaml`.

---

## Environment Variables Reference

| Variable | Required | Source in production |
|----------|----------|---------------------|
| `DATABASE_URL` | Yes | Secret Manager (`aic-database-url`) |
| `SECRET_KEY` | Yes | Secret Manager (`aic-secret-key`) |
| `GCP_PROJECT_ID` | Yes | Cloud Run env var (Terraform) |
| `GCS_BUCKET_NAME` | Yes | Cloud Run env var (Terraform) |
| `BIGQUERY_DATASET` | Yes | Cloud Run env var (Terraform) |
| `STORAGE_BACKEND` | Yes | `gcs` (Terraform) |
| `USE_SECRET_MANAGER` | Yes | `true` (Terraform) |
| `APP_ENV` | Yes | `production` (Terraform) |
| `ALLOWED_ORIGINS` | No | Defaults to localhost — update for prod domain |

---

## Scaling & Cost

| Resource | Default | Notes |
|----------|---------|-------|
| Backend Cloud Run | 0–10 instances | Scales to zero when idle |
| Frontend Cloud Run | 0–5 instances | Scales to zero when idle |
| Cloud SQL | `db-g1-small` | Upgrade `db_tier` in tfvars for load |
| GCS | Pay-per-use | Lifecycle rule moves old files to Nearline after 1 year |
| BigQuery | Pay-per-query | Use `job_config` with `LIMIT` in queries |

Estimated idle cost: ~$15–25/month (Cloud SQL dominates).

---

## Secrets Rotation

To rotate the JWT secret key:

```bash
# Add new version
echo -n "NEW_SECRET_KEY" | gcloud secrets versions add aic-secret-key --data-file=-

# Cloud Run picks up the new version on next cold start
# Trigger a new revision:
gcloud run services update aic-backend \
  --region=us-central1 \
  --set-env-vars=FORCE_REDEPLOY=$(date +%s)
```

---

## Tearing Down

```bash
cd terraform
terraform destroy
```

Note: Cloud SQL has `deletion_protection = true`. To destroy it:
```bash
terraform apply -var="deletion_protection=false"  # you would need to add this variable
# or via console: Cloud SQL → instance → Edit → uncheck deletion protection
terraform destroy
```

Also delete the Terraform state bucket if you no longer need it:
```bash
gsutil rm -r gs://${PROJECT_ID}-tf-state
```

---

## Troubleshooting

**Cloud Run service fails to start**
```bash
gcloud run services logs read aic-backend --region=us-central1 --limit=50
```
Common causes: Secret Manager secret has no version yet (Step 6), wrong image tag, Cloud SQL Auth Proxy not attached.

**`Permission denied` when accessing Secret Manager**
Verify the runtime service account has `roles/secretmanager.secretAccessor`:
```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role=roles/secretmanager.secretAccessor"
```

**GitHub Actions authentication fails**
Check that `WIF_PROVIDER` and `WIF_SERVICE_ACCOUNT` secrets are set in the repository and that the Workload Identity pool attribute condition matches your `github_org/github_repo` values.

**Database connection errors**
Ensure `CLOUD_SQL_CONNECTION_NAME` in the Cloud Run service matches `terraform output db_connection_name` exactly (format: `project:region:instance`).
