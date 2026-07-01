# Codex Deployment Fix Plan

This branch documents the deployment fixes required after commit `ac9e4aa`.

## Problem

The deployment failed because the Cloud Build setup was not fully aligned with Google Cloud IAM and the HYRIN organization policy.

The known issues are:

1. The setup script creates `aic-cloudbuild-sa`, but the Cloud Build trigger does not explicitly use that service account.
2. The Cloud Run deploy steps use public unauthenticated access, which conflicts with the HYRIN organization policy that blocks `allUsers` access.
3. The frontend build still uses a placeholder backend API URL unless the trigger substitution is manually updated.
4. The setup script does not fail early with a clear explanation when the active Google account lacks permissions to enable APIs.

## Required code fixes

### 1. Cloud Build trigger

In `scripts/setup-gcp.sh`, update the `gcloud builds triggers create github` command to include the dedicated Cloud Build service account:

```bash
--service-account="projects/${PROJECT_ID}/serviceAccounts/aic-cloudbuild-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 2. Remove public Cloud Run deployment flags

In `cloudbuild.yaml`, remove `--allow-unauthenticated` from both backend and frontend Cloud Run deploy steps.

Public exposure should be handled later through Cloud Run domain mapping, HTTPS load balancer, or Identity-Aware Proxy.

### 3. Resolve backend URL dynamically

In `cloudbuild.yaml`, deploy the backend first, then resolve the backend service URL with:

```bash
gcloud run services describe ${_BACKEND_SERVICE} --region=${_REGION} --format='value(status.url)'
```

Use that resolved URL as `NEXT_PUBLIC_API_URL` when building the frontend image.

### 4. Add preflight IAM check

In `scripts/setup-gcp.sh`, add a preflight check before enabling APIs:

```bash
if ! gcloud services list --enabled --project "$PROJECT_ID" >/dev/null 2>&1; then
  echo "ERROR: The active Google account cannot manage services for project $PROJECT_ID."
  echo "Grant the account Project Owner or Service Usage Admin temporarily, then rerun this script."
  exit 1
fi
```

### 5. Validate after fix

Run:

```bash
export PROJECT_ID=african-intelligence-cloud
gcloud config set project "$PROJECT_ID"
gcloud services enable serviceusage.googleapis.com cloudrun.googleapis.com cloudbuild.googleapis.com
bash scripts/setup-gcp.sh
git push origin main
```

## Notes

Keep Cloud Run private by default because HYRIN organization policy blocks public `allUsers` access. Configure `aic.hyrin.org` and `api.hyrin.org` later using managed HTTPS and an approved access model.
