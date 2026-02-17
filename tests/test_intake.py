"""Tests for the INTAKE stage."""

from alchemia.intake.crawler import crawl, file_metadata, sha256_file
from alchemia.intake.dedup import mark_duplicates


def test_sha256_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    h = sha256_file(f)
    assert len(h) == 64
    assert h == sha256_file(f)  # deterministic


def test_sha256_different_content(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("hello")
    f2.write_text("world")
    assert sha256_file(f1) != sha256_file(f2)


def test_crawl_basic(tmp_path):
    (tmp_path / "doc.md").write_text("# Hello")
    (tmp_path / "code.py").write_text("print('hi')")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.txt").write_text("deep file")

    entries = crawl([tmp_path])
    assert len(entries) == 3
    names = {e["filename"] for e in entries}
    assert names == {"doc.md", "code.py", "deep.txt"}


def test_crawl_skips_git(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")
    (tmp_path / "real.md").write_text("real file")

    entries = crawl([tmp_path])
    assert len(entries) == 1
    assert entries[0]["filename"] == "real.md"


def test_crawl_skips_ds_store(tmp_path):
    (tmp_path / ".DS_Store").write_bytes(b"\x00\x00")
    (tmp_path / "real.md").write_text("real file")

    entries = crawl([tmp_path])
    assert len(entries) == 1


def test_file_metadata_fields(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("# Hello World")
    meta = file_metadata(f, tmp_path)

    assert meta["filename"] == "test.md"
    assert meta["extension"] == ".md"
    assert meta["mime_type"] == "text/markdown"
    assert meta["size_bytes"] == len("# Hello World")
    assert meta["sha256"]
    assert meta["depth"] == 0


def test_mark_duplicates():
    entries = [
        {"path": "/a/deep/file.md", "sha256": "abc123", "depth": 2},
        {"path": "/b/file.md", "sha256": "abc123", "depth": 0},
        {"path": "/c/unique.md", "sha256": "def456", "depth": 0},
    ]
    result = mark_duplicates(entries)
    # Deeper path wins
    assert result[0]["duplicate"] is False  # /a/deep/file.md (depth 2)
    assert result[1]["duplicate"] is True  # /b/file.md (depth 0)
    assert result[2]["duplicate"] is False  # unique


def test_crawl_nonexistent_dir(tmp_path, capsys):
    entries = crawl([tmp_path / "nonexistent"])
    assert entries == []
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
