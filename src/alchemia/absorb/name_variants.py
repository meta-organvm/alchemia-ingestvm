"""Name-variant mapping for directories that don't exactly match registry repo names."""

# workspace_dir_name → registry_repo_name
NAME_VARIANTS = {
    "hokage-chess--believe-it!": "hokage-chess",
    "knowledge-base": "my-knowledge-base",
    "your--fit-tailored": "your-fit-tailored",
    "auto-rev-epistemic-engine_spec": "auto-revision-epistemic-engine",
    "metasystem-core": "metasystem-master",
    "shared-rememberance-gateway": "shared-remembrance-gateway",
    "portfolio": "showcase-portfolio",
}

# Staging dir pattern: ORG-{roman}-*-staging → organ org name
STAGING_DIR_TO_ORG = {
    "ORG-IV-orchestration-staging": "organvm-iv-taxis",
    "ORG-V-public-process-staging": "organvm-v-logos",
    "ORG-VI-community-staging": "organvm-vi-koinonia",
    "ORG-VII-marketing-staging": "organvm-vii-kerygma",
}

# processCONTAINER files → target repo
PROCESS_CONTAINER_TARGET = {
    "org": "organvm-i-theoria",
    "repo": "recursive-engine--generative-entity",
}

# Directories that map to an organ but not a specific repo
# These are bulk-routing rules for directories not in the registry
DIR_TO_ORGAN = {
    "OS-me": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "Personal OS/meta-system workspace → orchestration organ",
    },
    "omni-dromenon-machina": {
        "organ": "ORGAN-II",
        "org": "organvm-ii-poiesis",
        "reason": "Performance engine (not in registry) → art/performance organ",
    },
    "omni-dromenon-machina.BACKUP-20260207": {
        "organ": "ORGAN-II",
        "org": "organvm-ii-poiesis",
        "reason": "Backup of performance engine → art/performance organ",
    },
    "JST_": {
        "organ": "ORGAN-VII",
        "org": "organvm-vii-kerygma",
        "reason": "Social media/marketing content → marketing organ",
    },
    "4444J99": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "Personal account workspace → meta/orchestration organ",
    },
    "4444JPP": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "Personal account workspace → meta/orchestration organ",
    },
    "organvm-pactvm": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "Planning workspace → orchestration organ",
    },
    "mcp-servers": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "MCP server configs → orchestration/tooling organ",
    },
    "cloudbase-mcp": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "Cloud MCP tooling → orchestration organ",
    },
    "src": {
        "organ": "ORGAN-I",
        "org": "organvm-i-theoria",
        "reason": "Loose source files → theory organ (default)",
    },
    "self-patent-fulfillment": {
        "organ": "ORGAN-I",
        "org": "organvm-i-theoria",
        "reason": "Self-patent concept → theory organ",
    },
    "Projects": {
        "organ": "ORGAN-IV",
        "org": "organvm-iv-taxis",
        "reason": "General projects folder → orchestration organ",
    },
}

# inSORT subdirectory → RE:GE subsystem routing (like processCONTAINER)
INSORT_TARGET = {
    "org": "organvm-i-theoria",
    "repo": "recursive-engine--generative-entity",
}

# MET4 subdirectory → meta-system routing
MET4_TARGET = {
    "organ": "ORGAN-I",
    "org": "organvm-i-theoria",
    "reason": "MET4 Fuse-Transform-Symbiote → theory/meta organ",
}


def resolve_variant(dir_name: str) -> str | None:
    """Return the canonical registry repo name for a known variant, or None."""
    return NAME_VARIANTS.get(dir_name)


def resolve_staging(dir_name: str) -> str | None:
    """Return the target org name for a staging directory, or None."""
    return STAGING_DIR_TO_ORG.get(dir_name)


def resolve_organ_dir(dir_name: str) -> dict | None:
    """Return organ routing info for a non-repo directory, or None."""
    return DIR_TO_ORGAN.get(dir_name)
