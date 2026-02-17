"""ABSORB Stage — Classify files to target organ/org/repo using 7 priority rules."""

from pathlib import Path

from alchemia.absorb.name_variants import (
    DIR_TO_ORGAN,
    INSORT_TARGET,
    MET4_TARGET,
    NAME_VARIANTS,
    PROCESS_CONTAINER_TARGET,
    STAGING_DIR_TO_ORG,
)
from alchemia.absorb.registry_loader import load_registry

# Organ-level keyword patterns for Rule 6 (content-keyword heuristic)
ORGAN_KEYWORDS = {
    "ORGAN-I": {
        "keywords": [
            "epistemology", "recursive", "ontology", "ontological", "noumenon",
            "phenomenology", "symbolic", "recursion", "axiom", "morphe",
            "dialectic", "teleology", "hermeneutic", "formal logic",
        ],
        "org": "organvm-i-theoria",
    },
    "ORGAN-II": {
        "keywords": [
            "generative art", "performance", "experiential", "dromenon",
            "ritual", "aesthetic", "creative coding", "visual art",
            "composition", "soundscape", "immersive", "mavs", "olevm",
        ],
        "org": "organvm-ii-poiesis",
    },
    "ORGAN-III": {
        "keywords": [
            "saas", "b2b", "b2c", "product", "revenue", "pricing",
            "customer", "subscription", "commerce", "marketplace",
            "startup", "business model", "monetization",
        ],
        "org": "organvm-iii-ergon",
    },
    "ORGAN-IV": {
        "keywords": [
            "orchestration", "governance", "routing", "workflow",
            "ci/cd", "pipeline", "automation", "dispatch", "agent",
        ],
        "org": "organvm-iv-taxis",
    },
    "ORGAN-V": {
        "keywords": [
            "essay", "blog", "public process", "building in public",
            "writing", "publication", "meta-commentary",
        ],
        "org": "organvm-v-logos",
    },
    "ORGAN-VI": {
        "keywords": [
            "community", "salon", "reading group", "discussion",
            "forum", "collective", "gathering",
        ],
        "org": "organvm-vi-koinonia",
    },
    "ORGAN-VII": {
        "keywords": [
            "marketing", "posse", "distribution", "announcement",
            "social media", "newsletter", "outreach",
        ],
        "org": "organvm-vii-kerygma",
    },
}

# Map manifest categories to organs
MANIFEST_CATEGORY_TO_ORGAN = {
    "strategic & governance": "ORGAN-IV",
    "technical specifications": "ORGAN-I",
    "creative & artistic": "ORGAN-II",
    "pedagogical & educational": "ORGAN-VI",
    "commercial & product": "ORGAN-III",
    "public process & essays": "ORGAN-V",
    "marketing & distribution": "ORGAN-VII",
    "meta-system & infrastructure": "ORGAN-IV",
}

# File extension → subdirectory mapping within docs/source-materials/
EXT_TO_SUBDIR = {
    ".md": "theory",
    ".txt": "theory",
    ".py": "prototypes",
    ".js": "prototypes",
    ".jsx": "prototypes",
    ".ts": "prototypes",
    ".tsx": "prototypes",
    ".html": "prototypes",
    ".yaml": "specs",
    ".yml": "specs",
    ".json": "specs",
    ".pdf": "research",
    ".docx": "theory",
    ".gdoc": "theory",
}


def _get_toplevel_dir(entry: dict) -> str:
    """Get the top-level workspace directory name from a file path."""
    parts = Path(entry["path"]).parts
    try:
        ws_idx = parts.index("Workspace")
        if ws_idx + 1 < len(parts):
            return parts[ws_idx + 1]
    except ValueError:
        pass
    return ""


def _subdir_for_ext(ext: str) -> str:
    """Determine the target subdirectory based on file extension."""
    return EXT_TO_SUBDIR.get(ext, "theory")


def _read_first_lines(path: str, n: int = 50) -> str:
    """Read first N lines of a text file for keyword scanning."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= n:
                    break
                lines.append(line)
            return "\n".join(lines).lower()
    except (OSError, UnicodeDecodeError):
        return ""


def classify_entry(entry: dict, registry: dict) -> dict:
    """Classify a single inventory entry using the 7-rule priority chain.

    Returns a classification dict with:
      - rule: which rule matched (1-7)
      - rule_name: human-readable rule name
      - confidence: 0.0-1.0
      - target_organ: e.g. "ORGAN-I"
      - target_org: e.g. "organvm-i-theoria"
      - target_repo: specific repo name or None
      - target_subdir: e.g. "docs/source-materials/theory/"
      - status: "CLASSIFIED" or "PENDING_REVIEW"
    """
    toplevel = _get_toplevel_dir(entry)
    by_name = registry["by_name"]
    ext = entry.get("extension", "")
    subdir = _subdir_for_ext(ext)

    # Rule 1: Direct repo match — parent dir name matches a registry repo
    if toplevel in by_name:
        repo_info = by_name[toplevel]
        return {
            "rule": 1,
            "rule_name": "direct_repo_match",
            "confidence": 1.0,
            "target_organ": repo_info["organ"],
            "target_org": repo_info["org"],
            "target_repo": repo_info["name"],
            "target_subdir": f"docs/source-materials/{subdir}/",
            "status": "CLASSIFIED",
        }

    # Rule 2: Name-variant match — known discrepancy table
    variant_name = NAME_VARIANTS.get(toplevel)
    if variant_name and variant_name in by_name:
        repo_info = by_name[variant_name]
        return {
            "rule": 2,
            "rule_name": "name_variant_match",
            "confidence": 0.95,
            "target_organ": repo_info["organ"],
            "target_org": repo_info["org"],
            "target_repo": repo_info["name"],
            "target_subdir": f"docs/source-materials/{subdir}/",
            "status": "CLASSIFIED",
        }

    # Rule 3: Staging dir match — ORG-{N}-*-staging/ pattern
    staging_org = STAGING_DIR_TO_ORG.get(toplevel)
    if staging_org:
        organ_map = {
            "organvm-iv-taxis": "ORGAN-IV",
            "organvm-v-logos": "ORGAN-V",
            "organvm-vi-koinonia": "ORGAN-VI",
            "organvm-vii-kerygma": "ORGAN-VII",
        }
        return {
            "rule": 3,
            "rule_name": "staging_dir_match",
            "confidence": 0.9,
            "target_organ": organ_map.get(staging_org, ""),
            "target_org": staging_org,
            "target_repo": None,  # needs manual routing to specific repo
            "target_subdir": f"docs/source-materials/{subdir}/",
            "status": "CLASSIFIED",
        }

    # Rule 3b: Directory-to-organ bulk routing (non-repo directories)
    organ_dir = DIR_TO_ORGAN.get(toplevel)
    if organ_dir:
        return {
            "rule": 3,
            "rule_name": "dir_to_organ",
            "confidence": 0.75,
            "target_organ": organ_dir["organ"],
            "target_org": organ_dir["org"],
            "target_repo": None,
            "target_subdir": f"docs/source-materials/{subdir}/",
            "status": "CLASSIFIED",
        }

    # Rule 4: processCONTAINER / inSORT / MET4 — specialized intake subdirs
    rel_path = entry.get("relative_path", "")
    file_path = entry.get("path", "")
    if "processCONTAINER" in rel_path or "processCONTAINER" in file_path:
        return {
            "rule": 4,
            "rule_name": "process_container",
            "confidence": 0.85,
            "target_organ": "ORGAN-I",
            "target_org": PROCESS_CONTAINER_TARGET["org"],
            "target_repo": PROCESS_CONTAINER_TARGET["repo"],
            "target_subdir": "docs/source-materials/specs/",
            "status": "CLASSIFIED",
        }
    if "inSORT" in rel_path or "inSORT" in file_path:
        return {
            "rule": 4,
            "rule_name": "insort_routing",
            "confidence": 0.8,
            "target_organ": "ORGAN-I",
            "target_org": INSORT_TARGET["org"],
            "target_repo": INSORT_TARGET["repo"],
            "target_subdir": "docs/source-materials/specs/",
            "status": "CLASSIFIED",
        }
    if "MET4" in rel_path or "MET4_Fuse" in file_path:
        return {
            "rule": 4,
            "rule_name": "met4_routing",
            "confidence": 0.8,
            "target_organ": MET4_TARGET["organ"],
            "target_org": MET4_TARGET["org"],
            "target_repo": None,
            "target_subdir": f"docs/source-materials/{subdir}/",
            "status": "CLASSIFIED",
        }

    # Rule 5: MANIFEST_INDEX_TABLE — CSV category + tags lookup
    manifest = entry.get("manifest")
    if manifest and manifest.get("manifest_category"):
        category = manifest["manifest_category"].lower().strip()
        for cat_prefix, organ in MANIFEST_CATEGORY_TO_ORGAN.items():
            if cat_prefix in category:
                organ_info = ORGAN_KEYWORDS.get(organ, {})
                return {
                    "rule": 5,
                    "rule_name": "manifest_category",
                    "confidence": 0.8,
                    "target_organ": organ,
                    "target_org": organ_info.get("org", ""),
                    "target_repo": None,
                    "target_subdir": f"docs/source-materials/{subdir}/",
                    "status": "CLASSIFIED",
                }

    # Rule 6: Content-keyword heuristic — scan first lines for organ keywords
    text_extensions = {".md", ".txt", ".py", ".js", ".ts", ".html", ".yaml", ".yml", ".json"}
    if ext in text_extensions:
        content = _read_first_lines(entry["path"])
        if content:
            best_organ = None
            best_score = 0
            for organ, kw_info in ORGAN_KEYWORDS.items():
                score = sum(1 for kw in kw_info["keywords"] if kw in content)
                if score > best_score:
                    best_score = score
                    best_organ = organ

            if best_organ and best_score >= 2:
                organ_info = ORGAN_KEYWORDS[best_organ]
                confidence = min(0.5 + best_score * 0.1, 0.85)
                return {
                    "rule": 6,
                    "rule_name": "content_keyword",
                    "confidence": confidence,
                    "target_organ": best_organ,
                    "target_org": organ_info["org"],
                    "target_repo": None,
                    "target_subdir": f"docs/source-materials/{subdir}/",
                    "status": "CLASSIFIED",
                }

    # Rule 7: Unresolved — flag for human review
    return {
        "rule": 7,
        "rule_name": "unresolved",
        "confidence": 0.0,
        "target_organ": None,
        "target_org": None,
        "target_repo": None,
        "target_subdir": None,
        "status": "PENDING_REVIEW",
    }


def classify_all(entries: list[dict], registry: dict | None = None) -> list[dict]:
    """Classify all inventory entries. Returns entries with 'classification' field added."""
    if registry is None:
        registry = load_registry()

    stats = {i: 0 for i in range(1, 8)}
    for entry in entries:
        classification = classify_entry(entry, registry)
        entry["classification"] = classification
        stats[classification["rule"]] += 1

    rule_names = {
        1: "direct_repo_match",
        2: "name_variant_match",
        3: "staging_dir_match",
        4: "process_container",
        5: "manifest_category",
        6: "content_keyword",
        7: "unresolved",
    }

    print("  Classification results:")
    for rule_num, count in sorted(stats.items()):
        print(f"    Rule {rule_num} ({rule_names[rule_num]}): {count}")

    classified = sum(v for k, v in stats.items() if k < 7)
    total = len(entries)
    pct = (classified / total * 100) if total else 0
    print(f"  Classified: {classified}/{total} ({pct:.1f}%)")
    print(f"  Pending review: {stats[7]}")

    return entries
