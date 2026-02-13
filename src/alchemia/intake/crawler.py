"""INTAKE Stage — Crawl source directories and fingerprint every file."""

import hashlib
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path

# Directories to skip during crawl
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "venv",
    ".egg-info",
    "dist",
    "build",
    ".DS_Store",
    ".Trash",
    ".Spotlight-V100",
    ".fseventsd",
}

# Top-level workspace directories to skip entirely (SDKs, tool installs, self-reference)
SKIP_TOPLEVEL = {
    "google-cloud-sdk",
    "alchemia-ingestvm",
}

# File patterns to skip
SKIP_FILES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".gitkeep",
}


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file using chunked reads."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
    except (OSError, PermissionError):
        return "ERROR_UNREADABLE"
    return h.hexdigest()


def file_metadata(path: Path, root_dir: Path) -> dict:
    """Gather metadata for a single file."""
    stat = path.stat()
    ext = path.suffix.lower()
    mime_type, _ = mimetypes.guess_type(str(path))

    return {
        "path": str(path),
        "relative_path": str(path.relative_to(root_dir)),
        "source_dir": str(root_dir),
        "filename": path.name,
        "extension": ext,
        "mime_type": mime_type or "application/octet-stream",
        "size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "sha256": sha256_file(path),
        "parent_dir": path.parent.name,
        "depth": len(path.relative_to(root_dir).parts) - 1,
    }


def crawl(source_dirs: list[Path]) -> list[dict]:
    """Crawl all source directories and return file metadata entries."""
    entries = []
    seen_paths = set()

    for root_dir in source_dirs:
        root_dir = root_dir.expanduser().resolve()
        if not root_dir.exists():
            print(f"  WARNING: Source dir does not exist: {root_dir}")
            continue
        if not root_dir.is_dir():
            print(f"  WARNING: Not a directory: {root_dir}")
            continue

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Prune skippable directories in-place
            dp = Path(dirpath)
            is_toplevel = dp == root_dir
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS
                and not d.startswith(".")
                and not (is_toplevel and d in SKIP_TOPLEVEL)
            ]

            for fname in filenames:
                if fname in SKIP_FILES:
                    continue

                fpath = Path(dirpath) / fname
                resolved = fpath.resolve()

                # Skip symlinks and already-seen files
                if fpath.is_symlink() or str(resolved) in seen_paths:
                    continue
                seen_paths.add(str(resolved))

                try:
                    entry = file_metadata(fpath, root_dir)
                    entries.append(entry)
                except (OSError, PermissionError) as e:
                    print(f"  WARNING: Cannot read {fpath}: {e}")

    return entries
