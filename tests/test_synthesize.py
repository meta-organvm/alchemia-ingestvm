"""Tests for synthesize.py — creative brief generation."""

from unittest.mock import patch

from alchemia.synthesize import (
    ORGAN_MAP,
    analyze_references,
    generate_all_briefs,
    generate_creative_brief,
    generate_workflow_integration_example,
)


@patch("alchemia.synthesize.load_taste")
def test_analyze_references_empty(mock_taste):
    mock_taste.return_value = {"references": []}
    result = analyze_references()
    assert result["total"] == 0
    assert result["by_tag"] == {}


@patch("alchemia.synthesize.load_taste")
def test_analyze_references_with_refs(mock_taste):
    mock_taste.return_value = {
        "references": [
            {"type": "url", "tags": ["art", "design"]},
            {"type": "url", "tags": ["art", "code"]},
            {"type": "description", "tags": ["theory"]},
        ],
    }
    result = analyze_references()
    assert result["total"] == 3
    assert "art" in result["by_tag"]
    assert len(result["by_tag"]["art"]) == 2
    assert result["tag_counts"]["art"] == 2
    assert "url" in result["by_type"]


@patch("alchemia.synthesize.resolve_aesthetic_chain")
@patch("alchemia.synthesize.load_taste")
@patch("alchemia.synthesize.format_prompt_injection", return_value="# prompt block")
def test_generate_creative_brief_has_sections(mock_fmt, mock_taste, mock_chain):
    mock_taste.return_value = {"references": []}
    mock_chain.return_value = {"palette": {"primary": "#000"}, "references": []}
    brief = generate_creative_brief("ORGAN-I")
    assert "Identity" in brief
    assert "Color Palette" in brief
    assert "Theoria" in brief


@patch("alchemia.synthesize.resolve_aesthetic_chain")
@patch("alchemia.synthesize.load_taste")
@patch("alchemia.synthesize.format_prompt_injection", return_value="# prompt block")
def test_generate_creative_brief_unknown_organ(mock_fmt, mock_taste, mock_chain):
    mock_taste.return_value = {"references": []}
    mock_chain.return_value = {"references": []}
    brief = generate_creative_brief("ORGAN-X")
    assert "ORGAN-X" in brief  # Uses the key as name


@patch("alchemia.synthesize.generate_creative_brief")
def test_generate_all_briefs(mock_brief, tmp_path):
    mock_brief.return_value = "# Brief content"
    outputs = generate_all_briefs(output_dir=tmp_path)
    assert len(outputs) == len(ORGAN_MAP)
    for p in outputs:
        assert p.exists()


def test_workflow_integration_example():
    example = generate_workflow_integration_example()
    assert len(example) > 0
    assert "GitHub Actions" in example


def test_organ_map_has_all_organs():
    assert len(ORGAN_MAP) == 8
    assert "ORGAN-I" in ORGAN_MAP
    assert "META-ORGANVM" in ORGAN_MAP
