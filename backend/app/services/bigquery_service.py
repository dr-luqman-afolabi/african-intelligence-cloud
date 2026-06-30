from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import bigquery
        from app.config import get_settings
        s = get_settings()
        _client = bigquery.Client(project=s.gcp_project_id)
    return _client


def ensure_dataset(dataset_id: str, location: str = "US") -> None:
    """Create the BigQuery dataset if it does not already exist."""
    from google.cloud import bigquery
    client = _get_client()
    try:
        client.get_dataset(client.dataset(dataset_id))
        logger.info("BigQuery dataset exists", extra={"dataset": dataset_id})
    except Exception:
        ds = bigquery.Dataset(client.dataset(dataset_id))
        ds.location = location
        client.create_dataset(ds)
        logger.info("Created BigQuery dataset", extra={"dataset": dataset_id})


def insert_rows(dataset_id: str, table_id: str, rows: list[dict[str, Any]]) -> list[dict]:
    """Stream rows into a BigQuery table. Returns insert errors (empty = success)."""
    client = _get_client()
    table_ref = f"{client.project}.{dataset_id}.{table_id}"
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        logger.error("BigQuery insert errors", extra={"table": table_ref, "errors": errors})
    else:
        logger.info("Inserted rows into BigQuery", extra={"table": table_ref, "count": len(rows)})
    return errors


def run_query(sql: str, job_config: Any = None) -> list[dict[str, Any]]:
    """Run a SQL query and return results as a list of row dicts."""
    client = _get_client()
    query_job = client.query(sql, job_config=job_config)
    rows = [dict(row) for row in query_job.result()]
    logger.info("BigQuery query complete", extra={"rows": len(rows)})
    return rows


def load_dataframe(dataset_id: str, table_id: str, df: Any) -> None:
    """Load a pandas DataFrame into a BigQuery table (full replace)."""
    from google.cloud import bigquery
    client = _get_client()
    table_ref = f"{client.project}.{dataset_id}.{table_id}"
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    logger.info("Loaded DataFrame to BigQuery", extra={"table": table_ref, "rows": len(df)})
