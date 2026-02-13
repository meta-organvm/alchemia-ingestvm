"""CLI entry point for alchemia commands."""

import argparse
import sys
from pathlib import Path


def cmd_intake(args):
    """Run the INTAKE stage: crawl + fingerprint source directories."""
    from alchemia.intake.crawler import crawl
    from alchemia.intake.dedup import mark_duplicates
    from alchemia.intake.manifest_loader import enrich_from_manifest, enrich_from_sidecars

    source_dirs = [Path(d) for d in args.source_dir]
    output = Path(args.output)

    print(f"INTAKE — Crawling {len(source_dirs)} source directories...")
    inventory = crawl(source_dirs)
    print(f"  Found {len(inventory)} files")

    # Enrich with existing metadata
    if args.manifest:
        manifest_path = Path(args.manifest)
        if manifest_path.exists():
            print(f"  Enriching from manifest: {manifest_path}")
            inventory = enrich_from_manifest(inventory, manifest_path)

    print("  Enriching from .meta.json sidecars...")
    inventory = enrich_from_sidecars(inventory)

    print("  Detecting duplicates...")
    inventory = mark_duplicates(inventory)

    # Write output
    import json

    with open(output, "w") as f:
        json.dump(
            {
                "schema_version": "1.0",
                "stage": "intake",
                "source_dirs": [str(d) for d in source_dirs],
                "total_files": len(inventory),
                "entries": inventory,
            },
            f,
            indent=2,
            default=str,
        )
    print(f"  Wrote {output} ({len(inventory)} entries)")


def cmd_absorb(args):
    """Run the ABSORB stage: classify + map files to target repos."""
    import json

    from alchemia.absorb.classifier import classify_all
    from alchemia.absorb.registry_loader import load_registry

    inventory_path = Path(args.inventory)
    output = Path(args.output)

    print("ABSORB — Loading inventory...")
    with open(inventory_path) as f:
        data = json.load(f)
    entries = data["entries"]
    print(f"  Loaded {len(entries)} entries from {inventory_path}")

    print("  Loading registry...")
    registry = load_registry()
    print(f"  Registry: {len(registry['repos'])} repos, {len(registry['archived'])} archived")

    print("  Classifying...")
    entries = classify_all(entries, registry)

    # Write output
    with open(output, "w") as f:
        json.dump(
            {
                "schema_version": "1.0",
                "stage": "absorb",
                "source_inventory": str(inventory_path),
                "total_entries": len(entries),
                "entries": entries,
            },
            f,
            indent=2,
            default=str,
        )
    print(f"  Wrote {output} ({len(entries)} entries)")


def cmd_alchemize(args):
    """Run the ALCHEMIZE stage: transform + deploy."""
    import json

    from alchemia.absorb.registry_loader import load_registry
    from alchemia.alchemize.deployer import deploy_file, is_archived
    from alchemia.alchemize.provenance import generate_provenance_registry, get_deployment_plan
    from alchemia.alchemize.transformer import classify_action, get_deploy_path

    mapping_path = Path(args.mapping)
    print("ALCHEMIZE — Loading classified inventory...")
    with open(mapping_path) as f:
        data = json.load(f)
    entries = data["entries"]
    print(f"  Loaded {len(entries)} entries")

    registry = load_registry()

    # Build deployment plan
    plan = get_deployment_plan(entries)
    total_deploy = sum(len(v["deploy"]) for v in plan.values())
    total_convert = sum(len(v["convert"]) for v in plan.values())
    total_reference = sum(len(v["reference"]) for v in plan.values())
    total_skip = sum(len(v["skip"]) for v in plan.values())

    print(f"\n  Deployment plan:")
    print(f"    Deploy directly: {total_deploy}")
    print(f"    Convert (docx→md): {total_convert}")
    print(f"    Reference only: {total_reference}")
    print(f"    Skip (dup/unclassified): {total_skip}")
    print(f"    Target repos: {len(plan)}")

    # Filter by organ/repo if specified
    if args.organ:
        organ_filter = f"ORGAN-{args.organ.upper()}"
        plan = {
            k: v for k, v in plan.items()
            if any(e.get("classification", {}).get("target_organ") == organ_filter
                   for e in v["deploy"] + v["convert"])
        }
        print(f"    Filtered to organ {args.organ}: {len(plan)} repos")

    if args.repo:
        plan = {k: v for k, v in plan.items() if args.repo in k}
        print(f"    Filtered to repo '{args.repo}': {len(plan)} repos")

    if args.dry_run:
        print("\n  [DRY RUN] Would deploy to:")
        for repo_key, actions in sorted(plan.items()):
            deploy_count = len(actions["deploy"])
            ref_count = len(actions["reference"])
            if deploy_count or ref_count:
                print(f"    {repo_key}: {deploy_count} files + {ref_count} references")
                for entry in actions["deploy"][:3]:
                    print(f"      → {entry.get('_deploy_path', '?')}")
                if deploy_count > 3:
                    print(f"      ... and {deploy_count - 3} more")
        print(f"\n  Total: {total_deploy} deployments across {len(plan)} repos")
        print("  Run without --dry-run to execute.")
        return

    # Generate provenance registry
    prov_registry = generate_provenance_registry(entries)
    prov_path = Path("data/provenance-registry.json")
    with open(prov_path, "w") as f:
        json.dump(prov_registry, f, indent=2, default=str)
    print(f"\n  Wrote {prov_path}")
    print(f"  Provenance: {prov_registry['total_classified']} classified → {prov_registry['total_target_repos']} repos")


def cmd_status(args):
    """Show pipeline status."""
    import json

    for name in ["intake-inventory.json", "absorb-mapping.json", "provenance-registry.json"]:
        p = Path("data") / name
        if p.exists():
            with open(p) as f:
                data = json.load(f)
            print(f"  {name}: {data.get('total_files', data.get('total_entries', '?'))} entries")
        else:
            print(f"  {name}: not found")


def cmd_review(args):
    """Interactive review of PENDING_REVIEW items."""
    print("REVIEW — Not yet implemented (Phase B)")
    sys.exit(1)


def cmd_capture(args):
    """Quick-capture an aesthetic reference."""
    from alchemia.aesthetic import add_reference

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    entry = add_reference(
        ref_type=args.type,
        value=args.value,
        tags=tags,
        notes=args.notes or "",
    )
    print(f"CAPTURE — Added {entry['type']} reference")
    print(f"  Tags: {entry.get('tags', [])}")
    print(f"  Captured: {entry.get('captured', '')}")


DEFAULT_SOURCE_DIRS = [
    "~/Workspace/intake",
    "~/Workspace/organvm-pactvm",
    "~/Workspace/ORG-IV-orchestration-staging",
    "~/Workspace/ORG-V-public-process-staging",
    "~/Workspace/ORG-VI-community-staging",
    "~/Workspace/ORG-VII-marketing-staging",
    "~/Workspace/metasystem-core",
    "~/Workspace/auto-rev-epistemic-engine_spec",
    "~/Workspace/all-fusion-engine",
    "~/Workspace/4444J99",
    "~/Workspace/4444JPP",
    "~/Workspace/4444j99-organs",
    "~/Workspace/4444j99-orchestration",
    "~/Workspace/4444j99-community",
    "~/Workspace/4444j99-marketing",
]


def main():
    parser = argparse.ArgumentParser(
        prog="alchemia",
        description="The Alchemical Forge — Material ingestion & aesthetic propagation",
    )
    sub = parser.add_subparsers(dest="command")

    # intake
    p_intake = sub.add_parser("intake", help="Crawl + fingerprint source directories")
    p_intake.add_argument(
        "--source-dir",
        nargs="+",
        default=[str(Path(d).expanduser()) for d in DEFAULT_SOURCE_DIRS],
        help="Directories to crawl",
    )
    p_intake.add_argument(
        "--manifest",
        default=str(Path("~/Workspace/organvm-pactvm/MANIFEST_INDEX_TABLE.csv").expanduser()),
        help="Path to MANIFEST_INDEX_TABLE.csv",
    )
    p_intake.add_argument(
        "--output",
        default="data/intake-inventory.json",
        help="Output file path",
    )
    p_intake.set_defaults(func=cmd_intake)

    # absorb
    p_absorb = sub.add_parser("absorb", help="Classify + map files to target repos")
    p_absorb.add_argument("--inventory", default="data/intake-inventory.json")
    p_absorb.add_argument("--output", default="data/absorb-mapping.json")
    p_absorb.set_defaults(func=cmd_absorb)

    # alchemize
    p_alch = sub.add_parser("alchemize", help="Transform + deploy to repos")
    p_alch.add_argument("--mapping", default="data/absorb-mapping.json", help="Classified mapping file")
    p_alch.add_argument("--dry-run", action="store_true")
    p_alch.add_argument("--organ", help="Limit to specific organ (e.g. I, II)")
    p_alch.add_argument("--repo", help="Limit to specific repo name")
    p_alch.add_argument("--batch-size", type=int, default=20)
    p_alch.set_defaults(func=cmd_alchemize)

    # status
    p_status = sub.add_parser("status", help="Pipeline stats")
    p_status.set_defaults(func=cmd_status)

    # review
    p_review = sub.add_parser("review", help="Interactive review of PENDING_REVIEW items")
    p_review.add_argument("--status", default="PENDING_REVIEW")
    p_review.set_defaults(func=cmd_review)

    # capture
    p_capture = sub.add_parser("capture", help="Quick-capture an aesthetic reference")
    p_capture.add_argument("--type", choices=["url", "note", "screenshot"], required=True)
    p_capture.add_argument("value", help="URL, note text, or file path")
    p_capture.add_argument("--tags", help="Comma-separated tags")
    p_capture.add_argument("--notes", help="Why this reference matters")
    p_capture.set_defaults(func=cmd_capture)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)
