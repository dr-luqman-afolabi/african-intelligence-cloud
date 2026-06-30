terraform {
  required_version = ">= 1.8"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state stored in GCS — bucket must exist before first `terraform init`
  # Create it manually once: gsutil mb -l us-central1 gs://<project-id>-tf-state
  backend "gcs" {
    bucket = ""       # override: -backend-config="bucket=<project-id>-tf-state"
    prefix = "aic/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
