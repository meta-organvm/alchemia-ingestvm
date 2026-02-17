"""Apple Notes bridge — export notes from 'Alchemia' folder via AppleScript."""

import json
import subprocess
from pathlib import Path

NOTES_OUTPUT_DIR = Path("~/Workspace/alchemia-ingestvm/data/notes").expanduser()


def export_alchemia_notes() -> list[dict]:
    """Export notes from the 'Alchemia' folder in Apple Notes.

    Uses AppleScript to read note titles and bodies. Notes are
    classified by hashtag:
      - #aesthetic → taste.yaml references
      - #spec / #idea → material pipeline
      - No tag → uncategorized
    """
    NOTES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # AppleScript to export notes from "Alchemia" folder
    applescript = """
    tell application "Notes"
        set output to ""
        try
            set alchemiaFolder to folder "Alchemia"
            repeat with aNote in notes of alchemiaFolder
                set noteTitle to name of aNote
                set noteBody to plaintext of aNote
                set noteDate to modification date of aNote as «class isot» as string
                set noteId to id of aNote
                -- JSON-escape basic characters
                set output to output & "{"
                set output to output & "\\"id\\": \\"" & noteId & "\\","
                set output to output & "\\"title\\": \\"" & noteTitle & "\\","
                set output to output & "\\"modified\\": \\"" & noteDate & "\\","
                set output to output & "\\"body_length\\": " & (length of noteBody) & ""
                set output to output & "}" & linefeed
            end repeat
        on error errMsg
            set output to "ERROR: " & errMsg
        end try
        return output
    end tell
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("  WARNING: Apple Notes export timed out")
        return []

    if result.returncode != 0 or result.stdout.startswith("ERROR:"):
        err = result.stdout.strip() or result.stderr.strip()
        if "folder" in err.lower() and "alchemia" in err.lower():
            print(
                "  INFO: No 'Alchemia' folder found in Apple Notes — create one to use this channel"
            )
        else:
            print(f"  WARNING: Apple Notes export failed: {err[:200]}")
        return []

    # Parse the output (one JSON object per line)
    notes = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("ERROR:"):
            continue
        try:
            note = json.loads(line)
            notes.append(note)
        except json.JSONDecodeError:
            continue

    return notes


def export_note_body(note_title: str) -> str:
    """Export the full body of a specific note."""
    applescript = f'''
    tell application "Notes"
        try
            set alchemiaFolder to folder "Alchemia"
            repeat with aNote in notes of alchemiaFolder
                if name of aNote is "{note_title}" then
                    return plaintext of aNote
                end if
            end repeat
        on error
            return ""
        end try
        return ""
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout
    except subprocess.TimeoutExpired:
        pass
    return ""
