#!/usr/bin/env bash
# African Intelligence Cloud — two-phase bootstrap for Google Cloud deployment.
#
# Usage:
#   ./bootstrap.sh --project-id=my-project --github-org=hyrin [options]
#
# Options:
#   --project-id=VALUE        GCP project ID (required)
#   --github-org=VALUE        GitHub org or user (required)
#   --region=VALUE            GCP region (default: us-central1)
#   --environment=VALUE       production | staging (default: production)
#   --notification-email=VAL  Email for monitoring alerts (default: "")
#   --db-name=VALUE           PostgreSQL database name (default: aic_db)
#   --db-user=VALUE           PostgreSQL user name (default: aic_user)
#   --github-repo=VALUE       GitHub repo name (default: african-intelligence-cloud)

set -euo pipefail

# ── defaults ───────────────────────────────────────────────────────────────────
PROJECT_ID=""
GITHUB_ORG=""
REGION="us-central1"
ENVIRONMENT="production"
NOTIFICATION_EMAIL=""
DB_NAME="aic_db"
DB_USER="aic_user"
GITHUB_REPO="african-intelligence-cloud"

# ── parse args ────────────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --project-id=*)         PROJECT_ID="${arg#*=}" ;;
        --github-org=*)         GITHUB_ORG="${arg#*=}" ;;
        --region=*)             REGION="${arg#*=}" ;;
        --environment=*)        ENVIRONMENT="${arg#*=}" ;;
        --notification-email=*) NOTIFICATION_EMAIL="${arg#*=}" ;;
        --db-name=*)            DB_NAME="${arg#*=}" ;;
        --db-user=*)            DB_USER="${arg#*=}" ;;
        --github-repo=*)        GITHUB_REPO="${arg#*=}" ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

[ -z "$PROJECT_ID" ] && { echo "ERROR: --project-id is required" >&2; exit 1; }
[ -z "$GITHUB_ORG" ] && { echo "ERROR: --github-org is required" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_BUCKET="${PROJECT_ID}-tf-state"
PLACEHOLDER_IMAGE="us-docker.pkg.dev/cloudrun/container/hello"

# ── helpers ───────────────────────────────────────────────────────────────────
step() { echo; echo "==> $*"; }
ok()   { echo "    OK: $*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }

require() {
    command -v "$1" >/dev/null 2>&1 || fail "'$1' not found. Please install it and re-run."
    ok "$1 found"
}

# ── 1. preflight ──────────────────────────────────────────────────────────────
step "Checking prerequisites"
require gcloud
require docker
require terraform

step "Authenticating with Google Cloud"
gcloud auth application-default login --quiet
gcloud config set project "$PROJECT_ID"
ok "Project set to $PROJECT_ID"

step "Checking billing"
billing=$(gcloud beta billing projects describe "$PROJECT_ID" --format="value(billingEnabled)" 2>&1)
[ "$billing" = "True" ] || fail "Billing is not enabled on project '$PROJECT_ID'. Enable it in the Cloud Console and re-run."
ok "Billing enabled"

step "Enabling required APIs (this may take a few minutes)"
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
    cloudresourcemanager.googleapis.com \
    cloudscheduler.googleapis.com \
    pubsub.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudtrace.googleapis.com \
    --project "$PROJECT_ID"
ok "APIs enabled"

# ── 2. create GCS state bucket (idempotent) ───────────────────────────────────
step "Creating Terraform state bucket: $STATE_BUCKET"
if gcloud storage buckets list --filter="name=$STATE_BUCKET" --format="value(name)" 2>/dev/null | grep -q "$STATE_BUCKET"; then
    ok "Bucket already exists — skipping"
else
    gcloud storage buckets create "gs://$STATE_BUCKET" --location="$REGION" --project="$PROJECT_ID"
    ok "Bucket created"
fi

# ── 3. phase 1 — placeholder images ───────────────────────────────────────────
step "Phase 1: Terraform init + plan + apply (placeholder images)"

cd "$SCRIPT_DIR/terraform"

TF_COMMON_VARS=(
    -var="project_id=$PROJECT_ID"
    -var="region=$REGION"
    -var="environment=$ENVIRONMENT"
    -var="github_org=$GITHUB_ORG"
    -var="github_repo=$GITHUB_REPO"
    -var="notification_email=$NOTIFICATION_EMAIL"
    -var="db_name=$DB_NAME"
    -var="db_user=$DB_USER"
)

terraform init -backend-config="bucket=$STATE_BUCKET" -reconfigure
terraform plan \
    "${TF_COMMON_VARS[@]}" \
    -var="backend_image=$PLACEHOLDER_IMAGE" \
    -var="frontend_image=$PLACEHOLDER_IMAGE" \
    -out=tfplan.phase1
terraform apply -auto-approve tfplan.phase1

# ── 4. capture phase-1 outputs ────────────────────────────────────────────────
step "Reading Phase 1 outputs"
BACKEND_URL=$(terraform output -raw backend_url)
REGISTRY_REPO=$(terraform output -raw artifact_registry_repo)
DB_CONN_NAME=$(terraform output -raw db_connection_name)
DB_PASSWORD=$(terraform output -raw db_password)

ok "Backend URL   : $BACKEND_URL"
ok "Registry repo : $REGISTRY_REPO"
ok "DB connection : $DB_CONN_NAME"

cd "$SCRIPT_DIR"

# ── 5. populate Secret Manager (before Phase 2) ──────────────────────────────
step "Populating Secret Manager secrets (before Phase 2)"

TMP_SECRETS=$(mktemp -d)
trap 'rm -rf "$TMP_SECRETS"' EXIT

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null || \
             openssl rand -hex 64)
printf '%s' "$SECRET_KEY" > "$TMP_SECRETS/secret_key"

DATABASE_URL="postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${DB_CONN_NAME}"
printf '%s' "$DATABASE_URL" > "$TMP_SECRETS/database_url"

gcloud secrets versions add "aic-secret-key"   --data-file="$TMP_SECRETS/secret_key"   --project="$PROJECT_ID"
gcloud secrets versions add "aic-database-url" --data-file="$TMP_SECRETS/database_url" --project="$PROJECT_ID"
ok "Secrets populated"

# ── 6. build & push Docker images ─────────────────────────────────────────────
step "Authenticating Docker with Artifact Registry"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

BACKEND_TAG="${REGISTRY_REPO}/aic-backend:latest"
FRONTEND_TAG="${REGISTRY_REPO}/aic-frontend:latest"

step "Building backend image"
docker build -t "$BACKEND_TAG" "$SCRIPT_DIR/backend"

step "Pushing backend image"
docker push "$BACKEND_TAG"
ok "Backend pushed: $BACKEND_TAG"

step "Building frontend image (NEXT_PUBLIC_API_URL=$BACKEND_URL)"
docker build \
    --build-arg "NEXT_PUBLIC_API_URL=$BACKEND_URL" \
    -t "$FRONTEND_TAG" \
    "$SCRIPT_DIR/frontend"

step "Pushing frontend image"
docker push "$FRONTEND_TAG"
ok "Frontend pushed: $FRONTEND_TAG"

# ── 7. phase 2 — real images ──────────────────────────────────────────────────
step "Phase 2: Terraform apply with real images"

cd "$SCRIPT_DIR/terraform"

terraform plan \
    "${TF_COMMON_VARS[@]}" \
    -var="backend_image=$BACKEND_TAG" \
    -var="frontend_image=$FRONTEND_TAG" \
    -out=tfplan.phase2
terraform apply -auto-approve tfplan.phase2

FRONTEND_URL=$(terraform output -raw frontend_url)
ok "Frontend URL: $FRONTEND_URL"

cd "$SCRIPT_DIR"

# ── 8. update CORS origins ────────────────────────────────────────────────────
step "Updating ALLOWED_ORIGINS on backend"
gcloud run services update "aic-backend" \
    --region="$REGION" \
    --update-env-vars="ALLOWED_ORIGINS=$FRONTEND_URL" \
    --project="$PROJECT_ID"
ok "CORS updated"

# ── 9. verify deployment ──────────────────────────────────────────────────────
step "Verifying backend health (up to 5 attempts)"
MAX=5
attempt=0
healthy=false

while [ $attempt -lt $MAX ]; do
    attempt=$((attempt + 1))
    sleep $((10 * attempt))
    if curl -sf "$BACKEND_URL/health" >/dev/null 2>&1; then
        healthy=true
        break
    fi
    echo "    Attempt $attempt/$MAX — not ready yet..."
done

$healthy || fail "Backend did not respond healthy after $MAX attempts. Check Cloud Run logs."
ok "Backend is healthy"

# ── 10. done ──────────────────────────────────────────────────────────────────
echo
echo "============================================================"
echo "  Deployment complete!"
echo "============================================================"
echo "  Backend  : $BACKEND_URL"
echo "  Frontend : $FRONTEND_URL"
echo "============================================================"
echo
