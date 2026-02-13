"""Bookmark sync — Safari and Chrome 'Inspirations' folder monitoring."""

import json
import plistlib
import subprocess
from pathlib import Path


SAFARI_BOOKMARKS = Path("~/Library/Safari/Bookmarks.plist").expanduser()
CHROME_BOOKMARKS = Path(
    "~/Library/Application Support/Google/Chrome/Default/Bookmarks"
).expanduser()

INSPIRATIONS_FOLDER = "Inspirations"


def parse_safari_bookmarks() -> list[dict]:
    """Parse Safari bookmarks for items in the 'Inspirations' folder.

    Safari stores bookmarks as a binary plist with nested Children arrays.
    """
    if not SAFARI_BOOKMARKS.exists():
        return []

    try:
        # Convert binary plist to XML for parsing
        result = subprocess.run(
            ["plutil", "-convert", "xml1", "-o", "-", str(SAFARI_BOOKMARKS)],
            capture_output=True,
        )
        if result.returncode != 0:
            return []
        data = plistlib.loads(result.stdout)
    except (plistlib.InvalidFileException, OSError):
        return []

    bookmarks = []
    _walk_safari_tree(data.get("Children", []), [], bookmarks)
    return bookmarks


def _walk_safari_tree(children: list, path: list, results: list):
    """Recursively walk Safari bookmark tree looking for Inspirations folder."""
    for item in children:
        item_type = item.get("WebBookmarkType", "")
        title = item.get("Title", item.get("URIDictionary", {}).get("title", ""))

        if item_type == "WebBookmarkTypeList":
            # Folder
            new_path = path + [title]
            if title == INSPIRATIONS_FOLDER or INSPIRATIONS_FOLDER in path:
                _walk_safari_tree(item.get("Children", []), new_path, results)
            else:
                _walk_safari_tree(item.get("Children", []), new_path, results)

        elif item_type == "WebBookmarkTypeLeaf":
            # Bookmark
            if INSPIRATIONS_FOLDER in path:
                url = item.get("URLString", "")
                if url:
                    results.append({
                        "source": "safari",
                        "url": url,
                        "title": title,
                        "folder_path": "/".join(path),
                    })


def parse_chrome_bookmarks() -> list[dict]:
    """Parse Chrome bookmarks for items in the 'Inspirations' folder.

    Chrome stores bookmarks as a JSON file.
    """
    if not CHROME_BOOKMARKS.exists():
        return []

    try:
        with open(CHROME_BOOKMARKS, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    bookmarks = []
    roots = data.get("roots", {})
    for root_name, root_data in roots.items():
        if isinstance(root_data, dict):
            _walk_chrome_tree(root_data, [], bookmarks)
    return bookmarks


def _walk_chrome_tree(node: dict, path: list, results: list):
    """Recursively walk Chrome bookmark tree looking for Inspirations folder."""
    name = node.get("name", "")
    node_type = node.get("type", "")

    if node_type == "folder":
        new_path = path + [name]
        for child in node.get("children", []):
            if name == INSPIRATIONS_FOLDER or INSPIRATIONS_FOLDER in path:
                _walk_chrome_tree(child, new_path, results)
            else:
                _walk_chrome_tree(child, new_path, results)

    elif node_type == "url":
        if INSPIRATIONS_FOLDER in path:
            url = node.get("url", "")
            if url:
                results.append({
                    "source": "chrome",
                    "url": url,
                    "title": name,
                    "folder_path": "/".join(path),
                })


def sync_bookmarks() -> list[dict]:
    """Sync bookmarks from all browser sources. Returns new bookmark entries."""
    all_bookmarks = []
    all_bookmarks.extend(parse_safari_bookmarks())
    all_bookmarks.extend(parse_chrome_bookmarks())
    return all_bookmarks
