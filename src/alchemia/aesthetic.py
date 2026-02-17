"""Aesthetic Nervous System — taste.yaml management and capture."""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

TASTE_PATH = Path(__file__).parent.parent.parent / "taste.yaml"


def load_taste(path: Path | None = None) -> dict:
    """Load the taste.yaml file."""
    path = path or TASTE_PATH
    with open(path) as f:
        return yaml.safe_load(f)


def save_taste(data: dict, path: Path | None = None) -> None:
    """Save the taste.yaml file, preserving comments via backup-and-write."""
    path = path or TASTE_PATH
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def add_reference(
    ref_type: str,
    value: str,
    tags: list[str] | None = None,
    notes: str = "",
    path: Path | None = None,
) -> dict:
    """Add a reference to taste.yaml.

    Args:
        ref_type: "url", "screenshot", "note", or "description"
        value: URL string, file path, or note text
        tags: List of tags for categorization
        notes: Additional notes about why this reference matters
        path: Override taste.yaml path
    """
    taste = load_taste(path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = {
        "type": ref_type,
        "tags": tags or ["uncategorized"],
        "notes": notes,
        "captured": now,
    }

    if ref_type == "url":
        entry["source"] = value
    elif ref_type == "screenshot":
        # Copy to inspirations/ directory
        source = Path(value).expanduser()
        if source.exists():
            dest_dir = (path or TASTE_PATH).parent / "inspirations"
            dest_dir.mkdir(exist_ok=True)
            dest = dest_dir / source.name
            if not dest.exists():
                shutil.copy2(source, dest)
            entry["path"] = f"inspirations/{source.name}"
        else:
            entry["path"] = value
    elif ref_type in ("note", "description"):
        entry["type"] = "description"
        entry["text"] = value

    if taste.get("references") is None:
        taste["references"] = []
    taste["references"].append(entry)
    save_taste(taste, path)

    return entry


def resolve_aesthetic_chain(
    organ: str | None = None,
    repo: str | None = None,
    taste_path: Path | None = None,
    organ_aesthetics_dir: Path | None = None,
) -> dict:
    """Resolve the full cascading aesthetic chain.

    Returns a merged dict: taste.yaml ← organ-aesthetic.yaml ← repo-aesthetic.yaml
    """
    taste = load_taste(taste_path)

    result = {
        "palette": taste.get("palette", {}),
        "typography": taste.get("typography", {}),
        "tone": taste.get("tone", {}),
        "visual_language": taste.get("visual_language", {}),
        "anti_patterns": taste.get("anti_patterns", []),
        "references": taste.get("references", []),
    }

    # Layer organ aesthetic
    if organ:
        default_dir = (taste_path or TASTE_PATH).parent / "data" / "organ-aesthetics"
        organ_dir = organ_aesthetics_dir or default_dir
        organ_map = {
            "ORGAN-I": "organ-i-theoria.yaml",
            "ORGAN-II": "organ-ii-poiesis.yaml",
            "ORGAN-III": "organ-iii-ergon.yaml",
            "ORGAN-IV": "organ-iv-taxis.yaml",
            "ORGAN-V": "organ-v-logos.yaml",
            "ORGAN-VI": "organ-vi-koinonia.yaml",
            "ORGAN-VII": "organ-vii-kerygma.yaml",
            "META": "organ-meta.yaml",
        }
        organ_file = organ_dir / organ_map.get(organ, "")
        if organ_file.exists():
            with open(organ_file) as f:
                organ_data = yaml.safe_load(f)
            result["organ_modifiers"] = organ_data.get("modifiers", {})
            result["organ_name"] = organ_data.get("name", "")
            result["references"].extend(organ_data.get("specific_references", []))

    return result


def format_prompt_injection(chain: dict) -> str:
    """Format the resolved aesthetic chain as an AI prompt injection block.

    This is what gets inserted into AI generation prompts to enforce
    the aesthetic DNA on generated content.
    """
    lines = ["## Aesthetic Guidelines (MANDATORY)"]
    lines.append("")

    tone = chain.get("tone", {})
    if tone:
        lines.append(f"**Voice:** {tone.get('voice', 'professional')}")
        lines.append(f"**Register:** {tone.get('register', 'standard')}")
        lines.append(f"**Density:** {tone.get('density', 'moderate')}")
        if tone.get("first_person"):
            lines.append(f"**First person:** {tone['first_person']}")
        lines.append("")

    mods = chain.get("organ_modifiers", {})
    if mods:
        lines.append(f"**Organ:** {chain.get('organ_name', 'Unknown')}")
        if mods.get("tone_shift"):
            lines.append(f"**Tone shift:** {mods['tone_shift']}")
        if mods.get("typography_emphasis"):
            lines.append(f"**Typography:** {mods['typography_emphasis']}")
        if mods.get("visual_shift"):
            lines.append(f"**Visual:** {mods['visual_shift']}")
        lines.append("")

    anti = chain.get("anti_patterns", [])
    if anti:
        lines.append("**AVOID:**")
        for a in anti:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines)
