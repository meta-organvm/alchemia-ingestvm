"""Synthesis Engine — generate creative briefs from accumulated references."""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from alchemia.aesthetic import load_taste, resolve_aesthetic_chain, format_prompt_injection


ORGAN_MAP = {
    "ORGAN-I": {"name": "Theoria", "domain": "Theory, epistemology, recursion, ontology"},
    "ORGAN-II": {"name": "Poiesis", "domain": "Art, generative, performance, experiential"},
    "ORGAN-III": {"name": "Ergon", "domain": "Commerce, SaaS, B2B, B2C products"},
    "ORGAN-IV": {"name": "Taxis", "domain": "Orchestration, governance, routing"},
    "ORGAN-V": {"name": "Logos", "domain": "Public process, essays, building in public"},
    "ORGAN-VI": {"name": "Koinonia", "domain": "Community, salons, reading groups"},
    "ORGAN-VII": {"name": "Kerygma", "domain": "Marketing, POSSE distribution"},
    "META": {"name": "Meta-Organvm", "domain": "Umbrella governance, system-of-systems"},
}


def analyze_references(taste_path: Path | None = None) -> dict:
    """Analyze accumulated references and group by tag clusters.

    Returns dict with:
      - by_tag: {tag: [references]}
      - by_type: {type: [references]}
      - tag_counts: {tag: count}
      - total: int
    """
    taste = load_taste(taste_path)
    refs = taste.get("references", [])

    by_tag = defaultdict(list)
    by_type = defaultdict(list)
    tag_counts = defaultdict(int)

    for ref in refs:
        ref_type = ref.get("type", "unknown")
        by_type[ref_type].append(ref)

        for tag in ref.get("tags", ["uncategorized"]):
            by_tag[tag].append(ref)
            tag_counts[tag] += 1

    return {
        "by_tag": dict(by_tag),
        "by_type": dict(by_type),
        "tag_counts": dict(tag_counts),
        "total": len(refs),
    }


def generate_creative_brief(organ: str, taste_path: Path | None = None) -> str:
    """Generate a creative brief for a specific organ.

    The brief includes:
      1. Organ identity (domain, name)
      2. Resolved aesthetic chain (inherited from taste.yaml)
      3. Relevant references grouped by tag
      4. Typography recommendations
      5. Tone guide
      6. Anti-pattern checklist
    """
    chain = resolve_aesthetic_chain(organ=organ, taste_path=taste_path)
    organ_info = ORGAN_MAP.get(organ, {"name": organ, "domain": ""})
    analysis = analyze_references(taste_path)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Creative Brief: {organ_info['name']} ({organ})",
        "",
        f"> Generated {now} by Alchemia Synthesis Engine",
        f"> Domain: {organ_info['domain']}",
        "",
        "---",
        "",
        "## 1. Identity",
        "",
        f"**Organ:** {organ} — {organ_info['name']}",
        f"**Domain:** {organ_info['domain']}",
        "",
    ]

    # Palette
    palette = chain.get("palette", {})
    if palette:
        lines.extend([
            "## 2. Color Palette",
            "",
            "| Role | Value | Usage |",
            "|------|-------|-------|",
        ])
        for role, value in palette.items():
            lines.append(f"| {role} | `{value}` | {role.replace('_', ' ').title()} |")
        lines.append("")

        mods = chain.get("organ_modifiers", {})
        if mods.get("palette_shift"):
            lines.append(f"**Organ modifier:** {mods['palette_shift']}")
            lines.append("")

    # Typography
    typo = chain.get("typography", {})
    if typo:
        lines.extend([
            "## 3. Typography",
            "",
        ])
        for key, value in typo.items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        mods = chain.get("organ_modifiers", {})
        if mods.get("typography_emphasis"):
            lines.append(f"- **Organ emphasis:** {mods['typography_emphasis']}")
        lines.append("")

    # Tone
    tone = chain.get("tone", {})
    if tone:
        lines.extend([
            "## 4. Tone & Voice",
            "",
        ])
        for key, value in tone.items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        mods = chain.get("organ_modifiers", {})
        if mods.get("tone_shift"):
            lines.append(f"- **Organ shift:** {mods['tone_shift']}")
        lines.append("")

    # Visual language
    visual = chain.get("visual_language", {})
    if visual:
        lines.extend([
            "## 5. Visual Language",
            "",
        ])
        influences = visual.get("influences", [])
        if influences:
            lines.append("**Influences:**")
            for inf in influences:
                lines.append(f"- {inf}")
            lines.append("")
        keywords = visual.get("keywords", [])
        if keywords:
            lines.append(f"**Keywords:** {', '.join(keywords)}")
            lines.append("")
        mods = chain.get("organ_modifiers", {})
        if mods.get("visual_shift"):
            lines.append(f"**Organ visual:** {mods['visual_shift']}")
            lines.append("")

    # References
    refs = chain.get("references", [])
    if refs:
        lines.extend([
            "## 6. Accumulated References",
            "",
            f"Total references: {len(refs)}",
            "",
        ])
        for ref in refs:
            ref_type = ref.get("type", "unknown")
            if ref_type == "url":
                source = ref.get('source', 'URL')
                notes = ref.get('notes', '')
                lines.append(f"- [{source}]({source}) — {notes}")
            elif ref_type == "description":
                lines.append(f"- *\"{ref.get('text', '')}\"* — {ref.get('notes', '')}")
            elif ref_type == "screenshot":
                lines.append(f"- Screenshot: `{ref.get('path', '')}` — {ref.get('notes', '')}")
            tags = ref.get("tags", [])
            if tags:
                lines.append(f"  Tags: {', '.join(tags)}")
        lines.append("")

    # Anti-patterns
    anti = chain.get("anti_patterns", [])
    if anti:
        lines.extend([
            "## 7. Anti-Patterns (AVOID)",
            "",
        ])
        for a in anti:
            lines.append(f"- {a}")
        lines.append("")

    # Prompt injection block
    lines.extend([
        "---",
        "",
        "## Appendix: AI Prompt Injection Block",
        "",
        "Copy this block into AI generation prompts to enforce aesthetic guidelines:",
        "",
        "```markdown",
        format_prompt_injection(chain),
        "```",
    ])

    return "\n".join(lines)


def generate_all_briefs(
    output_dir: Path | None = None,
    taste_path: Path | None = None,
) -> list[Path]:
    """Generate creative briefs for all organs.

    Returns list of output file paths.
    """
    output_dir = output_dir or Path("data/creative-briefs")
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = []
    for organ in ORGAN_MAP:
        brief = generate_creative_brief(organ, taste_path)
        filename = f"creative-brief-{organ.lower().replace('-', '_')}.md"
        out_path = output_dir / filename
        out_path.write_text(brief)
        outputs.append(out_path)
        print(f"  Generated: {out_path}")

    return outputs


def generate_workflow_integration_example() -> str:
    """Generate an example GitHub Actions workflow step that consumes the aesthetic chain.

    This demonstrates how autonomous AI agents would use the taste profile.
    """
    return '''# Example GitHub Actions step: consume the aesthetic chain
# Add this to any workflow that generates content (READMEs, essays, etc.)

- name: Fetch aesthetic chain
  id: aesthetic
  run: |
    # Fetch taste.yaml from alchemia-ingestvm
    TASTE=$(gh api repos/meta-organvm/alchemia-ingestvm/contents/taste.yaml \\
      --jq '.content' | base64 -d)

    # Fetch organ-specific aesthetic
    ORGAN_AESTHETIC=$(gh api repos/${GITHUB_REPOSITORY_OWNER}/.github/contents/organ-aesthetic.yaml \\
      --jq '.content' | base64 -d 2>/dev/null || echo "")

    # Combine into a prompt injection block
    cat > aesthetic-context.md << 'AESTHETIC_EOF'
    ## Aesthetic Guidelines (from taste.yaml)

    ### Tone
    $(echo "$TASTE" | yq '.tone')

    ### Anti-Patterns
    $(echo "$TASTE" | yq '.anti_patterns[]' | sed 's/^/- /')

    ### Organ Modifiers
    $(echo "$ORGAN_AESTHETIC" | yq '.modifiers' 2>/dev/null || echo "None")
    AESTHETIC_EOF

- name: Generate content with aesthetic constraints
  run: |
    # Include aesthetic-context.md in the AI prompt
    cat aesthetic-context.md >> generation-prompt.md
    # ... rest of generation logic
'''
