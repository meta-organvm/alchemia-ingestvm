"""Load the registry-v2.json and provide repo lookup.

ISOTOPE DISSOLUTION: This module previously reimplemented registry loading
independently from organvm-engine. It now imports from the canonical source
when available, falling back to a minimal standalone loader when the engine
is not installed. The standalone fallback preserves alchemia's ability to
run independently, while the import path eliminates the isotope.

Gate: skeletal--define G1 (CANONICAL_REGISTRY)
Gate: respiratory--ingest G1 (ISOTOPES_DISSOLVED)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

REGISTRY_PATH = (
    Path(
        os.environ.get(
            "ORGANVM_CORPUS_DIR",
            str(Path("~/Workspace/meta-organvm/organvm-corpvs-testamentvm").expanduser()),
        ),
    )
    / "registry-v2.json"
)


def _load_raw(path: Path | None = None) -> dict:
    """Load raw registry JSON — canonical source or standalone fallback."""
    try:
        from organvm_engine.registry.loader import load_registry as _engine_load

        return _engine_load(path)
    except ImportError:
        # Standalone fallback — alchemia can run without the engine installed
        path = path or REGISTRY_PATH
        with Path(path).open(encoding="utf-8") as f:
            return json.load(f)


def load_registry(path: Path | None = None) -> dict:
    """Load registry and return structured lookup data.

    Returns dict with:
      - repos: list of {name, org, organ, status, implementation_status}
      - by_name: dict mapping repo name → repo info
      - by_org: dict mapping org name → list of repos
      - archived: set of archived repo names
    """
    reg = _load_raw(path)

    repos = []
    by_name = {}
    by_org = {}
    archived = set()

    for organ_key, organ_data in reg.get("organs", {}).items():
        for repo in organ_data.get("repositories", []):
            info = {
                "name": repo["name"],
                "org": repo.get("org", ""),
                "organ": organ_key,
                "status": repo.get("status", ""),
                "implementation_status": repo.get("implementation_status", ""),
                "description": repo.get("description", ""),
            }
            repos.append(info)
            by_name[repo["name"]] = info
            by_org.setdefault(repo["org"], []).append(info)

            if repo.get("status") == "ARCHIVED":
                archived.add(repo["name"])

    return {
        "repos": repos,
        "by_name": by_name,
        "by_org": by_org,
        "archived": archived,
    }
