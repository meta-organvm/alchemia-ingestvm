"""Tests for absorb/registry_loader.py — registry loading and lookup."""

import json

from alchemia.absorb.registry_loader import load_registry


def _write_registry(tmp_path, organs):
    reg = {"organs": organs}
    path = tmp_path / "registry-v2.json"
    path.write_text(json.dumps(reg))
    return path


def test_load_registry_from_fixture(tmp_path):
    path = _write_registry(
        tmp_path,
        {
            "ORGAN-I": {
                "repositories": [
                    {"name": "repo-a", "org": "org-a", "status": "ACTIVE"},
                ],
            },
        },
    )
    result = load_registry(path)
    assert "repos" in result
    assert "by_name" in result
    assert "by_org" in result
    assert "archived" in result
    assert len(result["repos"]) == 1


def test_load_registry_archived_detection(tmp_path):
    path = _write_registry(
        tmp_path,
        {
            "ORGAN-I": {
                "repositories": [
                    {"name": "old-repo", "org": "org-a", "status": "ARCHIVED"},
                ],
            },
        },
    )
    result = load_registry(path)
    assert "old-repo" in result["archived"]


def test_load_registry_by_name_lookup(tmp_path):
    path = _write_registry(
        tmp_path,
        {
            "ORGAN-I": {
                "repositories": [
                    {"name": "repo-x", "org": "org-a", "status": "ACTIVE"},
                ],
            },
        },
    )
    result = load_registry(path)
    assert "repo-x" in result["by_name"]
    assert result["by_name"]["repo-x"]["organ"] == "ORGAN-I"


def test_load_registry_by_org_grouping(tmp_path):
    path = _write_registry(
        tmp_path,
        {
            "ORGAN-I": {
                "repositories": [
                    {"name": "repo-a", "org": "shared-org", "status": "ACTIVE"},
                    {"name": "repo-b", "org": "shared-org", "status": "ACTIVE"},
                ],
            },
        },
    )
    result = load_registry(path)
    assert len(result["by_org"]["shared-org"]) == 2
