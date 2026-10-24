from unittest import mock

import httplib2
import pytest
from googleapiclient.errors import HttpError

import youtube_client


def _http_error(reason):
    resp = httplib2.Response({"status": 403})
    return HttpError(resp, f'{{"error": {{"errors": [{{"reason": "{reason}"}}]}}}}'.encode())


def _youtube_raising(err):
    yt = mock.MagicMock()
    yt.search.return_value.list.return_value.execute.side_effect = err
    return yt


def test_search_quota_exceeded_propagates():
    with pytest.raises(HttpError):
        youtube_client.search_videos(_youtube_raising(_http_error("quotaExceeded")), "q", 5, "2020-01-01T00:00:00Z")


def test_search_other_http_error_returns_empty():
    assert youtube_client.search_videos(_youtube_raising(_http_error("badRequest")), "q", 5, "2020-01-01T00:00:00Z") == []


def test_auth_without_token_fails_fast_when_headless(tmp_path, monkeypatch):
    monkeypatch.setattr(youtube_client, "TOKEN_FILE", str(tmp_path / "missing.pickle"))
    monkeypatch.setattr(youtube_client.sys.stdin, "isatty", lambda: False, raising=False)
    with mock.patch.object(youtube_client.InstalledAppFlow, "from_client_secrets_file") as flow:
        with pytest.raises(RuntimeError, match="Re-authenticate"):
            youtube_client.get_authenticated_service()
        flow.assert_not_called()


def test_importing_does_not_configure_root_logging():
    # A module-level basicConfig here used to stop scheduler.py's file
    # handler from ever being installed.
    import importlib, logging
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers.clear()
    try:
        importlib.reload(youtube_client)
        assert root.handlers == []
    finally:
        root.handlers[:] = saved
