"""Tests for cmd_review in cli.py — PENDING_REVIEW item display."""

import json
from argparse import Namespace

from alchemia.cli import cmd_review


def test_cmd_review_no_mapping_file(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    args = Namespace(status="PENDING_REVIEW")
    cmd_review(args)
    out = capsys.readouterr().out
    assert "No absorb-mapping.json found" in out


def test_cmd_review_no_matching_entries(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    mapping = {
        "entries": [
            {
                "filename": "file.md",
                "classification": {"status": "CLASSIFIED", "rule": 1},
            },
        ],
    }
    (data_dir / "absorb-mapping.json").write_text(json.dumps(mapping))

    args = Namespace(status="PENDING_REVIEW")
    cmd_review(args)
    out = capsys.readouterr().out
    assert "No entries with status 'PENDING_REVIEW'" in out


def test_cmd_review_displays_pending_entries(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    mapping = {
        "entries": [
            {
                "filename": "mystery.pdf",
                "classification": {
                    "status": "PENDING_REVIEW",
                    "rule": 7,
                    "rule_name": "unresolved",
                    "confidence": 0.0,
                    "target_organ": None,
                    "target_repo": None,
                },
            },
            {
                "filename": "known.md",
                "classification": {
                    "status": "CLASSIFIED",
                    "rule": 1,
                    "rule_name": "direct_repo_match",
                    "confidence": 1.0,
                    "target_organ": "ORGAN-I",
                    "target_repo": "my-repo",
                },
            },
        ],
    }
    (data_dir / "absorb-mapping.json").write_text(json.dumps(mapping))

    args = Namespace(status="PENDING_REVIEW")
    cmd_review(args)
    out = capsys.readouterr().out
    assert "1 entries with status 'PENDING_REVIEW'" in out
    assert "mystery.pdf" in out
    assert "unresolved" in out
    assert "known.md" not in out


def test_cmd_review_custom_status_filter(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    mapping = {
        "entries": [
            {
                "filename": "classified.md",
                "classification": {
                    "status": "CLASSIFIED",
                    "rule": 1,
                    "rule_name": "direct_repo_match",
                    "confidence": 1.0,
                    "target_organ": "ORGAN-I",
                    "target_repo": "repo-a",
                },
            },
        ],
    }
    (data_dir / "absorb-mapping.json").write_text(json.dumps(mapping))

    args = Namespace(status="CLASSIFIED")
    cmd_review(args)
    out = capsys.readouterr().out
    assert "1 entries with status 'CLASSIFIED'" in out
    assert "classified.md" in out


def test_cmd_review_shows_summary(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    mapping = {
        "entries": [
            {
                "filename": "a.pdf",
                "classification": {
                    "status": "PENDING_REVIEW",
                    "rule": 7,
                    "rule_name": "unresolved",
                    "confidence": 0.0,
                    "target_organ": None,
                    "target_repo": None,
                },
            },
            {
                "filename": "b.txt",
                "classification": {
                    "status": "PENDING_REVIEW",
                    "rule": 7,
                    "rule_name": "unresolved",
                    "confidence": 0.0,
                    "target_organ": None,
                    "target_repo": None,
                },
            },
        ],
    }
    (data_dir / "absorb-mapping.json").write_text(json.dumps(mapping))

    args = Namespace(status="PENDING_REVIEW")
    cmd_review(args)
    out = capsys.readouterr().out
    assert "Summary:" in out
    assert "unresolved: 2" in out
