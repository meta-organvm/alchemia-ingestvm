"""Tests for alchemia ALCHEMIZE transformer."""

from alchemia.alchemize.transformer import classify_action, get_deploy_path, sanitize_filename


def _classified_entry(ext=".md", size=100, duplicate=False):
    """Helper to build a classified entry dict."""
    return {
        "filename": f"test{ext}",
        "extension": ext,
        "size_bytes": size,
        "duplicate": duplicate,
        "classification": {
            "status": "CLASSIFIED",
            "target_subdir": "docs/source-materials/",
            "target_repo": "test-repo",
            "target_org": "test-org",
        },
    }


class TestClassifyAction:
    def test_deploy_md(self):
        assert classify_action(_classified_entry(".md")) == "deploy"

    def test_convert_docx(self):
        assert classify_action(_classified_entry(".docx")) == "convert_docx"

    def test_reference_gdoc(self):
        assert classify_action(_classified_entry(".gdoc")) == "reference"

    def test_skip_duplicate(self):
        assert classify_action(_classified_entry(duplicate=True)) == "skip"

    def test_large_pdf_reference(self):
        assert classify_action(_classified_entry(".pdf", size=6_000_000)) == "reference"

    def test_small_pdf_deploy(self):
        assert classify_action(_classified_entry(".pdf", size=1_000_000)) == "deploy"

    def test_unclassified_skip(self):
        entry = _classified_entry()
        entry["classification"]["status"] = "UNCLASSIFIED"
        assert classify_action(entry) == "skip"

    def test_python_deploy(self):
        assert classify_action(_classified_entry(".py")) == "deploy"

    def test_unknown_small_deploy(self):
        assert classify_action(_classified_entry(".xyz", size=50_000)) == "deploy"


class TestSanitizeFilename:
    def test_special_chars(self):
        result = sanitize_filename('file|name"test')
        assert "|" not in result
        assert '"' not in result
        assert "-" in result

    def test_collapse_dashes(self):
        result = sanitize_filename("a---b---c")
        assert "---" not in result
        assert result == "a-b-c"

    def test_empty_returns_unnamed(self):
        assert sanitize_filename("...") == "unnamed"


class TestGetDeployPath:
    def test_correct_path(self):
        entry = _classified_entry(".md")
        result = get_deploy_path(entry)
        assert result == "docs/source-materials/test.md"
