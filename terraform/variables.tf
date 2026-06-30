variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Primary GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (production / staging)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging"], var.environment)
    error_message = "environment must be 'production' or 'staging'."
  }
}

variable "backend_image" {
  description = "Full Artifact Registry image URL for the backend (including tag)"
  type        = string
  # example: us-central1-docker.pkg.dev/my-project/aic-images/backend:latest
}

variable "frontend_image" {
  description = "Full Artifact Registry image URL for the frontend (including tag)"
  type        = string
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-g1-small"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "aic_db"
}

variable "db_user" {
  description = "PostgreSQL user name"
  type        = string
  default     = "aic_user"
}

variable "github_org" {
  description = "GitHub organization or user name (used for Workload Identity pool)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (e.g. african-intelligence-cloud)"
  type        = string
  default     = "african-intelligence-cloud"
}

variable "notification_email" {
  description = "Email address for monitoring alert notifications. Leave empty to skip."
  type        = string
  default     = ""
}

variable "scheduler_timezone" {
  description = "IANA timezone for Cloud Scheduler jobs (e.g. UTC, Africa/Lagos)."
  type        = string
  default     = "UTC"
}
