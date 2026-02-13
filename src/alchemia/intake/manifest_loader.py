"""Load and cross-reference existing metadata sources."""

import csv
import json
from pathlib import Path


def enrich_from_manifest(entries: list[dict], manifest_path: Path) -> list[dict]:
    """Cross-reference entries with MANIFEST_INDEX_TABLE.csv.

    The CSV has columns: ID, Category, Title, Size_KB, Type, Status,
    Primary_Tags, Key_Dependencies, Primary_Use, Phase
    """
    manifest = {}
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Title", "").strip()
            if title:
                manifest[title.lower()] = {
                    "manifest_id": row.get("ID", ""),
                    "manifest_category": row.get("Category", ""),
                    "manifest_tags": row.get("Primary_Tags", ""),
                    "manifest_type": row.get("Type", ""),
                    "manifest_status": row.get("Status", ""),
                    "manifest_primary_use": row.get("Primary_Use", ""),
                    "manifest_phase": row.get("Phase", ""),
                    "manifest_dependencies": row.get("Key_Dependencies", ""),
                }

    matched = 0
    for entry in entries:
        fname = entry["filename"].lower()
        # Try exact match first, then without extension
        stem = Path(fname).stem.lower()
        match = manifest.get(fname) or manifest.get(stem)
        if match:
            entry["manifest"] = match
            matched += 1
        else:
            entry["manifest"] = None

    print(f"  Manifest cross-ref: {matched}/{len(entries)} files matched")
    return entries


def enrich_from_sidecars(entries: list[dict]) -> list[dict]:
    """Look for .meta.json sidecar files and merge their metadata.

    FUNCTIONcalled naming convention: if a file is `foo.py`,
    its sidecar is `foo.py.meta.json`.
    """
    # Build a lookup of all .meta.json files in the inventory
    sidecar_paths = {}
    for entry in entries:
        if entry["filename"].endswith(".meta.json"):
            # The source file is the filename minus ".meta.json"
            source_name = entry["filename"][: -len(".meta.json")]
            parent = str(Path(entry["path"]).parent)
            sidecar_paths[(parent, source_name)] = entry["path"]

    enriched = 0
    for entry in entries:
        if entry["filename"].endswith(".meta.json"):
            continue
        key = (str(Path(entry["path"]).parent), entry["filename"])
        sidecar_path = sidecar_paths.get(key)
        if sidecar_path:
            try:
                with open(sidecar_path, encoding="utf-8") as f:
                    sidecar_data = json.load(f)
                entry["sidecar"] = sidecar_data
                enriched += 1
            except (json.JSONDecodeError, OSError):
                entry["sidecar"] = None
        else:
            entry["sidecar"] = None

    print(f"  Sidecar enrichment: {enriched}/{len(entries)} files have .meta.json")
    return entries
