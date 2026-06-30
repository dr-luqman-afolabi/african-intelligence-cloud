locals {
  name_prefix = "aic-${var.environment}"
  labels = {
    project     = "african-intelligence-cloud"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# ── Enable required GCP APIs ─────────────────────────────────────────────────
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
  ])
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}

# ── Service account ───────────────────────────────────────────────────────────
resource "google_service_account" "aic_runtime" {
  account_id   = "${local.name_prefix}-runtime"
  display_name = "AIC Runtime Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "aic_runtime_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/storage.objectAdmin",
    "roles/cloudsql.client",
    "roles/monitoring.metricWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.aic_runtime.email}"
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "aic-images"
  format        = "DOCKER"
  labels        = local.labels
  depends_on    = [google_project_service.apis]
}

# ── Cloud SQL (PostgreSQL 16) ─────────────────────────────────────────────────
resource "google_sql_database_instance" "postgres" {
  name             = "${local.name_prefix}-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = var.db_tier
    ip_configuration {
      ipv4_enabled = true
      # Cloud Run connects via Cloud SQL Auth Proxy (unix socket); IAM controls access
    }
    backup_configuration {
      enabled = true
      start_time = "03:00"
    }
    insights_config {
      query_insights_enabled = true
    }
  }

  deletion_protection = true
  depends_on          = [google_project_service.apis]
}

resource "google_sql_database" "aic" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "aic" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# ── GCS bucket for dataset uploads ───────────────────────────────────────────
resource "google_storage_bucket" "datasets" {
  name                        = "${var.project_id}-aic-datasets"
  location                    = var.region
  uniform_bucket_level_access = true
  labels                      = local.labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# ── BigQuery dataset ─────────────────────────────────────────────────────────
resource "google_bigquery_dataset" "analytics" {
  dataset_id  = "aic_analytics"
  location    = "US"
  labels      = local.labels
  description = "AIC analytics data (macro indicators, user events)"
  depends_on  = [google_project_service.apis]
}

# ── Secret Manager ────────────────────────────────────────────────────────────
resource "google_secret_manager_secret" "secret_key" {
  secret_id = "aic-secret-key"
  labels    = local.labels
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "aic-database-url"
  labels    = local.labels
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

# ── Cloud Run: backend ────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = "aic-backend"
  location = var.region
  labels   = local.labels

  template {
    service_account = google_service_account.aic_runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.datasets.name
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = google_bigquery_dataset.analytics.dataset_id
      }
      env {
        name  = "STORAGE_BACKEND"
        value = "gcs"
      }
      env {
        name  = "USE_SECRET_MANAGER"
        value = "true"
      }
      env {
        name  = "CLOUD_SQL_CONNECTION_NAME"
        value = google_sql_database_instance.postgres.connection_name
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql+psycopg2://placeholder@/placeholder"
      }
      env {
        name  = "SECRET_KEY"
        value = "placeholder-override-via-secret-manager"
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 15
        period_seconds        = 30
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_project_iam_member.aic_runtime_roles,
  ]
}

# allUsers IAM blocked by hyrin.org domain-restricted sharing org policy.
# Public access requires org policy exemption or Cloud Load Balancer in front.
# resource "google_cloud_run_v2_service_iam_member" "backend_public" { ... }

# ── Cloud Run: frontend ───────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "frontend" {
  name     = "aic-frontend"
  location = var.region
  labels   = local.labels

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = var.frontend_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# allUsers IAM blocked by hyrin.org domain-restricted sharing org policy.
# Public access requires org policy exemption or Cloud Load Balancer in front.
# resource "google_cloud_run_v2_service_iam_member" "frontend_public" { ... }

# ── Workload Identity Federation for GitHub Actions ───────────────────────────
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  depends_on                = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_org}/${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_actions" {
  account_id   = "${local.name_prefix}-ci"
  display_name = "AIC GitHub Actions Service Account"
  project      = var.project_id
}

resource "google_service_account_iam_member" "github_wif" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_org}/${var.github_repo}"
}

resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/run.developer",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountTokenCreator",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
