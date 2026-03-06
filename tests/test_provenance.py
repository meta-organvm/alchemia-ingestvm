"""Tests for alchemia ALCHEMIZE provenance generation."""

import yaml

from alchemia.alchemize.provenance import (
    generate_provenance_registry,
    generate_provenance_yaml,
    get_deployment_plan,
)


def _entry(filename="test.md", repo="repo-a", org="org-a", ext=".md", size=100):
    return {
        "filename": filename,
        "path": f"/source/{filename}",
        "sha256": "abc123",
        "size_bytes": size,
        "last_modified": "2026-03-01",
        "extension": ext,
        "duplicate": False,
        "classification": {
            "status": "CLASSIFIED",
            "target_repo": repo,
            "target_org": org,
            "target_organ": "ORGAN-I",
            "target_subdir": "docs/",
            "rule_name": "theory-docs",
            "confidence": 0.9,
        },
    }


class TestGenerateProvenanceYaml:
    def test_empty_returns_empty(self):
        assert generate_provenance_yaml([], "repo-a", "org-a") == ""

    def test_with_entries(self):
        result = generate_provenance_yaml([_entry()], "repo-a", "org-a")
        assert result  # non-empty
        parsed = yaml.safe_load(result)
        assert parsed["repo"] == "repo-a"
        assert parsed["total_materials"] == 1

    def test_filters_by_repo(self):
        entries = [_entry(repo="repo-a"), _entry(filename="other.md", repo="repo-b")]
        result = generate_provenance_yaml(entries, "repo-a", "org-a")
        parsed = yaml.safe_load(result)
        assert parsed["total_materials"] == 1


class TestGenerateProvenanceRegistry:
    def test_bidirectional_mapping(self):
        result = generate_provenance_registry([_entry()])
        assert result["total_classified"] == 1
        assert result["total_target_repos"] == 1
        assert "/source/test.md" in result["source_to_repo"]
        assert "org-a/repo-a" in result["repo_to_sources"]

    def test_none_repo_becomes_unspecified(self):
        """When target_repo is None (rules 3,5,6), key should use 'unspecified' not 'None'."""
        e = _entry()
        e["classification"]["target_repo"] = None
        result = generate_provenance_registry([e])
        # Must NOT contain "None" as a string
        for key in result["repo_to_sources"]:
            assert "/None" not in key, f"Found literal 'None' in key: {key}"
        assert "org-a/unspecified" in result["repo_to_sources"]


class TestGetDeploymentPlan:
    def test_groups_by_repo(self):
        entries = [_entry(repo="repo-a"), _entry(filename="b.md", repo="repo-b")]
        plan = get_deployment_plan(entries)
        assert "org-a/repo-a" in plan
        assert "org-a/repo-b" in plan

    def test_action_categories(self):
        entries = [
            _entry(ext=".md"),
            _entry(filename="doc.docx", ext=".docx"),
            _entry(filename="big.pdf", ext=".pdf", size=6_000_000),
        ]
        plan = get_deployment_plan(entries)
        key = "org-a/repo-a"
        assert len(plan[key]["deploy"]) >= 1
        assert len(plan[key]["convert"]) == 1
        assert len(plan[key]["reference"]) == 1
