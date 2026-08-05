"""Run a bounded, auditable refresh across automated data connectors."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from app.database import SessionLocal
from app.services.incremental_sync_service import run_all_incremental

logger = logging.getLogger(__name__)


def main() -> int:
    started_at = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        results = run_all_incremental(db)
    except Exception:
        logger.exception("Automated data refresh could not start")
        return 1
    finally:
        db.close()

    succeeded = [item for item in results if item.get("status") == "ok"]
    failed = [item for item in results if item.get("status") == "error"]
    skipped = [item for item in results if item.get("status") == "no_connector"]
    records = sum(int(item.get("records_fetched") or 0) for item in succeeded)
    written = sum(int(item.get("records_written") or 0) for item in succeeded)

    summary = {
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "sources_succeeded": len(succeeded),
        "sources_failed": len(failed),
        "sources_skipped": len(skipped),
        "records_fetched": records,
        "records_written": written,
        "failures": [
            {"source_id": item.get("source_id"), "message": item.get("message")}
            for item in failed
        ],
    }
    print(json.dumps(summary, sort_keys=True))

    if not succeeded:
        logger.error("Automated data refresh produced no successful source updates")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
