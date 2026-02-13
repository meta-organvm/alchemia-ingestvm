"""Tests for the ABSORB stage classifier."""

from alchemia.absorb.classifier import classify_entry
from alchemia.absorb.name_variants import NAME_VARIANTS


def _mock_registry():
    return {
        "repos": [
            {"name": "recursive-engine--generative-entity", "org": "organvm-i-theoria", "organ": "ORGAN-I"},
            {"name": "showcase-portfolio", "org": "organvm-ii-poiesis", "organ": "ORGAN-II"},
            {"name": "hokage-chess", "org": "organvm-iii-ergon", "organ": "ORGAN-III"},
        ],
        "by_name": {
            "recursive-engine--generative-entity": {
                "name": "recursive-engine--generative-entity",
                "org": "organvm-i-theoria",
                "organ": "ORGAN-I",
            },
            "showcase-portfolio": {
                "name": "showcase-portfolio",
                "org": "organvm-ii-poiesis",
                "organ": "ORGAN-II",
            },
            "hokage-chess": {
                "name": "hokage-chess",
                "org": "organvm-iii-ergon",
                "organ": "ORGAN-III",
            },
        },
        "by_org": {},
        "archived": set(),
    }


def test_rule1_direct_match():
    entry = {
        "path": "/Users/4jp/Workspace/recursive-engine--generative-entity/src/main.py",
        "filename": "main.py",
        "extension": ".py",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 1
    assert result["rule_name"] == "direct_repo_match"
    assert result["confidence"] == 1.0
    assert result["target_repo"] == "recursive-engine--generative-entity"


def test_rule2_name_variant():
    entry = {
        "path": "/Users/4jp/Workspace/hokage-chess--believe-it!/README.md",
        "filename": "README.md",
        "extension": ".md",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 2
    assert result["rule_name"] == "name_variant_match"
    assert result["target_repo"] == "hokage-chess"


def test_rule3_staging_dir():
    entry = {
        "path": "/Users/4jp/Workspace/ORG-IV-orchestration-staging/plan.md",
        "filename": "plan.md",
        "extension": ".md",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 3
    assert result["target_org"] == "organvm-iv-taxis"


def test_rule4_process_container():
    entry = {
        "path": "/Users/4jp/Workspace/intake/processCONTAINER/spec.md",
        "relative_path": "processCONTAINER/spec.md",
        "filename": "spec.md",
        "extension": ".md",
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 4
    assert result["rule_name"] == "process_container"
    assert result["target_repo"] == "recursive-engine--generative-entity"


def test_rule7_unresolved():
    entry = {
        "path": "/Users/4jp/Workspace/unknown-dir/mystery.zip",
        "filename": "mystery.zip",
        "extension": ".zip",
        "manifest": None,
    }
    result = classify_entry(entry, _mock_registry())
    assert result["rule"] == 7
    assert result["status"] == "PENDING_REVIEW"


def test_name_variants_table():
    assert NAME_VARIANTS["hokage-chess--believe-it!"] == "hokage-chess"
    assert NAME_VARIANTS["portfolio"] == "showcase-portfolio"
