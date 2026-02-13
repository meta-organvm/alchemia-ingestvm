"""Deploy files to GitHub repos via the Contents API."""

import base64
import json
import subprocess
from pathlib import Path


def gh_api(method: str, endpoint: str, data: dict | None = None, silent: bool = False) -> dict | str | None:
    """Call GitHub API via gh CLI."""
    cmd = ["gh", "api", "-X", method, endpoint]
    if data:
        if "content" in data:
            cmd.extend(["-f", f"content={data['content']}"])
        if "message" in data:
            cmd.extend(["-f", f"message={data['message']}"])
        if "sha" in data:
            cmd.extend(["-f", f"sha={data['sha']}"])
        if "branch" in data:
            cmd.extend(["-f", f"branch={data['branch']}"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if not silent:
            print(f"    API error: {result.stderr.strip()[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout


def get_file_sha(org: str, repo: str, path: str) -> str | None:
    """Get the SHA of an existing file, or None if it doesn't exist."""
    result = gh_api("GET", f"/repos/{org}/{repo}/contents/{path}", silent=True)
    if result and isinstance(result, dict) and "sha" in result:
        return result["sha"]
    return None


def get_default_branch(org: str, repo: str) -> str:
    """Get the default branch of a repo."""
    result = gh_api("GET", f"/repos/{org}/{repo}", silent=True)
    if result and isinstance(result, dict):
        return result.get("default_branch", "main")
    return "main"


def is_archived(org: str, repo: str) -> bool:
    """Check if a repo is archived on GitHub."""
    result = gh_api("GET", f"/repos/{org}/{repo}", silent=True)
    if result and isinstance(result, dict):
        return result.get("archived", False)
    return False


def is_branch_protected(org: str, repo: str, branch: str) -> bool:
    """Check if a branch has protection rules."""
    result = gh_api("GET", f"/repos/{org}/{repo}/branches/{branch}/protection", silent=True)
    return result is not None and isinstance(result, dict)


def put_file(
    org: str,
    repo: str,
    path: str,
    content_bytes: bytes,
    message: str,
    branch: str | None = None,
    force: bool = False,
) -> bool:
    """Create or update a file via the GitHub Contents API.

    Returns True on success, False on failure.
    If force=False and file already exists, skips (returns False).
    """
    sha = get_file_sha(org, repo, path)
    if sha and not force:
        print(f"    SKIP {path}: already exists (use --force to overwrite)")
        return False

    b64_content = base64.b64encode(content_bytes).decode("utf-8")

    cmd = [
        "gh", "api", "-X", "PUT",
        f"/repos/{org}/{repo}/contents/{path}",
        "-f", f"message={message}",
        "-f", f"content={b64_content}",
    ]
    if sha:
        cmd.extend(["-f", f"sha={sha}"])
    if branch:
        cmd.extend(["-f", f"branch={branch}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip()[:200]
        print(f"    FAIL {path}: {err}")
        return False
    return True


def deploy_file(
    org: str,
    repo: str,
    target_path: str,
    source_path: Path,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Deploy a single file to a GitHub repo.

    Returns a result dict with status information.
    """
    result = {
        "org": org,
        "repo": repo,
        "target_path": target_path,
        "source_path": str(source_path),
        "status": "pending",
    }

    if dry_run:
        result["status"] = "dry_run"
        print(f"  [DRY RUN] {org}/{repo}: {target_path}")
        return result

    try:
        content = source_path.read_bytes()
    except OSError as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"    ERROR reading {source_path}: {e}")
        return result

    success = put_file(org, repo, target_path, content, f"chore: ingest source material — {source_path.name}", force=force)
    result["status"] = "deployed" if success else "failed"
    return result
