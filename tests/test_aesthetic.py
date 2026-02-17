"""Tests for the aesthetic nervous system."""

from pathlib import Path

import yaml

from alchemia.aesthetic import add_reference, format_prompt_injection, resolve_aesthetic_chain


def test_taste_yaml_valid():
    taste_path = Path(__file__).parent.parent / "taste.yaml"
    with open(taste_path) as f:
        data = yaml.safe_load(f)
    assert data["schema_version"] == "1.0"
    assert "palette" in data
    assert "typography" in data
    assert "tone" in data
    assert "anti_patterns" in data
    assert len(data["anti_patterns"]) > 0


def test_organ_aesthetics_valid():
    organ_dir = Path(__file__).parent.parent / "data" / "organ-aesthetics"
    for yaml_file in organ_dir.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        assert data["schema_version"] == "1.0"
        assert "inherits" in data
        assert "modifiers" in data


def test_resolve_chain_organ_i():
    chain = resolve_aesthetic_chain(organ="ORGAN-I")
    assert "palette" in chain
    assert "tone" in chain
    assert "organ_modifiers" in chain
    assert chain["organ_name"] == "Theoria"


def test_format_prompt_injection():
    chain = resolve_aesthetic_chain(organ="ORGAN-I")
    prompt = format_prompt_injection(chain)
    assert "Aesthetic Guidelines" in prompt
    assert "cerebral but accessible" in prompt
    assert "Theoria" in prompt
    assert "AVOID:" in prompt


def test_add_reference(tmp_path):
    taste = tmp_path / "taste.yaml"
    taste.write_text(
        yaml.dump(
            {
                "schema_version": "1.0",
                "references": [],
                "anti_patterns": [],
            }
        )
    )
    entry = add_reference("note", "Test note", tags=["test"], path=taste)
    assert entry["type"] == "description"
    assert entry["text"] == "Test note"

    # Verify it was written
    with open(taste) as f:
        data = yaml.safe_load(f)
    assert len(data["references"]) == 1
