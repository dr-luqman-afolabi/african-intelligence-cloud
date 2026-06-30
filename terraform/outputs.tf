output "backend_url" {
  description = "Public URL of the AIC backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Public URL of the AIC frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "db_connection_name" {
  description = "Cloud SQL connection name used by the backend service"
  value       = google_sql_database_instance.postgres.connection_name
}

output "gcs_bucket_name" {
  description = "GCS bucket name for dataset uploads"
  value       = google_storage_bucket.datasets.name
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for analytics"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "service_account_email" {
  description = "Email of the runtime service account used by Cloud Run"
  value       = google_service_account.aic_runtime.email
}

output "artifact_registry_repo" {
  description = "Artifact Registry repository for Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "wif_provider" {
  description = "Workload Identity Federation provider (use as WIF_PROVIDER secret in GitHub)"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "wif_service_account" {
  description = "Service account email for GitHub Actions (use as WIF_SERVICE_ACCOUNT secret in GitHub)"
  value       = google_service_account.github_actions.email
}

output "db_password" {
  description = "Cloud SQL PostgreSQL password (populate aic-database-url secret in Secret Manager)"
  value       = random_password.db_password.result
  sensitive   = true
}

