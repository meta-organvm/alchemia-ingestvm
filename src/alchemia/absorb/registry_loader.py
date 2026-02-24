"""Load the registry-v2.json and provide repo lookup."""

import json
import os
from pathlib import Path

REGISTRY_PATH = (
    Path(
        os.environ.get(
            "ORGANVM_CORPUS_DIR",
            str(Path("~/Workspace/meta-organvm/organvm-corpvs-testamentvm").expanduser()),
        )
    )
    / "registry-v2.json"
)


def load_registry(path: Path | None = None) -> dict:
    """Load registry and return structured lookup data.

    Returns dict with:
      - repos: list of {name, org, organ, status, implementation_status}
      - by_name: dict mapping repo name → repo info
      - by_org: dict mapping org name → list of repos
      - archived: set of archived repo names
    """
    path = path or REGISTRY_PATH
    with open(path, encoding="utf-8") as f:
        reg = json.load(f)

    repos = []
    by_name = {}
    by_org = {}
    archived = set()

    for organ_key, organ_data in reg["organs"].items():
        for repo in organ_data.get("repositories", []):
            info = {
                "name": repo["name"],
                "org": repo["org"],
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
