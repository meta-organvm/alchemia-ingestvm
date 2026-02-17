"""Generate PROVENANCE.yaml and provenance-registry.json."""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml


def generate_provenance_yaml(entries: list[dict], repo_name: str, org: str) -> str:
    """Generate a PROVENANCE.yaml for a specific repo.

    Lists all source materials ingested into this repo with their
    original paths, SHA-256 fingerprints, and classification metadata.
    """
    materials = []
    for entry in entries:
        classification = entry.get("classification", {})
        if classification.get("target_repo") != repo_name:
            continue
        if classification.get("target_org") != org:
            continue

        materials.append({
            "filename": entry["filename"],
            "source_path": entry["path"],
            "sha256": entry["sha256"],
            "size_bytes": entry["size_bytes"],
            "last_modified": entry["last_modified"],
            "classification_rule": classification.get("rule_name", ""),
            "confidence": classification.get("confidence", 0),
            "target_subdir": classification.get("target_subdir", ""),
        })

    if not materials:
        return ""

    doc = {
        "schema_version": "1.0",
        "repo": repo_name,
        "org": org,
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_materials": len(materials),
        "materials": materials,
    }

    return yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)


def generate_provenance_registry(entries: list[dict]) -> dict:
    """Generate the master provenance-registry.json with bidirectional traceability.

    Maps: source_file → target_repo AND target_repo → source_files
    """
    source_to_repo = {}
    repo_to_sources = defaultdict(list)

    for entry in entries:
        classification = entry.get("classification", {})
        if classification.get("status") != "CLASSIFIED":
            continue

        org = classification.get('target_org', '')
        repo = classification.get('target_repo', 'unspecified')
        target_key = f"{org}/{repo}"
        source_path = entry["path"]

        source_to_repo[source_path] = {
            "target": target_key,
            "organ": classification.get("target_organ", ""),
            "rule": classification.get("rule_name", ""),
            "confidence": classification.get("confidence", 0),
        }

        repo_to_sources[target_key].append({
            "source_path": source_path,
            "filename": entry["filename"],
            "sha256": entry["sha256"],
            "size_bytes": entry["size_bytes"],
        })

    return {
        "schema_version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_classified": len(source_to_repo),
        "total_target_repos": len(repo_to_sources),
        "source_to_repo": source_to_repo,
        "repo_to_sources": dict(repo_to_sources),
    }


def get_deployment_plan(entries: list[dict]) -> dict:
    """Group classified entries by target repo for deployment planning."""
    from alchemia.alchemize.transformer import classify_action, get_deploy_path

    plan = defaultdict(lambda: {"deploy": [], "convert": [], "reference": [], "skip": []})

    for entry in entries:
        classification = entry.get("classification", {})
        if classification.get("status") != "CLASSIFIED":
            continue

        org = classification.get("target_org", "")
        repo = classification.get("target_repo")
        if not org:
            continue

        key = f"{org}/{repo or 'unspecified'}"
        action = classify_action(entry)

        if action == "skip":
            plan[key]["skip"].append(entry)
        elif action == "reference":
            plan[key]["reference"].append(entry)
        elif action == "convert_docx":
            plan[key]["convert"].append(entry)
        else:
            entry["_deploy_path"] = get_deploy_path(entry)
            plan[key]["deploy"].append(entry)

    return dict(plan)
