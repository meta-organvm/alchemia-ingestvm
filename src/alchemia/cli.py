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
    from alchemia.alchemize.provenance import generate_provenance_registry, get_deployment_plan

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

    print("\n  Deployment plan:")
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

    # Actual deployment
    from alchemia.alchemize.batch_deployer import build_deployment_manifest, deploy_repo_batch

    manifest = build_deployment_manifest(entries, registry)

    # Apply organ/repo filters
    if args.organ:
        organ_filter = f"ORGAN-{args.organ.upper()}"
        manifest = {
            k: v for k, v in manifest.items()
            if any(
                e.get("classification", {}).get("target_organ") == organ_filter
                for e in entries
                if e.get("classification", {}).get("target_repo") == v["repo"]
            )
        }

    if args.repo:
        manifest = {k: v for k, v in manifest.items() if args.repo in k}

    print(f"\n  Deploying to {len(manifest)} repos...")
    total_deployed = 0
    total_skipped = 0
    total_failed = 0

    for repo_key, repo_data in sorted(manifest.items()):
        org = repo_data["org"]
        repo = repo_data["repo"]
        files = repo_data["files"]
        print(f"\n  {repo_key}: {len(files)} files")

        result = deploy_repo_batch(
            org, repo, files,
            force=args.force,
            batch_size=args.batch_size,
        )

        total_deployed += result["deployed"]
        total_skipped += result["skipped"]
        total_failed += result["failed"]

        deployed = result['deployed']
        skipped = result['skipped']
        failed = result['failed']
        print(f"    deployed={deployed} skipped={skipped} failed={failed}")
        if result.get("errors"):
            for err in result["errors"][:3]:
                print(f"    ERROR: {err}")

    print(f"\n  Summary: deployed={total_deployed} skipped={total_skipped} failed={total_failed}")

    # Generate and save provenance registry
    prov_registry = generate_provenance_registry(entries)
    prov_path = Path("data/provenance-registry.json")
    with open(prov_path, "w") as f:
        json.dump(prov_registry, f, indent=2, default=str)
    print(f"  Wrote {prov_path}")


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


def cmd_synthesize(args):
    """Generate creative briefs from accumulated references."""
    from alchemia.synthesize import generate_all_briefs, generate_workflow_integration_example

    output_dir = Path(args.output_dir)
    print("SYNTHESIZE — Generating creative briefs...")

    briefs = generate_all_briefs(output_dir=output_dir)
    print(f"\n  Generated {len(briefs)} creative briefs")

    # Also generate the workflow integration example
    example = generate_workflow_integration_example()
    example_path = output_dir / "workflow-integration-example.yml"
    example_path.write_text(example)
    print(f"  Generated: {example_path}")

    print(f"\n  All briefs written to {output_dir}/")


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


def cmd_sync(args):
    """Sync all capture channels (bookmarks, notes, AI chats)."""
    from alchemia.aesthetic import add_reference
    from alchemia.channels.bookmarks import sync_bookmarks
    from alchemia.channels.apple_notes import export_alchemia_notes
    from alchemia.channels.ai_chats import parse_gemini_visits

    print("SYNC — Running capture channels...")

    # Channel 2: Bookmarks
    print("\n  Bookmarks:")
    bookmarks = sync_bookmarks()
    new_bookmarks = 0
    for bm in bookmarks:
        entry = add_reference(
            ref_type="url",
            value=bm["url"],
            tags=["bookmark", bm["source"]],
            notes=f"From {bm['source']}: {bm.get('title', '')}",
        )
        new_bookmarks += 1
    print(f"    Found {len(bookmarks)} bookmarks in Inspirations folder, added {new_bookmarks}")

    # Channel 3: Apple Notes
    print("\n  Apple Notes:")
    notes = export_alchemia_notes()
    print(f"    Found {len(notes)} notes in Alchemia folder")
    for note in notes:
        print(f"    - {note.get('title', 'Untitled')} ({note.get('body_length', 0)} chars)")

    # Channel 4: Google Docs
    print("\n  Google Docs:")
    from alchemia.channels.google_docs import get_status, sync_google_docs

    gdocs_status = get_status()
    if not gdocs_status["installed"]:
        print("    Skipped — google-api-python-client not installed")
        print("    Run: pip install google-api-python-client google-auth-oauthlib")
    elif not gdocs_status["authenticated"]:
        print("    Skipped — not authenticated")
        print("    Run: alchemia gdocs-auth")
    else:
        gdocs = sync_google_docs()
        synced = sum(1 for d in gdocs if d["status"] == "synced")
        up_to_date = sum(1 for d in gdocs if d["status"] == "up_to_date")
        failed = sum(1 for d in gdocs if d["status"] == "failed")
        print(
            f"    {len(gdocs)} docs in Alchemia folder:"
            f" {synced} synced, {up_to_date} up-to-date, {failed} failed"
        )
        for doc in gdocs:
            print(f"    - {doc['name']} [{doc['status']}]")

    # Channel 5: Gemini visits
    print("\n  Gemini visits:")
    intake_dir = Path("~/Workspace/intake").expanduser()
    gemini = parse_gemini_visits(intake_dir)
    print(f"    Found {len(gemini)} Gemini visit files")

    print("\n  Sync complete.")


def cmd_gdocs_auth(args):
    """Authorize Google Docs access via OAuth2."""
    from alchemia.channels.google_docs import authorize

    print("GDOCS-AUTH — Starting OAuth2 consent flow...")
    success = authorize()
    if success:
        print("  Authorization successful. Google Docs sync is now available.")
    else:
        sys.exit(1)


def cmd_gdocs_status(args):
    """Show Google Docs integration status."""
    from alchemia.channels.google_docs import get_status

    print("GDOCS-STATUS —")
    status = get_status()
    print(f"  Dependencies installed: {status['installed']}")
    print(f"  Authenticated: {status['authenticated']}")
    print(f"  Alchemia folder found: {status['folder_found']}")
    print(f"  Documents in folder: {status['doc_count']}")

    if not status["installed"]:
        print("\n  To set up: pip install google-api-python-client google-auth-oauthlib")
    elif not status["authenticated"]:
        print("\n  To authenticate: alchemia gdocs-auth")
    elif not status["folder_found"]:
        print("\n  Create a folder named 'Alchemia' in Google Drive to get started.")


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
    p_alch.add_argument(
        "--mapping", default="data/absorb-mapping.json",
        help="Classified mapping file",
    )
    p_alch.add_argument("--dry-run", action="store_true")
    p_alch.add_argument("--force", action="store_true", help="Overwrite existing files")
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

    # sync
    p_sync = sub.add_parser("sync", help="Sync all capture channels")
    p_sync.set_defaults(func=cmd_sync)

    # synthesize
    p_synth = sub.add_parser("synthesize", help="Generate creative briefs from references")
    p_synth.add_argument("--output-dir", default="data/creative-briefs", help="Output directory")
    p_synth.set_defaults(func=cmd_synthesize)

    # gdocs-auth
    p_gdauth = sub.add_parser("gdocs-auth", help="Authorize Google Docs access via OAuth2")
    p_gdauth.set_defaults(func=cmd_gdocs_auth)

    # gdocs-status
    p_gdstatus = sub.add_parser("gdocs-status", help="Show Google Docs integration status")
    p_gdstatus.set_defaults(func=cmd_gdocs_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)
