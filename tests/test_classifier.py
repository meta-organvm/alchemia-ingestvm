"""Tests for absorb/classifier.py — 7-rule priority chain classification."""

from pathlib import Path

from alchemia.absorb.classifier import (
    _get_toplevel_dir,
    _subdir_for_ext,
    classify_all,
    classify_entry,
)


def _mock_registry():
    return {
        "by_name": {
            "my-repo": {
                "name": "my-repo",
                "organ": "ORGAN-I",
                "org": "organvm-i-theoria",
            },
            "hokage-chess": {
                "name": "hokage-chess",
                "organ": "ORGAN-III",
                "org": "labores-profani-crux",
            },
        },
        "archived": set(),
    }


def test_rule1_direct_repo_match():
    entry = {"path": "/Users/x/Workspace/my-repo/docs/file.md", "extension": ".md"}
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 1
    assert result["confidence"] == 1.0
    assert result["target_organ"] == "ORGAN-I"
    assert result["status"] == "CLASSIFIED"


def test_rule2_name_variant_match():
    entry = {"path": "/Users/x/Workspace/hokage-chess--believe-it!/file.py", "extension": ".py"}
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 2
    assert result["confidence"] == 0.95
    assert result["target_repo"] == "hokage-chess"


def test_rule3_staging_dir_match():
    entry = {
        "path": "/Users/x/Workspace/ORG-IV-orchestration-staging/spec.md",
        "extension": ".md",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 3
    assert result["rule_name"] == "staging_dir_match"
    assert result["target_org"] == "organvm-iv-taxis"


def test_rule3b_dir_to_organ():
    entry = {"path": "/Users/x/Workspace/OS-me/notes.txt", "extension": ".txt"}
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 3
    assert result["rule_name"] == "dir_to_organ"
    assert result["target_organ"] == "ORGAN-IV"


def test_rule4_process_container():
    entry = {
        "path": "/Users/x/Workspace/intake/processCONTAINER/file.yaml",
        "relative_path": "processCONTAINER/file.yaml",
        "extension": ".yaml",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 4
    assert result["rule_name"] == "process_container"
    assert result["target_organ"] == "ORGAN-I"


def test_rule4_insort():
    entry = {
        "path": "/Users/x/Workspace/intake/inSORT/file.json",
        "relative_path": "inSORT/file.json",
        "extension": ".json",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 4
    assert result["rule_name"] == "insort_routing"
    assert result["target_organ"] == "ORGAN-I"


def test_rule5_manifest_category():
    entry = {
        "path": "/Users/x/Workspace/unknown-dir/spec.md",
        "extension": ".md",
        "relative_path": "unknown-dir/spec.md",
        "manifest": {"manifest_category": "Technical Specifications"},
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 5
    assert result["target_organ"] == "ORGAN-I"


def test_rule6_content_keyword(tmp_path):
    # Create a file with enough organ-I keywords
    f = tmp_path / "theory.md"
    f.write_text("epistemology recursive ontology dialectic formal logic")
    entry = {
        "path": str(f),
        "extension": ".md",
        "relative_path": "some-unknown/theory.md",
        "manifest": None,
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 6
    assert result["target_organ"] == "ORGAN-I"


def test_rule6_insufficient_keywords(tmp_path):
    # Only 1 keyword match — not enough for rule 6
    f = tmp_path / "partial.md"
    f.write_text("epistemology is interesting but nothing else matches here.")
    entry = {
        "path": str(f),
        "extension": ".md",
        "relative_path": "some-unknown/partial.md",
        "manifest": None,
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 7  # Falls through to unresolved


def test_rule7_unresolved():
    entry = {
        "path": "/Users/x/Workspace/random-place/file.pdf",
        "extension": ".pdf",
        "relative_path": "random-place/file.pdf",
        "manifest": None,
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 7
    assert result["status"] == "PENDING_REVIEW"
    assert result["confidence"] == 0.0


def test_classify_all_adds_classification():
    entries = [
        {"path": "/Users/x/Workspace/my-repo/a.md", "extension": ".md"},
        {"path": "/Users/x/Workspace/random/b.pdf", "extension": ".pdf",
         "relative_path": "random/b.pdf", "manifest": None},
    ]
    result = classify_all(entries, _mock_registry())
    assert all("classification" in e for e in result)


def test_subdir_for_ext_md():
    assert _subdir_for_ext(".md") == "theory"


def test_subdir_for_ext_py():
    assert _subdir_for_ext(".py") == "prototypes"


def test_subdir_for_ext_unknown():
    assert _subdir_for_ext(".xyz") == "theory"


def test_get_toplevel_dir():
    entry = {"path": "/Users/x/Workspace/my-repo/sub/file.py"}
    assert _get_toplevel_dir(entry) == "my-repo"
