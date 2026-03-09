"""Tests for alchemize/deployer.py — GitHub API file deployment."""

import json
import subprocess

from alchemia.alchemize.deployer import (
    deploy_file,
    get_default_branch,
    get_file_sha,
    gh_api,
    is_archived,
)


def _mock_subprocess(monkeypatch, returncode=0, stdout="", stderr=""):
    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(subprocess, "run", mock_run)
    return mock_run


def test_gh_api_success(monkeypatch):
    _mock_subprocess(monkeypatch, stdout=json.dumps({"sha": "abc123"}))
    result = gh_api("GET", "/repos/org/repo/contents/file.md")
    assert result == {"sha": "abc123"}


def test_gh_api_failure(monkeypatch):
    _mock_subprocess(monkeypatch, returncode=1, stderr="not found")
    result = gh_api("GET", "/repos/org/repo/contents/nope", silent=True)
    assert result is None


def test_gh_api_non_json(monkeypatch):
    _mock_subprocess(monkeypatch, stdout="plain text response")
    result = gh_api("GET", "/repos/org/repo")
    assert result == "plain text response"


def test_get_file_sha_exists(monkeypatch):
    _mock_subprocess(monkeypatch, stdout=json.dumps({"sha": "abc123"}))
    assert get_file_sha("org", "repo", "file.md") == "abc123"


def test_get_file_sha_not_found(monkeypatch):
    _mock_subprocess(monkeypatch, returncode=1, stderr="not found")
    assert get_file_sha("org", "repo", "nope.md") is None


def test_get_default_branch(monkeypatch):
    _mock_subprocess(monkeypatch, stdout=json.dumps({"default_branch": "develop"}))
    assert get_default_branch("org", "repo") == "develop"


def test_is_archived_true(monkeypatch):
    _mock_subprocess(monkeypatch, stdout=json.dumps({"archived": True}))
    assert is_archived("org", "repo") is True


def test_is_archived_false(monkeypatch):
    _mock_subprocess(monkeypatch, stdout=json.dumps({"archived": False}))
    assert is_archived("org", "repo") is False


def test_deploy_file_dry_run(tmp_path):
    source = tmp_path / "file.md"
    source.write_text("content")
    result = deploy_file("org", "repo", "docs/file.md", source, dry_run=True)
    assert result["status"] == "dry_run"


def test_deploy_file_success(monkeypatch, tmp_path):
    source = tmp_path / "file.md"
    source.write_text("content")

    call_count = {"n": 0}

    def mock_run(cmd, **kwargs):
        call_count["n"] += 1
        # First call: get_file_sha (not found), second call: put_file
        if call_count["n"] == 1:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not found")
        return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = deploy_file("org", "repo", "docs/file.md", source)
    assert result["status"] == "deployed"


def test_deploy_file_source_missing(tmp_path):
    source = tmp_path / "nonexistent.md"
    result = deploy_file("org", "repo", "docs/file.md", source)
    assert result["status"] == "error"
