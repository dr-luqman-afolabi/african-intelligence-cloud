#!/usr/bin/env bash
# One-shot setup for GitHub Actions -> Google Cloud deploys via Workload
# Identity Federation (keyless; no downloaded service-account keys).
#
# Prereq: gcloud auth login   (as an owner/editor of the project)
# Run:    bash scripts/setup_github_deploy_wif.sh
#
# Idempotent: safe to re-run; each resource is created only if missing.
# When it finishes it prints the two values to paste into GitHub:
#   Settings -> Secrets and variables -> Actions -> New repository secret
#     WIF_PROVIDER
#     WIF_SERVICE_ACCOUNT
set -euo pipefail

PROJECT_ID="african-intelligence-cloud"
GITHUB_REPO="dr-luqman-afolabi/african-intelligence-cloud"
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
SA_NAME="github-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo ">> Using project: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}" --quiet
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")

echo ">> Enabling required APIs"
gcloud services enable iamcredentials.googleapis.com iam.googleapis.com \
  run.googleapis.com artifactregistry.googleapis.com --quiet

echo ">> Workload identity pool"
if ! gcloud iam workload-identity-pools describe "${POOL_ID}" --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${POOL_ID}" \
    --location=global --display-name="GitHub Actions"
fi

echo ">> Workload identity provider (restricted to ${GITHUB_REPO})"
if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --location=global --workload-identity-pool="${POOL_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
    --location=global \
    --workload-identity-pool="${POOL_ID}" \
    --display-name="GitHub OIDC" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition="assertion.repository == '${GITHUB_REPO}'"
fi

echo ">> Deploy service account"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" --display-name="GitHub Actions deployer"
fi

echo ">> Granting deploy roles to ${SA_EMAIL}"
# run.admin: deploy Cloud Run revisions; artifactregistry.writer: push images.
# iam.serviceAccountUser is required to deploy services that run *as* another
# service account (aic-backend-sa) — granted project-wide for simplicity;
# narrow to the individual runtime service accounts if you prefer.
for role in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="${role}" \
    --condition=None --quiet >/dev/null
done

echo ">> Allowing the GitHub repo to impersonate ${SA_EMAIL}"
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_REPO}" \
  --quiet >/dev/null

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

echo
echo "============================================================"
echo "DONE. Add these two repository secrets on GitHub:"
echo "https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo
echo "  WIF_PROVIDER        = ${WIF_PROVIDER}"
echo "  WIF_SERVICE_ACCOUNT = ${SA_EMAIL}"
echo "============================================================"
echo "Then re-run the failed deploy from the Actions tab, or push any commit."
