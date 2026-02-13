"""Duplicate detection by SHA-256 fingerprint."""

from collections import defaultdict


def mark_duplicates(entries: list[dict]) -> list[dict]:
    """Mark duplicate files. Most-specific directory path wins (deepest nesting)."""
    by_hash = defaultdict(list)

    for entry in entries:
        sha = entry.get("sha256")
        if sha and sha != "ERROR_UNREADABLE":
            by_hash[sha].append(entry)

    dup_count = 0
    for sha, group in by_hash.items():
        if len(group) < 2:
            for e in group:
                e["duplicate"] = False
                e["duplicate_group"] = None
            continue

        # Sort by depth (deepest = most specific wins), then by path length
        group.sort(key=lambda e: (-e.get("depth", 0), len(e["path"])))
        primary = group[0]
        primary["duplicate"] = False
        primary["duplicate_group"] = sha[:12]

        for dup in group[1:]:
            dup["duplicate"] = True
            dup["duplicate_group"] = sha[:12]
            dup["duplicate_of"] = primary["path"]
            dup_count += 1

    # Mark non-duplicate singletons
    for entry in entries:
        if "duplicate" not in entry:
            entry["duplicate"] = False
            entry["duplicate_group"] = None

    print(f"  Found {dup_count} duplicate files across {len(by_hash)} unique hashes")
    return entries
