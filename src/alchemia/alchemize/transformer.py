"""File transformation for the ALCHEMIZE stage."""

import re
import shutil
import subprocess
from pathlib import Path

# File handling rules per the plan
DEPLOY_DIRECT = {
    ".md", ".txt", ".py", ".js", ".jsx", ".html", ".yaml", ".yml", ".json",
    ".ts", ".tsx", ".sh", ".css", ".svg", ".astro",
}
CONVERT_DOCX = {".docx"}
DEPLOY_SMALL_BINARY = {".pdf", ".png", ".jpg", ".jpeg", ".gif"}
REFERENCE_ONLY = {".gdoc", ".zip", ".pages", ".numbers", ".plist", ".tar.gz"}

MAX_BINARY_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_SIZE = 2 * 1024 * 1024   # 2MB


def classify_action(entry: dict) -> str:
    """Determine the action for a file: 'deploy', 'convert', 'reference', or 'skip'.

    Returns one of:
      - 'deploy': File can be deployed directly
      - 'convert_docx': .docx → .md conversion needed
      - 'reference': Too large or unsupported format; reference-only in PROVENANCE.yaml
      - 'skip': Duplicate or unclassified; skip entirely
    """
    if entry.get("duplicate"):
        return "skip"

    classification = entry.get("classification", {})
    if classification.get("status") != "CLASSIFIED":
        return "skip"

    ext = entry.get("extension", "").lower()
    size = entry.get("size_bytes", 0)

    if ext in DEPLOY_DIRECT:
        return "deploy"

    if ext in CONVERT_DOCX:
        return "convert_docx"

    if ext in DEPLOY_SMALL_BINARY:
        if ext == ".pdf" and size >= MAX_BINARY_SIZE:
            return "reference"
        if ext in {".png", ".jpg", ".jpeg", ".gif"} and size >= MAX_IMAGE_SIZE:
            return "reference"
        return "deploy"

    if ext in REFERENCE_ONLY:
        return "reference"

    # Unknown extension — if small text file, deploy; otherwise reference
    if size < 100 * 1024:  # <100KB
        return "deploy"
    return "reference"


def sanitize_filename(name: str) -> str:
    """Sanitize filename for GitHub compatibility."""
    # Replace problematic characters
    sanitized = re.sub(r'[|"?*:<>]', "-", name)
    # Collapse multiple dashes
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    # Remove leading/trailing dashes and dots
    sanitized = sanitized.strip("-.")
    return sanitized or "unnamed"


def convert_docx_to_md(source_path: Path, output_dir: Path) -> Path | None:
    """Convert .docx to .md using pandoc. Returns output path or None on failure."""
    if not shutil.which("pandoc"):
        print(f"    WARNING: pandoc not found, cannot convert {source_path.name}")
        return None

    output_path = output_dir / (source_path.stem + ".md")
    try:
        subprocess.run(
            ["pandoc", str(source_path), "-t", "gfm", "-o", str(output_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"    WARNING: pandoc conversion failed for {source_path.name}: {e}")
    return None


def get_deploy_path(entry: dict) -> str:
    """Compute the target path in the repo for this file."""
    classification = entry.get("classification", {})
    subdir = classification.get("target_subdir", "docs/source-materials/theory/")
    filename = sanitize_filename(entry["filename"])
    return f"{subdir}{filename}"
