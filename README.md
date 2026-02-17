# Alchemia Ingestvm

**The Alchemical Forge — Material ingestion pipeline and aesthetic nervous system for the eight-organ creative-institutional system.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Organ: Meta](https://img.shields.io/badge/organ-Meta-purple)](https://github.com/meta-organvm)

Alchemia is the ingestion engine that absorbs raw creative material — documents, code prototypes, screenshots, bookmarks, notes — classifies each file to its target organ and repository, and deploys it with full provenance tracking. It also maintains the **aesthetic nervous system**: a cascading `taste.yaml` → organ-aesthetic → repository-aesthetic chain that enforces visual and tonal DNA across all AI-generated content in the system.

---

## Table of Contents

- [Architecture](#architecture)
- [The Three-Stage Pipeline](#the-three-stage-pipeline)
- [Aesthetic Nervous System](#aesthetic-nervous-system)
- [Capture Channels](#capture-channels)
- [Module Reference](#module-reference)
- [CLI Usage](#cli-usage)
- [Data Directories](#data-directories)
- [Configuration](#configuration)
- [Development](#development)

---

## Architecture

Alchemia operates as a three-stage pipeline with a parallel aesthetic subsystem:

```
                    ┌──────────────────────────────────────────┐
                    │           CAPTURE CHANNELS               │
                    │  Bookmarks · Apple Notes · Google Docs   │
                    │  AI Chat Transcripts · Screenshots       │
                    └────────────────┬─────────────────────────┘
                                     │
                    ┌────────────────▼─────────────────────────┐
                    │           STAGE 1: INTAKE                │
                    │  Crawl directories · SHA-256 fingerprint │
                    │  Detect duplicates · Enrich from manifest│
                    │  Output: intake-inventory.json           │
                    └────────────────┬─────────────────────────┘
                                     │
                    ┌────────────────▼─────────────────────────┐
                    │           STAGE 2: ABSORB                │
                    │  7-rule priority classification chain     │
                    │  Map files → organ/org/repo              │
                    │  Output: absorb-mapping.json             │
                    └────────────────┬─────────────────────────┘
                                     │
                    ┌────────────────▼─────────────────────────┐
                    │          STAGE 3: ALCHEMIZE              │
                    │  Transform (docx→md) · Deploy via GitHub │
                    │  Contents API · Batch deployment         │
                    │  Output: provenance-registry.json        │
                    └──────────────────────────────────────────┘

    AESTHETIC NERVOUS SYSTEM (parallel)
    ┌──────────────────────────────────────────────────────────┐
    │  taste.yaml ← organ-aesthetics/*.yaml ← repo overrides  │
    │  Cascading palette/tone/typography/anti-patterns          │
    │  Creative briefs per organ · AI prompt injection blocks   │
    └──────────────────────────────────────────────────────────┘
```

The pipeline reads from `~/Workspace/` source directories, classifies every file to one of the eight organs and their specific repositories, and deploys via the GitHub Contents API. The aesthetic system runs in parallel, providing style guidance to any AI agent generating content across the system.

---

## The Three-Stage Pipeline

### Stage 1: INTAKE

**Command:** `alchemia intake`

Crawls configured source directories and builds a fingerprinted inventory of every file:

- **Directory walking** with intelligent pruning (skips `.git`, `node_modules`, `__pycache__`, `.venv`, etc.)
- **SHA-256 fingerprinting** for deduplication and provenance tracking
- **Metadata extraction**: file size, MIME type, extension, modification time, directory depth
- **Manifest enrichment**: cross-references with `MANIFEST_INDEX_TABLE.csv` for pre-existing category metadata
- **Sidecar enrichment**: reads `.meta.json` files alongside source files for additional context
- **Duplicate detection**: marks files with matching SHA-256 hashes

Output: `data/intake-inventory.json` (schema v1.0)

### Stage 2: ABSORB

**Command:** `alchemia absorb`

Classifies each inventory entry to a target organ, organization, and repository using a 7-rule priority chain:

| Priority | Rule | Confidence | Description |
|----------|------|-----------|-------------|
| 1 | Direct repo match | 1.0 | Parent directory name matches a registry-v2.json repo |
| 2 | Name-variant match | 0.95 | Known naming discrepancy (e.g., `hokage-chess--believe-it!` → `hokage-chess`) |
| 3 | Staging dir / bulk routing | 0.75–0.9 | `ORG-{N}-*-staging/` directories or known non-repo directories |
| 4 | Special containers | 0.8–0.85 | `processCONTAINER`, `inSORT`, `MET4` subdirectories |
| 5 | Manifest category | 0.8 | CSV category lookup (strategic → ORGAN-IV, commercial → ORGAN-III, etc.) |
| 6 | Content keywords | 0.5–0.85 | Scan first 50 lines for organ-specific keyword clusters (2+ keyword threshold) |
| 7 | Unresolved | 0.0 | Flagged for human review (`PENDING_REVIEW`) |

The classification chain is designed so that high-confidence structural rules fire first, with increasingly heuristic rules as fallback. Registry-v2.json (from `organvm-corpvs-testamentvm`) provides the canonical repo list.

Output: `data/absorb-mapping.json` (schema v1.0)

### Stage 3: ALCHEMIZE

**Command:** `alchemia alchemize`

Transforms and deploys classified files to their target repositories:

- **Deployment planning**: groups files by target repo, separates into deploy/convert/reference/skip buckets
- **File transformation**: converts `.docx` → `.md` via pandoc, sanitizes filenames for GitHub compatibility
- **Batch deployment**: pushes files via the GitHub Contents API using `gh api` with stdin piping (avoids `ARG_MAX` limits on large files)
- **Provenance generation**: creates `PROVENANCE.yaml` per repo (source paths, SHA-256, classification metadata) and `provenance-registry.json` (bidirectional source↔repo mapping)
- **Safety features**: skips archived repos, respects branch protection, supports `--dry-run` and organ/repo filters

Output: `data/provenance-registry.json` (schema v1.0)

---

## Aesthetic Nervous System

The aesthetic subsystem maintains visual and tonal consistency across the entire organ system by defining a cascading style chain:

### taste.yaml (System Root)

The root aesthetic file defines system-wide DNA:

- **Palette**: primary, secondary, accent, background, text, muted colors
- **Typography**: heading/body/code font families, weight preferences, letter spacing
- **Tone**: voice (cerebral but accessible), register (elevated without pretension), density (rich, layered), pacing (deliberate, unhurried)
- **Visual language**: influences (Tufte, Rams, Brutalist web, academic typography, terminal aesthetics)
- **Anti-patterns**: explicitly banned visual patterns (stock photography, startup gradients, emoji-heavy communication, default Bootstrap/Tailwind, pastel SaaS palettes)
- **References**: accumulated aesthetic captures (URLs, screenshots, notes) with tags and dates

### Organ Aesthetics (`data/organ-aesthetics/`)

Each organ has a YAML file with modifiers that layer on top of `taste.yaml`:

- `organ-i-theoria.yaml` — Formal, mathematical, high density
- `organ-ii-poiesis.yaml` — Expressive, visual, experimental
- `organ-iii-ergon.yaml` — Product-focused, conversion-oriented
- `organ-iv-taxis.yaml` — Systematic, diagrammatic, precise
- `organ-v-logos.yaml` — Essay-quality, narrative, personal voice
- `organ-vi-koinonia.yaml` — Warm, inviting, community-focused
- `organ-vii-kerygma.yaml` — Bold, outward-facing, promotional
- `organ-meta.yaml` — Architectural, holistic, meta-systemic

### Creative Briefs (`data/creative-briefs/`)

**Command:** `alchemia synthesize`

Generates per-organ creative briefs that combine the resolved aesthetic chain with accumulated references. Each brief includes identity, palette, typography, tone, visual language, references, anti-patterns, and an **AI prompt injection block** — a formatted text block that can be inserted directly into AI generation prompts to enforce the aesthetic DNA.

### Aesthetic Resolution

```python
resolve_aesthetic_chain(organ="ORGAN-II")
# Returns: taste.yaml merged with organ-ii-poiesis.yaml modifiers
# Includes: palette, typography, tone, visual_language, anti_patterns, references
```

The `format_prompt_injection()` function converts a resolved chain into a markdown block suitable for inserting into any AI prompt — this is how the aesthetic system propagates to content generation workflows.

---

## Capture Channels

Alchemia provides multiple ingestion channels for capturing aesthetic references and source material:

### Bookmarks (`channels/bookmarks.py`)

Reads browser bookmark exports and extracts URLs from an "Inspirations" folder. Synced via `alchemia sync`.

### Apple Notes (`channels/apple_notes.py`)

Exports notes from an "Alchemia" folder in Apple Notes via AppleScript/JXA. Captures note titles, body text, and metadata.

### Google Docs (`channels/google_docs.py`)

Full OAuth2 integration with Google Drive. Syncs documents from an "Alchemia" folder, tracking document state (synced, up-to-date, failed). Requires separate authentication via `alchemia gdocs-auth`.

### AI Chat Transcripts (`channels/ai_chats.py`)

Parses Gemini visit files from the intake directory. Captures conversation threads that may contain creative direction or aesthetic references.

### Screenshot Watcher (`agents/com.alchemia.screenshot-watcher.plist`)

A macOS launchd agent that monitors for screenshots and auto-captures them as aesthetic references. Installed via `scripts/install-agents.sh`.

---

## Module Reference

### `alchemia.intake`

| Module | Purpose |
|--------|---------|
| `crawler.py` | Directory walker with SHA-256 fingerprinting, duplicate detection, skip-list pruning |
| `dedup.py` | Mark duplicate files based on SHA-256 hash matching |
| `manifest_loader.py` | Enrich inventory from MANIFEST_INDEX_TABLE.csv and .meta.json sidecars |

### `alchemia.absorb`

| Module | Purpose |
|--------|---------|
| `classifier.py` | 7-rule priority classification chain mapping files → organs/repos |
| `registry_loader.py` | Load and index registry-v2.json for repo lookups |
| `name_variants.py` | Known naming discrepancies, staging-dir mappings, bulk-routing rules |

### `alchemia.alchemize`

| Module | Purpose |
|--------|---------|
| `transformer.py` | File action classification (deploy/convert/reference/skip), filename sanitization, docx→md conversion |
| `deployer.py` | Single-file deployment via GitHub Contents API with SHA tracking |
| `batch_deployer.py` | Multi-file batch deployment with sub-batching, archived-repo skipping |
| `provenance.py` | PROVENANCE.yaml generation, bidirectional provenance registry, deployment planning |

### `alchemia.channels`

| Module | Purpose |
|--------|---------|
| `bookmarks.py` | Browser bookmark sync from Inspirations folder |
| `apple_notes.py` | Apple Notes export via AppleScript/JXA |
| `google_docs.py` | Google Docs OAuth2 sync from Alchemia folder |
| `ai_chats.py` | Gemini visit transcript parsing |

### `alchemia.aesthetic`

Taste profile management — load/save `taste.yaml`, add references, resolve cascading aesthetic chains, format AI prompt injection blocks.

### `alchemia.synthesize`

Creative brief generation engine — analyzes references, generates per-organ briefs with palette/typography/tone/visual-language/anti-patterns, produces workflow integration examples.

---

## CLI Usage

```bash
# Install
pip install -e ".[dev]"

# Full pipeline
alchemia intake                          # Crawl source dirs → intake-inventory.json
alchemia absorb                          # Classify → absorb-mapping.json
alchemia alchemize --dry-run             # Preview deployment plan
alchemia alchemize                       # Deploy to GitHub repos
alchemia alchemize --organ III --repo life  # Filter by organ/repo

# Aesthetic system
alchemia capture --type url "https://example.com" --tags "brutalist,typography"
alchemia capture --type screenshot ~/Desktop/reference.png --tags "palette"
alchemia sync                            # Sync all capture channels
alchemia synthesize                      # Generate creative briefs

# Google Docs integration
alchemia gdocs-auth                      # OAuth2 consent flow
alchemia gdocs-status                    # Check integration status

# Status
alchemia status                          # Pipeline data summary
```

---

## Data Directories

```
data/
  intake-inventory.json      # Stage 1 output: all crawled files with fingerprints
  absorb-mapping.json        # Stage 2 output: classified files with organ targets
  provenance-registry.json   # Stage 3 output: bidirectional source↔repo mapping
  creative-briefs/           # Synthesized creative briefs per organ
    creative-brief-organ_i.md
    creative-brief-organ_ii.md
    ...
    creative-brief-meta.md
    workflow-integration-example.yml
  organ-aesthetics/          # Per-organ aesthetic modifier YAML files
    organ-i-theoria.yaml
    organ-ii-poiesis.yaml
    ...
    organ-meta.yaml
  watcher-stdout.log         # Screenshot watcher output
  watcher-stderr.log         # Screenshot watcher errors
```

---

## Configuration

### Dependencies

- **Required**: Python 3.11+, PyYAML
- **Development**: pytest, ruff
- **Optional**: google-api-python-client + google-auth-oauthlib (for Google Docs channel)
- **External**: pandoc (for .docx → .md conversion), gh CLI (for GitHub API deployment)

### Registry Path

The registry loader defaults to looking for `registry-v2.json` at the path configured in `alchemia.absorb.registry_loader`. Update `REGISTRY_PATH` if your corpus path differs.

### Source Directories

Default source directories for `alchemia intake` are configured in `cli.py` as `DEFAULT_SOURCE_DIRS`. Override with `--source-dir` flags.

---

## Development

```bash
# Set up development environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Run specific test module
pytest tests/test_absorb.py -v
```

---

## Part of the Organ System

Alchemia Ingestvm is the material ingestion engine for the [eight-organ creative-institutional system](https://github.com/meta-organvm/organvm-corpvs-testamentvm). It operates at the Meta level, processing raw material from across the workspace and routing it to the appropriate organ repositories with full provenance tracking and aesthetic consistency enforcement.

| Relationship | Target |
|-------------|--------|
| Consumes | `registry-v2.json` from `organvm-corpvs-testamentvm` |
| Produces | Classified artifacts, deployment manifests, provenance records, creative briefs |
| Aesthetic chain | `taste.yaml` propagates to all organ content generation |

---

*Built with the [AI-conductor model](https://github.com/organvm-v-logos/public-process): human directs, AI generates, human refines.*
