resource "google_storage_bucket" "log_archive" {
  name                        = "${var.project_id}-aic-logs"
  location                    = var.region
  uniform_bucket_level_access = true
  labels                      = local.labels
  storage_class               = "COLDLINE"

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_logging_project_sink" "error_logs" {
  name        = "aic-error-log-sink"
  destination = "storage.googleapis.com/${google_storage_bucket.log_archive.name}"
  filter      = "resource.type=\"cloud_run_revision\" AND severity>=ERROR"
  project     = var.project_id

  unique_writer_identity = true
}

resource "google_storage_bucket_iam_member" "log_sink_writer" {
  bucket = google_storage_bucket.log_archive.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.error_logs.writer_identity
}

resource "google_logging_metric" "http_5xx" {
  name    = "aic_http_5xx"
  project = var.project_id
  filter  = "resource.type=\"cloud_run_revision\" AND httpRequest.status>=500"

  metric_descriptor {
    metric_kind  = "DELTA"
    value_type   = "INT64"
    unit         = "1"
    display_name = "AIC HTTP 5xx Errors"
  }

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "email" {
  count        = var.notification_email != "" ? 1 : 0
  display_name = "AIC Alerts — Email"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.notification_email
  }
}

resource "google_monitoring_uptime_check_config" "backend_health" {
  display_name = "AIC Backend — /health"
  timeout      = "10s"
  period       = "300s"
  project      = var.project_id

  http_check {
    path           = "/health"
    port           = 443
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = trimprefix(google_cloud_run_v2_service.backend.uri, "https://")
    }
  }

  depends_on = [google_cloud_run_v2_service.backend]
}

resource "google_monitoring_alert_policy" "backend_down" {
  display_name = "AIC Backend — Uptime Check Failing"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "Backend /health failing for 5 minutes"
    condition_threshold {
      filter          = "resource.type = \"uptime_url\" AND metric.type = \"monitoring.googleapis.com/uptime_check/check_passed\""
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "300s"
      aggregations {
        alignment_period     = "1200s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_TRUE"
        group_by_fields      = ["resource.label.host"]
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].name] : []

  documentation {
    content   = "AIC backend /health check is failing. Check Cloud Run service and logs."
    mime_type = "text/markdown"
  }

  depends_on = [google_monitoring_uptime_check_config.backend_health]
}
