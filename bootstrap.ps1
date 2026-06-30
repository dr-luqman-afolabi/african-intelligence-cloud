#Requires -Version 5.1
<#
.SYNOPSIS
  African Intelligence Cloud — two-phase bootstrap for Google Cloud deployment.

.PARAMETER ProjectId
  GCP project ID (required).

.PARAMETER GithubOrg
  GitHub organisation or user that owns this repository (required).

.PARAMETER Region
  GCP region (default: us-central1).

.PARAMETER Environment
  Deployment environment — production or staging (default: production).

.PARAMETER NotificationEmail
  Email for Cloud Monitoring alerts. Leave empty to skip (default: "").

.PARAMETER DbName
  PostgreSQL database name (default: aic_db).

.PARAMETER DbUser
  PostgreSQL user name (default: aic_user).

.PARAMETER GithubRepo
  GitHub repository name (default: african-intelligence-cloud).

.EXAMPLE
  .\bootstrap.ps1 -ProjectId my-project -GithubOrg hyrin
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ProjectId,
    [Parameter(Mandatory)][string]$GithubOrg,
    [string]$Region            = "us-central1",
    [string]$Environment       = "production",
    [string]$NotificationEmail = "",
    [string]$DbName            = "aic_db",
    [string]$DbUser            = "aic_user",
    [string]$GithubRepo        = "african-intelligence-cloud"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ── helpers ────────────────────────────────────────────────────────────────────
function Step([string]$msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function OK([string]$msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Fail([string]$msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

function Require([string]$cmd) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Fail "'$cmd' not found. Please install it and re-run."
    }
    OK "$cmd found"
}

# ── 1. preflight checks ────────────────────────────────────────────────────────
Step "Checking prerequisites"
Require "gcloud"
Require "docker"
Require "terraform"

Step "Authenticating with Google Cloud"
$adcFile = "$env:APPDATA\gcloud\application_default_credentials.json"
if (-not (Test-Path $adcFile)) {
    gcloud auth application-default login
}
gcloud config set project $ProjectId
OK "Project set to $ProjectId"

Step "Checking billing"
$billing = gcloud billing projects describe $ProjectId --format="value(billingEnabled)" 2>&1
if ($billing -ne "True") { Fail "Billing is not enabled on project '$ProjectId'. Enable it in the Cloud Console and re-run." }
OK "Billing enabled"

Step "Enabling required APIs (this may take a few minutes)"
$apis = @(
    "run.googleapis.com", "cloudbuild.googleapis.com", "secretmanager.googleapis.com",
    "sqladmin.googleapis.com", "storage.googleapis.com", "bigquery.googleapis.com",
    "artifactregistry.googleapis.com", "iam.googleapis.com", "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com", "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com", "monitoring.googleapis.com", "logging.googleapis.com",
    "cloudtrace.googleapis.com"
)
gcloud services enable @apis --project $ProjectId
OK "APIs enabled"

# ── 2. create GCS state bucket (idempotent) ────────────────────────────────────
$StateBucket = "$ProjectId-tf-state"
Step "Creating Terraform state bucket: $StateBucket"
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
gcloud storage buckets describe "gs://$StateBucket" --project=$ProjectId 2>&1 | Out-Null
$bucketExists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEap
if (-not $bucketExists) {
    gcloud storage buckets create "gs://$StateBucket" --location=$Region --project=$ProjectId
    OK "Bucket created"
} else {
    OK "Bucket already exists - skipping"
}

# ── 3. phase 1 — placeholder images ───────────────────────────────────────────
Step "Phase 1: Terraform init + plan + apply (placeholder images)"

Push-Location "$PSScriptRoot\terraform"

$PlaceholderImage = "us-docker.pkg.dev/cloudrun/container/hello"

$BootstrapVars = Join-Path (Get-Location) "_bootstrap.auto.tfvars"
@"
project_id         = "$ProjectId"
region             = "$Region"
environment        = "$Environment"
github_org         = "$GithubOrg"
github_repo        = "$GithubRepo"
backend_image      = "$PlaceholderImage"
frontend_image     = "$PlaceholderImage"
notification_email = "$NotificationEmail"
db_name            = "$DbName"
db_user            = "$DbUser"
"@ | Out-File -FilePath $BootstrapVars -Encoding utf8 -NoNewline

$initOk = $false
for ($i = 1; $i -le 3 -and -not $initOk; $i++) {
    if ($i -gt 1) { Write-Host "    Retrying terraform init (attempt $i/3)..."; Start-Sleep -Seconds 5 }
    $ErrorActionPreference = "Continue"
    terraform init -backend-config="bucket=$StateBucket" -reconfigure
    $initOk = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = "Stop"
}
if (-not $initOk) { Remove-Item $BootstrapVars -Force -ErrorAction SilentlyContinue; Fail "terraform init failed after 3 attempts" }

terraform plan -out=tfplan.phase1
if ($LASTEXITCODE -ne 0) { Remove-Item $BootstrapVars -Force -ErrorAction SilentlyContinue; Fail "terraform plan phase1 failed" }

terraform apply -auto-approve tfplan.phase1
if ($LASTEXITCODE -ne 0) { Remove-Item $BootstrapVars -Force -ErrorAction SilentlyContinue; Fail "terraform apply phase1 failed" }

Remove-Item $BootstrapVars -Force -ErrorAction SilentlyContinue

# ── 4. capture phase-1 outputs ────────────────────────────────────────────────
Step "Reading Phase 1 outputs"
$BackendUrl     = terraform output -raw backend_url
$RegistryRepo   = terraform output -raw artifact_registry_repo
$DbConnName     = terraform output -raw db_connection_name
$DbPassword     = terraform output -raw db_password   # sensitive

OK "Backend URL    : $BackendUrl"
OK "Registry repo  : $RegistryRepo"
OK "DB connection  : $DbConnName"

Pop-Location

# ── 5. populate Secret Manager (before Phase 2) ───────────────────────────────
Step "Populating Secret Manager secrets (before Phase 2)"

$TmpDir = [System.IO.Path]::GetTempPath()

$SecretKeyBytes = New-Object byte[] 64
$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
$rng.GetBytes($SecretKeyBytes)
$rng.Dispose()
$SecretKey = ($SecretKeyBytes | ForEach-Object { $_.ToString("x2") }) -join ""
$SecretKeyFile = Join-Path $TmpDir "aic_secret_key.tmp"
[System.IO.File]::WriteAllText($SecretKeyFile, $SecretKey, [System.Text.Encoding]::ASCII)

$DatabaseUrl     = "postgresql+psycopg2://${DbUser}:${DbPassword}@/${DbName}?host=/cloudsql/${DbConnName}"
$DatabaseUrlFile = Join-Path $TmpDir "aic_database_url.tmp"
[System.IO.File]::WriteAllText($DatabaseUrlFile, $DatabaseUrl, [System.Text.Encoding]::ASCII)

try {
    gcloud secrets versions add "aic-secret-key"   --data-file=$SecretKeyFile   --project=$ProjectId
    gcloud secrets versions add "aic-database-url" --data-file=$DatabaseUrlFile --project=$ProjectId
    OK "Secrets populated"
} finally {
    Remove-Item $SecretKeyFile   -Force -ErrorAction SilentlyContinue
    Remove-Item $DatabaseUrlFile -Force -ErrorAction SilentlyContinue
}

# ── 6. build & push Docker images ─────────────────────────────────────────────
Step "Authenticating Docker with Artifact Registry"
gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet

$BackendTag  = "$RegistryRepo/aic-backend:latest"
$FrontendTag = "$RegistryRepo/aic-frontend:latest"

Step "Building backend image"
docker build -t $BackendTag "$PSScriptRoot\backend"

Step "Pushing backend image"
docker push $BackendTag
OK "Backend pushed: $BackendTag"

Step "Building frontend image (NEXT_PUBLIC_API_URL=$BackendUrl)"
docker build `
    --build-arg "NEXT_PUBLIC_API_URL=$BackendUrl" `
    -t $FrontendTag `
    "$PSScriptRoot\frontend"

Step "Pushing frontend image"
docker push $FrontendTag
OK "Frontend pushed: $FrontendTag"

# ── 7. phase 2 — real images ───────────────────────────────────────────────────
Step "Phase 2: Terraform apply with real images"

Push-Location "$PSScriptRoot\terraform"

$BootstrapVars2 = Join-Path (Get-Location) "_bootstrap.auto.tfvars"
try {
    @"
project_id         = "$ProjectId"
region             = "$Region"
environment        = "$Environment"
github_org         = "$GithubOrg"
github_repo        = "$GithubRepo"
backend_image      = "$BackendTag"
frontend_image     = "$FrontendTag"
notification_email = "$NotificationEmail"
db_name            = "$DbName"
db_user            = "$DbUser"
"@ | Out-File -FilePath $BootstrapVars2 -Encoding utf8 -NoNewline

    terraform plan -out=tfplan.phase2
    if ($LASTEXITCODE -ne 0) { throw "terraform plan phase2 failed" }

    terraform apply -auto-approve tfplan.phase2
    if ($LASTEXITCODE -ne 0) { throw "terraform apply phase2 failed" }
} finally {
    Remove-Item $BootstrapVars2 -Force -ErrorAction SilentlyContinue
}

$FrontendUrl = terraform output -raw frontend_url
OK "Frontend URL: $FrontendUrl"

Pop-Location

# ── 8. update CORS origins ────────────────────────────────────────────────────
Step "Updating ALLOWED_ORIGINS on backend"
gcloud run services update "aic-backend" `
    --region=$Region `
    --update-env-vars="ALLOWED_ORIGINS=$FrontendUrl" `
    --project=$ProjectId
OK "CORS updated"

# ── 9. verify deployment ──────────────────────────────────────────────────────
Step "Verifying backend health (up to 5 attempts)"
$MaxAttempts = 5
$Attempt     = 0
$Healthy     = $false

while ($Attempt -lt $MaxAttempts -and -not $Healthy) {
    $Attempt++
    Start-Sleep -Seconds (10 * $Attempt)
    try {
        $resp = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 15
        if ($resp.StatusCode -eq 200) { $Healthy = $true; break }
    } catch { }
    Write-Host "    Attempt $Attempt/$MaxAttempts - not ready yet..."
}

if (-not $Healthy) { Fail "Backend did not respond healthy after $MaxAttempts attempts. Check Cloud Run logs." }
OK "Backend is healthy"

# ── 10. done ──────────────────────────────────────────────────────────────────
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Backend  : $BackendUrl"
Write-Host "  Frontend : $FrontendUrl"
Write-Host "============================================================`n" -ForegroundColor Green
