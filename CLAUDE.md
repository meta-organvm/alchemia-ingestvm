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
