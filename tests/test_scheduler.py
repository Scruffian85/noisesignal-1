import os
import time

import pandas as pd

import scheduler


def _executor(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scheduler, "EMAIL_ENABLED", False)
    monkeypatch.setattr(scheduler, "LOG_FILE", str(tmp_path / "logs" / "test.log"))
    return scheduler.ScheduledExecutor()


def test_stale_results_csv_is_not_reported(monkeypatch, tmp_path):
    ex = _executor(monkeypatch, tmp_path)
    pd.DataFrame([{"video_id": "v1", "title": "old"}]).to_csv("emerging_playlist_results.csv", index=False)
    week_ago = time.time() - 7 * 86400
    os.utime("emerging_playlist_results.csv", (week_ago, week_ago))
    summary = ex.get_execution_summary()
    assert summary["tracks_count"] == 0


def test_fresh_results_csv_is_reported(monkeypatch, tmp_path):
    ex = _executor(monkeypatch, tmp_path)
    (tmp_path / "playlist_id.txt").write_text("PL123\n")
    pd.DataFrame([{"video_id": "v1", "title": "new"}]).to_csv("emerging_playlist_results.csv", index=False)
    summary = ex.get_execution_summary()
    assert summary["tracks_count"] == 1
    assert summary["playlist_url"].endswith("list=PL123")


def test_retries_then_gives_up(monkeypatch, tmp_path):
    ex = _executor(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(scheduler.main_module, "main", lambda: calls.append(1) or (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(scheduler, "RETRY_DELAY", 0)
    assert ex.execute_with_retries() is False
    assert len(calls) == scheduler.MAX_RETRIES
