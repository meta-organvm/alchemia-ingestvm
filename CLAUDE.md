# CLAUDE.md — alchemia-ingestvm

**ORGAN Meta** (Meta) · `meta-organvm/alchemia-ingestvm`
**Status:** ACTIVE · **Branch:** `main`

## What This Repo Is

The Alchemical Forge — Material ingestion pipeline and aesthetic nervous system. Three-stage pipeline (INTAKE → ABSORB → ALCHEMIZE) for deploying source materials, plus cascading taste profiles (taste.yaml → organ-aesthetic.yaml → repo-aesthetic.yaml) for autonomous aesthetic propagation.

## Stack

**Languages:** Python, Shell
**Build:** Python (pip/setuptools)
**Testing:** pytest (likely)

## Directory Structure

```
📁 .github/
📁 agents/
📁 data/
📁 scripts/
    install-agents.sh
    screenshot-watcher.sh
📁 src/
    alchemia
📁 tests/
    __init__.py
    test_absorb.py
    test_aesthetic.py
    test_google_docs.py
    test_intake.py
  .gitignore
  README.md
  pyproject.toml
  seed.yaml
  taste.yaml
```

## Key Files

- `README.md` — Project documentation
- `pyproject.toml` — Python project config
- `seed.yaml` — ORGANVM orchestration metadata
- `src/` — Main source code
- `tests/` — Test suite

## Development

```bash
pip install -e .    # Install in development mode
pytest              # Run tests
```

## ORGANVM Context

This repository is part of the **ORGANVM** eight-organ creative-institutional system.
It belongs to **ORGAN Meta (Meta)** under the `meta-organvm` GitHub organization.

**Dependencies:**
- meta-organvm/organvm-corpvs-testamentvm

**Registry:** [`registry-v2.json`](https://github.com/meta-organvm/organvm-corpvs-testamentvm/blob/main/registry-v2.json)
**Corpus:** [`organvm-corpvs-testamentvm`](https://github.com/meta-organvm/organvm-corpvs-testamentvm)

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** META-ORGANVM (Meta) | **Tier:** standard | **Status:** CANDIDATE
**Org:** `unknown` | **Repo:** `alchemia-ingestvm`

### Edges
- **Produces** → `classified-artifacts`
- **Produces** → `deployment-manifests`
- **Produces** → `provenance-records`
- **Produces** → `creative-briefs`
- **Produces** → `aesthetic-chains`
- **Consumes** ← `organvm-corpvs-testamentvm`: registry-v2.json

### Siblings in Meta
`.github`, `organvm-corpvs-testamentvm`, `schema-definitions`, `organvm-engine`, `system-dashboard`, `organvm-mcp-server`

### Governance
- *Standard ORGANVM governance applies*

*Last synced: 2026-02-24T12:41:28Z*
<!-- ORGANVM:AUTO:END -->


## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.
