# African Intelligence Cloud — Deployment Guide

## Overview

This guide covers deploying AIC to Google Cloud from scratch. The entire process is automated except for two manual steps: Google authentication and billing activation.

Infrastructure is managed by **Terraform** and provisioned via a two-phase bootstrap script (`bootstrap.ps1` on Windows, `bootstrap.sh` on Linux/Mac).

---

## Prerequisites

Install the following tools before running the bootstrap:

| Tool | Minimum version | Install |
|------|----------------|---------|
| Google Cloud SDK (`gcloud`) | latest | https://cloud.google.com/sdk/docs/install |
| Docker Desktop | 24+ | https://docs.docker.com/get-docker/ |
| Terraform | 1.8+ | https://developer.hashicorp.com/terraform/install |

---

## Manual Steps (One-Time)

### 1. Authenticate with Google

```bash
gcloud auth login
gcloud auth application-default login
```

### 2. Enable Billing

Open the [Google Cloud Console](https://console.cloud.google.com/billing) and link a billing account to your project. The bootstrap will verify billing before proceeding.

---

## Running the Bootstrap

### Windows (PowerShell)

```powershell
.\bootstrap.ps1 -ProjectId "your-project-id" -GithubOrg "hyrin"
```

All parameters:

```powershell
.\bootstrap.ps1 `
  -ProjectId        "your-project-id" `
  -GithubOrg        "hyrin" `
  -Region           "us-central1" `
  -Environment      "production" `
  -NotificationEmail "ops@example.com" `
  -DbName           "aic_db" `
  -DbUser           "aic_user" `
  -GithubRepo       "african-intelligence-cloud"
```

### Linux / Mac (Bash)

```bash
chmod +x bootstrap.sh
./bootstrap.sh --project-id=your-project-id --github-org=hyrin
```

All parameters:

```bash
./bootstrap.sh \
  --project-id=your-project-id \
  --github-org=hyrin \
  --region=us-central1 \
  --environment=production \
  --notification-email=ops@example.com \
  --db-name=aic_db \
  --db-user=aic_user \
  --github-repo=african-intelligence-cloud
```

---

## What the Bootstrap Does

The script is fully idempotent — re-running it is safe.

### Phase 1 — Infrastructure

1. **Preflight checks** — verifies `gcloud`, `docker`, `terraform` are installed
2. **Authentication** — calls `gcloud auth application-default login`
3. **Billing check** — fails fast if billing is not enabled
4. **API enablement** — enables all 15 required GCP APIs
5. **State bucket** — creates `{PROJECT_ID}-tf-state` GCS bucket for Terraform remote state (skips if exists)
6. **Terraform Phase 1** — deploys all infrastructure using a placeholder image so Cloud Run services exist before real images are built:
   - Artifact Registry (`aic-images`)
   - Cloud SQL PostgreSQL 16 (private networking, Cloud SQL Auth Proxy)
   - Cloud Run services (`aic-backend`, `aic-frontend`) with placeholder image
   - Cloud Storage buckets (datasets, logs)
   - BigQuery dataset (`aic_analytics`)
   - Secret Manager secrets (`aic-secret-key`, `aic-database-url`) — empty placeholders
   - Service accounts and IAM roles
   - Workload Identity Federation for GitHub Actions
   - Pub/Sub topics and subscriptions
   - Cloud Scheduler jobs
   - Cloud Monitoring (uptime check, alert policy, log sink)

### Phase 2 — Application

7. **Docker build & push (backend)** — builds `./backend`, pushes to Artifact Registry
8. **Docker build & push (frontend)** — builds `./frontend` with `--build-arg NEXT_PUBLIC_API_URL=<backend_url>` baked in, pushes to Artifact Registry
9. **Terraform Phase 2** — re-applies with real image tags, updating Cloud Run services
10. **CORS update** — sets `ALLOWED_ORIGINS` on the backend to the frontend URL
11. **Secret Manager** — populates `aic-secret-key` (64-byte random hex) and `aic-database-url` (Cloud SQL socket connection string) via temp files (never via shell history)
12. **Health check** — polls `GET /health` up to 5 times with exponential backoff
13. **Prints service URLs**

---

## Infrastructure Provisioned

### Compute

| Resource | Name | Notes |
|----------|------|-------|
| Cloud Run (backend) | `aic-backend` | 0–10 instances, 1 CPU, 512 MiB |
| Cloud Run (frontend) | `aic-frontend` | 0–5 instances, 1 CPU, 512 MiB |

### Data

| Resource | Name / ID | Notes |
|----------|-----------|-------|
| Cloud SQL PostgreSQL 16 | `aic-postgres` | Private IP, Cloud SQL Auth Proxy |
| Cloud Storage (datasets) | `{PROJECT_ID}-aic-datasets` | Versioned, NEARLINE after 365 days |
| Cloud Storage (logs) | `{PROJECT_ID}-aic-logs` | COLDLINE, deleted after 90 days |
| BigQuery dataset | `aic_analytics` | US multi-region |

### Messaging & Scheduling

| Resource | Name |
|----------|------|
| Pub/Sub topic | `aic-data-sync` (7-day retention) |
| Pub/Sub topic | `aic-alerts` |
| Pub/Sub topic | `aic-dead-letter` |
| Pub/Sub subscription | `aic-data-sync-sub` (retry + dead-letter) |
| Cloud Scheduler | `aic-worldbank-daily-sync` (daily 02:00 UTC) |
| Cloud Scheduler | `aic-data-cleanup` (weekly Sunday 03:00 UTC) |

### Security & Identity

| Resource | Purpose |
|----------|---------|
| Service account: `aic-{env}-runtime` | Cloud Run identity (Secret Manager, BigQuery, GCS, Cloud SQL) |
| Service account: `aic-{env}-scheduler` | Cloud Scheduler → Cloud Run invoker |
| Service account: `github-actions-sa` | GitHub Actions CI/CD via WIF |
| Workload Identity Pool | `github-pool` |
| Secret Manager: `aic-secret-key` | FastAPI `SECRET_KEY` |
| Secret Manager: `aic-database-url` | PostgreSQL connection string |

### Observability

| Resource | Details |
|----------|---------|
| Log sink | Exports `severity>=ERROR` Cloud Run logs to GCS (COLDLINE) |
| Logging metric | `aic_http_5xx` — counts HTTP 5xx from Cloud Run |
| Uptime check | `GET /health` every 5 minutes via Cloud Monitoring |
| Alert policy | Pages on uptime failure >5 minutes (email if `notification_email` set) |

---

## Terraform Variables

Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and fill in your values. The bootstrap scripts pass variables directly via `-var` flags so a `tfvars` file is optional for scripted runs.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `project_id` | Yes | — | GCP project ID |
| `github_org` | Yes | — | GitHub org/user for WIF |
| `backend_image` | Yes | — | Set automatically by bootstrap |
| `frontend_image` | Yes | — | Set automatically by bootstrap |
| `region` | No | `us-central1` | GCP region |
| `environment` | No | `production` | `production` or `staging` |
| `db_tier` | No | `db-g1-small` | Cloud SQL tier |
| `db_name` | No | `aic_db` | Database name |
| `db_user` | No | `aic_user` | Database user |
| `github_repo` | No | `african-intelligence-cloud` | Repo name for WIF |
| `notification_email` | No | `""` | Alert email (leave empty to skip) |
| `scheduler_timezone` | No | `UTC` | IANA timezone for cron jobs |

---

## Terraform Outputs

After `terraform apply`, these outputs are available:

```bash
terraform -chdir=terraform output backend_url
terraform -chdir=terraform output frontend_url
terraform -chdir=terraform output artifact_registry_repo
terraform -chdir=terraform output db_connection_name
terraform -chdir=terraform output wif_provider
terraform -chdir=terraform output wif_service_account
# sensitive:
terraform -chdir=terraform output db_password
```

---

## GitHub Actions CI/CD Setup

After the first deployment, configure Workload Identity Federation in GitHub:

1. Get the WIF values from Terraform outputs:

```bash
WIF_PROVIDER=$(terraform -chdir=terraform output -raw wif_provider)
WIF_SA=$(terraform -chdir=terraform output -raw wif_service_account)
echo "WIF_PROVIDER : $WIF_PROVIDER"
echo "WIF_SA       : $WIF_SA"
```

2. In your GitHub repository → **Settings → Secrets and variables → Actions**, add:

| Secret name | Value |
|-------------|-------|
| `WIF_PROVIDER` | output from `wif_provider` |
| `WIF_SERVICE_ACCOUNT` | output from `wif_service_account` |
| `GCP_PROJECT_ID` | your GCP project ID |
| `GCP_REGION` | your region (e.g. `us-central1`) |

---

## Post-Deployment Verification

```bash
# Backend health
curl https://<backend_url>/health

# API docs
open https://<backend_url>/docs

# Frontend
open https://<frontend_url>
```

---

## Re-Running / Idempotency

All steps are idempotent:

- `gcloud services enable` — no-op if already enabled
- `gcloud storage buckets create` — skipped if bucket exists
- `terraform apply` — only modifies changed resources
- `docker push` — overwrites `:latest` tag
- `gcloud secrets versions add` — adds a new version (previous version remains accessible)

To update application code only (no infra changes):

```bash
# Build and push new images, then update Cloud Run
docker build -t $BACKEND_TAG ./backend && docker push $BACKEND_TAG
gcloud run services update aic-backend --image=$BACKEND_TAG --region=us-central1

docker build --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL -t $FRONTEND_TAG ./frontend
docker push $FRONTEND_TAG
gcloud run services update aic-frontend --image=$FRONTEND_TAG --region=us-central1
```

---

## Destroying Infrastructure

```bash
cd terraform
terraform destroy \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="github_org=hyrin" \
  -var="backend_image=placeholder" \
  -var="frontend_image=placeholder"
```

> **Note:** The Terraform state bucket and any Secret Manager secret versions must be deleted manually if you want a full teardown.

---

## Troubleshooting

### `billing is not enabled`
Enable billing at https://console.cloud.google.com/billing and link your project.

### `terraform init` fails with `bucket does not exist`
The state bucket was not created. Check that `gcloud storage buckets create` ran successfully, or create it manually:
```bash
gcloud storage buckets create gs://{PROJECT_ID}-tf-state --location=us-central1
```

### Cloud Run returns 503 after deploy
The container failed to start. Check logs:
```bash
gcloud run services logs read aic-backend --region=us-central1 --limit=50
```

### Secret Manager `PERMISSION_DENIED`
Ensure the runtime service account has `roles/secretmanager.secretAccessor`. Terraform grants this automatically, but IAM propagation can take up to 60 seconds after apply.

### Docker build fails for frontend
Ensure `NEXT_PUBLIC_API_URL` is set correctly. The backend must be deployed (Phase 1) before the frontend image is built.
