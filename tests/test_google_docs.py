"""Tests for Google Docs sync channel (no network required)."""

import pytest

from alchemia.channels.google_docs import (
    EXPORT_MIMES,
    GDOC_MIME,
    GSHEET_MIME,
    _sanitize_filename,
    get_status,
    list_docs,
)


def test_sanitize_filename():
    assert _sanitize_filename("hello world") == "hello world"
    assert _sanitize_filename("file:name") == "file-name"
    assert _sanitize_filename("a/b\\c") == "a-b-c"
    assert _sanitize_filename('bad"chars*here?') == "bad-chars-here-"
    assert _sanitize_filename("  leading.trailing.  ") == "leading.trailing"


def test_export_mimes_defined():
    assert GDOC_MIME in EXPORT_MIMES
    assert GSHEET_MIME in EXPORT_MIMES
    mime, ext = EXPORT_MIMES[GDOC_MIME]
    assert ext == ".md"
    assert "markdown" in mime


def test_get_status_without_deps():
    """get_status should return gracefully even if google packages aren't installed."""
    status = get_status()
    assert "installed" in status
    assert "authenticated" in status
    assert "folder_found" in status
    assert "doc_count" in status
    # If google packages aren't installed, should be False
    if not status["installed"]:
        assert not status["authenticated"]
        assert not status["folder_found"]
        assert status["doc_count"] == 0


def test_list_docs_honors_folder_name(monkeypatch: pytest.MonkeyPatch):
    class FakeFilesAPI:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def list(self, **kwargs):
            self.calls.append(kwargs)
            return self

        def execute(self):
            if len(self.calls) == 1:
                return {"files": [{"id": "folder-1", "name": "Custom Folder"}]}
            return {"files": []}

    class FakeService:
        def __init__(self) -> None:
            self.api = FakeFilesAPI()

        def files(self):
            return self.api

    service = FakeService()
    monkeypatch.setattr("alchemia.channels.google_docs._check_dependencies", lambda: True)
    monkeypatch.setattr("alchemia.channels.google_docs._build_service", lambda: service)

    list_docs(folder_name="Custom Folder")

    assert service.api.calls
    assert service.api.calls[0]["q"].startswith("name = 'Custom Folder'")
