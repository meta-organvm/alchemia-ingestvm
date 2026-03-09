"""Tests for intake/manifest_loader.py — CSV manifest and sidecar enrichment."""

import json

from alchemia.intake.manifest_loader import enrich_from_manifest, enrich_from_sidecars


def test_enrich_from_manifest_matches(tmp_path):
    csv_content = (
        "ID,Category,Title,Size_KB,Type,Status,Primary_Tags,Key_Dependencies,Primary_Use,Phase\n"
    )
    csv_content += '1,Theory,report.md,10,doc,active,"tag1","dep1",research,1\n'
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(csv_content)

    entries = [{"filename": "report.md", "path": str(tmp_path / "report.md")}]
    result = enrich_from_manifest(entries, manifest)
    assert result[0]["manifest"] is not None
    assert result[0]["manifest"]["manifest_category"] == "Theory"


def test_enrich_from_manifest_no_match(tmp_path):
    csv_content = (
        "ID,Category,Title,Size_KB,Type,Status,Primary_Tags,Key_Dependencies,Primary_Use,Phase\n"
    )
    csv_content += '1,Theory,other.md,10,doc,active,"tag1","dep1",research,1\n'
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(csv_content)

    entries = [{"filename": "unrelated.md", "path": str(tmp_path / "unrelated.md")}]
    result = enrich_from_manifest(entries, manifest)
    assert result[0]["manifest"] is None


def test_enrich_from_manifest_stem_match(tmp_path):
    csv_content = (
        "ID,Category,Title,Size_KB,Type,Status,Primary_Tags,Key_Dependencies,Primary_Use,Phase\n"
    )
    csv_content += '1,Theory,foo,10,doc,active,"tag1","dep1",research,1\n'
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(csv_content)

    entries = [{"filename": "foo.md", "path": str(tmp_path / "foo.md")}]
    result = enrich_from_manifest(entries, manifest)
    assert result[0]["manifest"] is not None


def test_enrich_from_sidecars_found(tmp_path):
    # Create main file and sidecar
    main_file = tmp_path / "foo.py"
    main_file.write_text("print('hello')")
    sidecar = tmp_path / "foo.py.meta.json"
    sidecar.write_text(json.dumps({"author": "test", "tags": ["util"]}))

    entries = [
        {"filename": "foo.py", "path": str(main_file)},
        {"filename": "foo.py.meta.json", "path": str(sidecar)},
    ]
    result = enrich_from_sidecars(entries)
    main_entry = [e for e in result if e["filename"] == "foo.py"][0]
    assert main_entry["sidecar"] is not None
    assert main_entry["sidecar"]["author"] == "test"


def test_enrich_from_sidecars_none(tmp_path):
    entries = [
        {"filename": "bar.py", "path": str(tmp_path / "bar.py")},
    ]
    result = enrich_from_sidecars(entries)
    assert result[0]["sidecar"] is None


def test_enrich_from_sidecars_invalid_json(tmp_path):
    main_file = tmp_path / "baz.py"
    main_file.write_text("x = 1")
    sidecar = tmp_path / "baz.py.meta.json"
    sidecar.write_text("{not valid json")

    entries = [
        {"filename": "baz.py", "path": str(main_file)},
        {"filename": "baz.py.meta.json", "path": str(sidecar)},
    ]
    result = enrich_from_sidecars(entries)
    main_entry = [e for e in result if e["filename"] == "baz.py"][0]
    assert main_entry["sidecar"] is None
