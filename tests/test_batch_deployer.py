"""Tests for alchemize/batch_deployer.py — batch deployment via GitHub API."""

import subprocess
from unittest.mock import patch

from alchemia.alchemize.batch_deployer import (
    build_deployment_manifest,
    deploy_repo_batch,
)


def _make_classified_entry(repo, org, status="CLASSIFIED"):
    return {
        "path": f"/tmp/source/{repo}/file.md",
        "filename": "file.md",
        "extension": ".md",
        "size_bytes": 100,
        "classification": {
            "status": status,
            "target_organ": "ORGAN-I",
            "target_org": org,
            "target_repo": repo,
            "target_subdir": "docs/source-materials/theory/",
        },
    }


@patch("alchemia.alchemize.batch_deployer.get_deploy_path", return_value="docs/source-materials/theory/file.md")
@patch("alchemia.alchemize.batch_deployer.classify_action", return_value="deploy")
def test_build_manifest_groups_by_repo(mock_action, mock_path):
    entries = [
        _make_classified_entry("repo-a", "org-a"),
        _make_classified_entry("repo-b", "org-b"),
    ]
    registry = {"archived": set()}
    manifest = build_deployment_manifest(entries, registry)
    assert len(manifest) == 2
    assert "org-a/repo-a" in manifest
    assert "org-b/repo-b" in manifest


@patch("alchemia.alchemize.batch_deployer.get_deploy_path", return_value="docs/file.md")
@patch("alchemia.alchemize.batch_deployer.classify_action", return_value="deploy")
def test_build_manifest_skips_unclassified(mock_action, mock_path):
    entries = [_make_classified_entry("repo-a", "org-a", status="PENDING_REVIEW")]
    manifest = build_deployment_manifest(entries, {"archived": set()})
    assert len(manifest) == 0


@patch("alchemia.alchemize.batch_deployer.get_deploy_path", return_value="docs/file.md")
@patch("alchemia.alchemize.batch_deployer.classify_action", return_value="reference")
def test_build_manifest_skips_non_deploy_actions(mock_action, mock_path):
    entries = [_make_classified_entry("repo-a", "org-a")]
    manifest = build_deployment_manifest(entries, {"archived": set()})
    assert len(manifest) == 0


def test_deploy_repo_batch_dry_run():
    files = [{"source": "/tmp/file.md", "target": "docs/file.md", "filename": "file.md"}]
    result = deploy_repo_batch("org", "repo", files, dry_run=True)
    assert result["status"] == "dry_run"


@patch("alchemia.alchemize.batch_deployer.is_repo_archived", return_value=True)
def test_deploy_repo_batch_archived(mock_archived):
    files = [{"source": "/tmp/file.md", "target": "docs/file.md", "filename": "file.md"}]
    result = deploy_repo_batch("org", "repo", files)
    assert result["status"] == "skipped_archived"
    assert result["skipped"] == 1


@patch("alchemia.alchemize.batch_deployer.is_repo_archived", return_value=False)
@patch("alchemia.alchemize.batch_deployer.get_default_branch", return_value="main")
@patch("alchemia.alchemize.batch_deployer.check_file_exists", return_value=False)
def test_deploy_repo_batch_source_not_found(mock_exists, mock_branch, mock_archived, tmp_path):
    files = [
        {
            "source": str(tmp_path / "nonexistent.md"),
            "target": "docs/file.md",
            "filename": "file.md",
        },
    ]
    result = deploy_repo_batch("org", "repo", files)
    assert result["failed"] == 1
