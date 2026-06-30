data "google_project" "current" {
  project_id = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "data_sync" {
  name    = "aic-data-sync"
  project = var.project_id
  labels  = local.labels

  message_retention_duration = "604800s"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "alerts" {
  name    = "aic-alerts"
  project = var.project_id
  labels  = local.labels

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "dead_letter" {
  name    = "aic-dead-letter"
  project = var.project_id
  labels  = local.labels

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_subscription" "data_sync_sub" {
  name    = "aic-data-sync-sub"
  topic   = google_pubsub_topic.data_sync.name
  project = var.project_id

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

# Runtime SA: publish to data-sync topic, subscribe to data-sync subscription
resource "google_pubsub_topic_iam_member" "runtime_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.data_sync.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.aic_runtime.email}"
}

resource "google_pubsub_subscription_iam_member" "runtime_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.data_sync_sub.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.aic_runtime.email}"
}

# Pub/Sub service agent: required for dead-letter delivery
resource "google_pubsub_topic_iam_member" "pubsub_sa_dead_letter_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.dead_letter.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription_iam_member" "pubsub_sa_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.data_sync_sub.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}
