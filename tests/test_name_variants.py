"""Tests for absorb/name_variants.py — directory name resolution."""

from alchemia.absorb.name_variants import (
    DIR_TO_ORGAN,
    NAME_VARIANTS,
    STAGING_DIR_TO_ORG,
    resolve_organ_dir,
    resolve_staging,
    resolve_variant,
)


def test_resolve_variant_known():
    assert resolve_variant("hokage-chess--believe-it!") == "hokage-chess"


def test_resolve_variant_unknown():
    assert resolve_variant("no-such-thing") is None


def test_resolve_staging_known():
    assert resolve_staging("ORG-IV-orchestration-staging") == "organvm-iv-taxis"


def test_resolve_staging_unknown():
    assert resolve_staging("random-dir") is None


def test_resolve_organ_dir_known():
    result = resolve_organ_dir("OS-me")
    assert result is not None
    assert result["organ"] == "ORGAN-IV"


def test_resolve_organ_dir_unknown():
    assert resolve_organ_dir("nope") is None


def test_name_variants_not_empty():
    assert len(NAME_VARIANTS) == 7


def test_dir_to_organ_not_empty():
    assert len(DIR_TO_ORGAN) == 12
