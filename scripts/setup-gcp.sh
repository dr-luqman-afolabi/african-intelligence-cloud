#!/usr/bin/env bash
# scripts/setup-gcp.sh
# One-shot GCP infrastructure provisioning for the AIC platform.
#
# Usage:
#   export PROJECT_ID=my-gcp-project
#   bash scripts/setup-gcp.sh
#
# Override any default with an env var, e.g.:
#   REGION=europe-west1 bash scripts/setup-gcp.sh

set -euo pipefail

PROJECT_ID="${PROJECT_ID:?ERROR: Set PROJECT_ID before running this script}"
REGION="${REGION:-africa-south1}"
DB_INSTANCE="${DB_INSTANCE:-aic-postgres}"
DB_NAME="${DB_NAME:-aic_db}"
DB_USER="${DB_USER:-aic_user}"
ARTIFACT_REPO="${ARTIFACT_REPO:-aic-images}"
BACKEND_SERVICE="${BACKEND_SERVICE:-aic-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-aic-frontend}"
BQ_DATASET="${BQ_DATASET:-aic_warehouse}"
GITHUB_OWNER="${GITHUB_OWNER:-dr-luqman-afolabi}"
GITHUB_REPO="${GITHUB_REPO:-african-intelligence-cloud}"

echo "============================================="
echo "  AIC Platform — GCP Infrastructure Setup"
echo "  project : $PROJECT_ID"
echo "  region  : $REGION"
echo "============================================="

gcloud config set project "$PROJECT_ID" --quiet

# ── Step 1: Enable APIs ────────────────────────────────────────────────────────
echo ""
echo "[1/8] Enabling required GCP APIs..."
gcloud services enable \
  cloudrun.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  bigquery.googleapis.com \
  bigquerystorage.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --quiet
echo "  Done."

# ── Step 2: Artifact Registry ─────────────────────────────────────────────────
echo ""
echo "[2/8] Creating Artifact Registry repository '$ARTIFACT_REPO'..."
gcloud artifacts repositories create "$ARTIFACT_REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="AIC Platform Docker images" \
  --quiet 2>/dev/null && echo "  Created." || echo "  Already exists — skipped."

# ── Step 3: Cloud SQL ──────────────────────────────────────────────────────────
echo ""
echo "[3/8] Creating Cloud SQL PostgreSQL 16 instance '$DB_INSTANCE'..."
echo "  (This can take 5-10 minutes on first creation)"
gcloud sql instances create "$DB_INSTANCE" \
  --database-version=POSTGRES_16 \
  --region="$REGION" \
  --tier=db-g1-small \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --deletion-protection \
  --quiet 2>/dev/null && echo "  Instance created." || echo "  Already exists — skipped."

echo "  Creating database '$DB_NAME'..."
gcloud sql databases create "$DB_NAME" \
  --instance="$DB_INSTANCE" \
  --quiet 2>/dev/null && echo "  Database created." || echo "  Already exists — skipped."

echo "  Creating database user '$DB_USER'..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 24)
gcloud sql users create "$DB_USER" \
  --instance="$DB_INSTANCE" \
  --password="$DB_PASSWORD" \
  --quiet 2>/dev/null && echo "  User created." || {
    echo "  User already exists — generating new password anyway..."
    gcloud sql users set-password "$DB_USER" \
      --instance="$DB_INSTANCE" \
      --password="$DB_PASSWORD" \
      --quiet
  }

DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE}"

# ── Step 4: Secret Manager ────────────────────────────────────────────────────
echo ""
echo "[4/8] Creating Secret Manager secrets..."
SECRET_KEY=$(openssl rand -base64 64 | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c 50)

# aic-database-url
if gcloud secrets describe aic-database-url --quiet 2>/dev/null; then
  echo -n "$DB_URL" | gcloud secrets versions add aic-database-url --data-file=- --quiet
  echo "  aic-database-url: new version added."
else
  echo -n "$DB_URL" | gcloud secrets create aic-database-url --data-file=- --quiet
  echo "  aic-database-url: created."
fi

# aic-secret-key
if gcloud secrets describe aic-secret-key --quiet 2>/dev/null; then
  echo -n "$SECRET_KEY" | gcloud secrets versions add aic-secret-key --data-file=- --quiet
  echo "  aic-secret-key: new version added."
else
  echo -n "$SECRET_KEY" | gcloud secrets create aic-secret-key --data-file=- --quiet
  echo "  aic-secret-key: created."
fi

# ── Step 5: BigQuery ──────────────────────────────────────────────────────────
echo ""
echo "[5/8] Creating BigQuery dataset '$BQ_DATASET'..."
bq --location="$REGION" mk \
  --dataset \
  --description="AIC Platform data warehouse" \
  "${PROJECT_ID}:${BQ_DATASET}" 2>/dev/null && echo "  Created." || echo "  Already exists — skipped."

# ── Step 6: Cloud Storage ─────────────────────────────────────────────────────
echo ""
echo "[6/8] Creating Cloud Storage bucket..."
BUCKET_NAME="${PROJECT_ID}-aic-storage"
gsutil mb -p "$PROJECT_ID" -l "$REGION" -b on "gs://${BUCKET_NAME}" 2>/dev/null \
  && echo "  Created: gs://${BUCKET_NAME}" \
  || echo "  Already exists — skipped."

# ── Step 7: IAM ───────────────────────────────────────────────────────────────
echo ""
echo "[7/8] Configuring IAM roles..."

CLOUDBUILD_SA="aic-cloudbuild-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "  Creating Cloud Build service account 'aic-cloudbuild-sa' (if not exists)..."
gcloud iam service-accounts create aic-cloudbuild-sa \
  --display-name="AIC Cloud Build Service Account" \
  --quiet 2>/dev/null && echo "  Created." || echo "  Already exists — skipped."

echo "  Granting roles to Cloud Build SA ($CLOUDBUILD_SA)..."
for ROLE in \
  roles/run.admin \
  roles/iam.serviceAccountUser \
  roles/secretmanager.secretAccessor \
  roles/artifactregistry.writer \
  roles/cloudsql.client \
  roles/bigquery.dataEditor \
  roles/storage.objectAdmin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUDBUILD_SA}" \
    --role="$ROLE" \
    --condition=None \
    --quiet > /dev/null
  echo "    + $ROLE"
done

echo "  Creating backend service account 'aic-backend-sa'..."
BACKEND_SA="aic-backend-sa@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts create aic-backend-sa \
  --display-name="AIC Backend Service Account" \
  --quiet 2>/dev/null && echo "  Created." || echo "  Already exists — skipped."

echo "  Granting roles to backend SA ($BACKEND_SA)..."
for ROLE in \
  roles/cloudsql.client \
  roles/secretmanager.secretAccessor \
  roles/bigquery.dataEditor \
  roles/bigquery.jobUser \
  roles/storage.objectAdmin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${BACKEND_SA}" \
    --role="$ROLE" \
    --condition=None \
    --quiet > /dev/null
  echo "    + $ROLE"
done

# Allow backend SA to access its own secrets
for SECRET in aic-database-url aic-secret-key; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --member="serviceAccount:${BACKEND_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet > /dev/null
done

# ── Step 8: Cloud Build trigger ────────────────────────────────────────────────
echo ""
echo "[8/8] Creating Cloud Build trigger 'aic-main-deploy'..."
gcloud builds triggers create github \
  --name="aic-main-deploy" \
  --repo-name="$GITHUB_REPO" \
  --repo-owner="$GITHUB_OWNER" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --substitutions="_REGION=${REGION},_ARTIFACT_REPO=${ARTIFACT_REPO},_BACKEND_SERVICE=${BACKEND_SERVICE},_FRONTEND_SERVICE=${FRONTEND_SERVICE},_DB_INSTANCE=${DB_INSTANCE},_BQ_DATASET=${BQ_DATASET}" \
  --quiet 2>/dev/null && echo "  Created." || echo "  Already exists — skipped."

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo "  Setup complete!"
echo "============================================="
echo ""
echo "SECRETS WRITTEN (store these securely):"
echo "  DATABASE_URL : $DB_URL"
echo "  SECRET_KEY   : $SECRET_KEY"
echo ""
echo "NEXT STEPS:"
echo "  1. Connect GitHub repo to Cloud Build:"
echo "     https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo ""
echo "  2. Push code to main to trigger first deploy:"
echo "     git push origin main"
echo ""
echo "  3. After first backend deploy, get the URL:"
echo "     gcloud run services describe $BACKEND_SERVICE --region=$REGION --format='value(status.url)'"
echo ""
echo "  4. Update _API_URL in the Cloud Build trigger substitutions:"
echo "     gcloud builds triggers update aic-main-deploy \\"
echo "       --substitutions=_API_URL=<BACKEND_URL>"
echo ""
echo "  5. Redeploy to propagate the API URL to the frontend:"
echo "     git commit --allow-empty -m 'chore: trigger redeploy for frontend API URL'"
echo "     git push origin main"
echo ""
echo "  Cloud Build console:"
echo "     https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
