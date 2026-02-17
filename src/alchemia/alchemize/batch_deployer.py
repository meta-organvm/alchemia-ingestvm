"""Batch deployment via GitHub push_files (single commit per repo)."""

import base64
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from alchemia.absorb.registry_loader import load_registry
from alchemia.alchemize.transformer import classify_action, get_deploy_path


def get_default_branch(org: str, repo: str) -> str:
    """Get the default branch of a repo."""
    result = subprocess.run(
        ["gh", "api", f"/repos/{org}/{repo}", "--jq", ".default_branch"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "main"


def is_repo_archived(org: str, repo: str) -> bool:
    """Check if a repo is archived."""
    result = subprocess.run(
        ["gh", "api", f"/repos/{org}/{repo}", "--jq", ".archived"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "true"


def check_file_exists(org: str, repo: str, path: str) -> bool:
    """Check if a file already exists in the repo."""
    result = subprocess.run(
        ["gh", "api", f"/repos/{org}/{repo}/contents/{path}"],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def build_deployment_manifest(entries: list[dict], registry: dict | None = None) -> dict:
    """Build a deployment manifest grouped by org/repo.

    Returns dict: {
        "org/repo": {
            "org": str,
            "repo": str,
            "files": [{"source": str, "target": str, "size": int}],
        }
    }
    """
    if registry is None:
        registry = load_registry()

    manifest = defaultdict(lambda: {"files": []})

    for entry in entries:
        classification = entry.get("classification", {})
        if classification.get("status") != "CLASSIFIED":
            continue

        action = classify_action(entry)
        if action not in ("deploy", "convert_docx"):
            continue

        org = classification.get("target_org", "")
        repo = classification.get("target_repo")
        if not org or not repo:
            continue

        # Skip archived repos
        if repo in registry.get("archived", set()):
            continue

        target_path = get_deploy_path(entry)

        key = f"{org}/{repo}"
        manifest[key]["org"] = org
        manifest[key]["repo"] = repo
        manifest[key]["files"].append({
            "source": entry["path"],
            "target": target_path,
            "size": entry.get("size_bytes", 0),
            "filename": entry["filename"],
        })

    return dict(manifest)


def deploy_repo_batch(
    org: str,
    repo: str,
    files: list[dict],
    dry_run: bool = False,
    force: bool = False,
    batch_size: int = 20,
) -> dict:
    """Deploy a batch of files to a single repo.

    Uses gh api to push files. Groups into sub-batches to avoid
    API payload limits.

    Returns deployment result dict.
    """
    result = {
        "org": org,
        "repo": repo,
        "total_files": len(files),
        "deployed": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    if dry_run:
        result["status"] = "dry_run"
        return result

    # Check if repo is archived
    if is_repo_archived(org, repo):
        result["status"] = "skipped_archived"
        result["skipped"] = len(files)
        print(f"  SKIP {org}/{repo}: archived")
        return result

    branch = get_default_branch(org, repo)

    # Deploy files in sub-batches
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]

        for file_info in batch:
            source = Path(file_info["source"])
            target = file_info["target"]

            if not source.exists():
                result["failed"] += 1
                result["errors"].append(f"Source not found: {source}")
                continue

            # Check if file already exists (skip unless force)
            if not force and check_file_exists(org, repo, target):
                result["skipped"] += 1
                continue

            try:
                content = source.read_bytes()
                b64 = base64.b64encode(content).decode("utf-8")

                # Get existing SHA if overwriting
                sha_cmd = ["gh", "api", f"/repos/{org}/{repo}/contents/{target}", "--jq", ".sha"]
                sha_result = subprocess.run(sha_cmd, capture_output=True, text=True)
                existing_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else None

                # Use stdin piping to avoid ARG_MAX on large files
                payload = {
                    "message": f"chore(alchemia): ingest {file_info['filename']}",
                    "content": b64,
                    "branch": branch,
                }
                if existing_sha:
                    payload["sha"] = existing_sha

                deploy_result = subprocess.run(
                    ["gh", "api", "-X", "PUT",
                     f"/repos/{org}/{repo}/contents/{target}",
                     "--input", "-"],
                    input=json.dumps(payload),
                    capture_output=True, text=True,
                )
                if deploy_result.returncode == 0:
                    result["deployed"] += 1
                else:
                    err = deploy_result.stderr.strip()[:200]
                    result["failed"] += 1
                    result["errors"].append(f"{target}: {err}")
            except OSError as e:
                result["failed"] += 1
                result["errors"].append(f"Read error {source}: {e}")

    result["status"] = "completed"
    return result
