from app.jobs import data_refresh


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_refresh_succeeds_when_at_least_one_connector_updates(monkeypatch, capsys):
    session = FakeSession()
    monkeypatch.setattr(data_refresh, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        data_refresh,
        "run_all_incremental",
        lambda db: [
            {"source_id": "world-bank", "status": "ok", "records_fetched": 12},
            {"source_id": "manual", "status": "no_connector", "records_fetched": 0},
        ],
    )

    assert data_refresh.main() == 0
    assert session.closed is True
    output = capsys.readouterr().out
    assert '"sources_succeeded": 1' in output
    assert '"records_fetched": 12' in output


def test_refresh_fails_when_no_connector_succeeds(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(data_refresh, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        data_refresh,
        "run_all_incremental",
        lambda db: [
            {"source_id": "world-bank", "status": "error", "message": "timeout"},
            {"source_id": "manual", "status": "no_connector"},
        ],
    )

    assert data_refresh.main() == 1
    assert session.closed is True


def test_refresh_fails_cleanly_when_orchestration_crashes(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(data_refresh, "SessionLocal", lambda: session)

    def fail(_db):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(data_refresh, "run_all_incremental", fail)

    assert data_refresh.main() == 1
    assert session.closed is True
