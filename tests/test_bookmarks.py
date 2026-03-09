"""Tests for channels/bookmarks.py — Safari and Chrome bookmark parsing."""

import json
import plistlib

from alchemia.channels.bookmarks import (
    parse_chrome_bookmarks,
    parse_safari_bookmarks,
    sync_bookmarks,
)


def test_parse_safari_missing_file(monkeypatch, tmp_path):
    import alchemia.channels.bookmarks as mod

    monkeypatch.setattr(mod, "SAFARI_BOOKMARKS", tmp_path / "nonexistent.plist")
    assert parse_safari_bookmarks() == []


def test_parse_safari_with_inspirations(monkeypatch, tmp_path):
    import subprocess

    import alchemia.channels.bookmarks as mod

    # Build a plist tree with an Inspirations folder containing 2 bookmarks
    plist_data = {
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeList",
                "Title": "Inspirations",
                "Children": [
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URLString": "https://example.com/a",
                        "URIDictionary": {"title": "Bookmark A"},
                    },
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URLString": "https://example.com/b",
                        "URIDictionary": {"title": "Bookmark B"},
                    },
                ],
            },
        ],
    }
    xml_bytes = plistlib.dumps(plist_data, fmt=plistlib.FMT_XML)

    # Make the file "exist"
    fake_plist = tmp_path / "Bookmarks.plist"
    fake_plist.write_bytes(b"fake")
    monkeypatch.setattr(mod, "SAFARI_BOOKMARKS", fake_plist)

    # Mock subprocess.run to return the XML plist
    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=xml_bytes, stderr=b"")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = parse_safari_bookmarks()
    assert len(result) == 2
    assert all(r["source"] == "safari" for r in result)
    assert result[0]["url"] == "https://example.com/a"


def test_parse_safari_no_inspirations(monkeypatch, tmp_path):
    import subprocess

    import alchemia.channels.bookmarks as mod

    plist_data = {
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeList",
                "Title": "OtherFolder",
                "Children": [
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URLString": "https://example.com/c",
                        "URIDictionary": {"title": "Not Inspiration"},
                    },
                ],
            },
        ],
    }
    xml_bytes = plistlib.dumps(plist_data, fmt=plistlib.FMT_XML)

    fake_plist = tmp_path / "Bookmarks.plist"
    fake_plist.write_bytes(b"fake")
    monkeypatch.setattr(mod, "SAFARI_BOOKMARKS", fake_plist)

    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=xml_bytes, stderr=b"")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = parse_safari_bookmarks()
    assert result == []


def test_parse_chrome_missing_file(monkeypatch, tmp_path):
    import alchemia.channels.bookmarks as mod

    monkeypatch.setattr(mod, "CHROME_BOOKMARKS", tmp_path / "nonexistent")
    assert parse_chrome_bookmarks() == []


def test_parse_chrome_with_inspirations(tmp_path, monkeypatch):
    import alchemia.channels.bookmarks as mod

    chrome_data = {
        "roots": {
            "bookmark_bar": {
                "name": "Bookmarks Bar",
                "type": "folder",
                "children": [
                    {
                        "name": "Inspirations",
                        "type": "folder",
                        "children": [
                            {
                                "name": "Cool Site",
                                "type": "url",
                                "url": "https://cool.example.com",
                            },
                        ],
                    },
                ],
            },
        },
    }
    chrome_file = tmp_path / "Bookmarks"
    chrome_file.write_text(json.dumps(chrome_data))
    monkeypatch.setattr(mod, "CHROME_BOOKMARKS", chrome_file)

    result = parse_chrome_bookmarks()
    assert len(result) == 1
    assert result[0]["source"] == "chrome"
    assert result[0]["url"] == "https://cool.example.com"


def test_parse_chrome_invalid_json(tmp_path, monkeypatch):
    import alchemia.channels.bookmarks as mod

    bad_file = tmp_path / "Bookmarks"
    bad_file.write_text("{not valid json")
    monkeypatch.setattr(mod, "CHROME_BOOKMARKS", bad_file)

    assert parse_chrome_bookmarks() == []


def test_sync_bookmarks_combines_sources(monkeypatch):
    import alchemia.channels.bookmarks as mod

    monkeypatch.setattr(
        mod,
        "parse_safari_bookmarks",
        lambda: [{"source": "safari", "url": "https://a.com"}],
    )
    monkeypatch.setattr(
        mod,
        "parse_chrome_bookmarks",
        lambda: [{"source": "chrome", "url": "https://b.com"}],
    )

    result = sync_bookmarks()
    assert len(result) == 2
