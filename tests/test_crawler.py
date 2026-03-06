"""Tests for intake/crawler.py — filesystem crawl and fingerprinting."""

import hashlib
from pathlib import Path

from alchemia.intake.crawler import crawl, file_metadata, sha256_file


def test_sha256_file(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert sha256_file(f) == expected


def test_sha256_file_unreadable(tmp_path, monkeypatch):
    f = tmp_path / "locked.txt"
    f.write_text("data")

    original_open = Path.open

    def broken_open(self, *args, **kwargs):
        if str(self) == str(f):
            raise OSError("Permission denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", broken_open)
    assert sha256_file(f) == "ERROR_UNREADABLE"


def test_file_metadata_fields(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x = 1")
    meta = file_metadata(f, tmp_path)
    assert meta["filename"] == "test.py"
    assert meta["extension"] == ".py"
    assert meta["size_bytes"] > 0
    assert meta["sha256"] != "ERROR_UNREADABLE"
    assert "path" in meta
    assert "relative_path" in meta
    assert "last_modified" in meta
    assert meta["depth"] == 0


def test_crawl_empty_dir(tmp_path):
    assert crawl([tmp_path]) == []


def test_crawl_with_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.py").write_text("b")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("c")
    result = crawl([tmp_path])
    assert len(result) == 3


def test_crawl_skips_gitdir(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("gitconfig")
    (tmp_path / "real.txt").write_text("real")
    result = crawl([tmp_path])
    assert len(result) == 1
    assert result[0]["filename"] == "real.txt"


def test_crawl_skips_ds_store(tmp_path):
    (tmp_path / ".DS_Store").write_text("x")
    (tmp_path / "real.txt").write_text("y")
    result = crawl([tmp_path])
    assert len(result) == 1
    assert result[0]["filename"] == "real.txt"


def test_crawl_nonexistent_dir(tmp_path):
    result = crawl([tmp_path / "nope"])
    assert result == []
