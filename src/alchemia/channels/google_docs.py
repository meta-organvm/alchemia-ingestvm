"""Google Docs sync — watch an 'Alchemia' folder in Google Drive and export docs as markdown.

Requires optional dependencies:
    pip install google-api-python-client google-auth-oauthlib

Setup:
    1. Create a Google Cloud project and enable the Drive API
    2. Create OAuth2 credentials (Desktop app type)
    3. Download the client secret JSON to ~/.config/alchemia/client_secret.json
    4. Run `alchemia gdocs-auth` to complete the consent flow (stores token)

The module gracefully degrades if google packages are not installed.
"""

from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path("~/.config/alchemia").expanduser()
CLIENT_SECRET_PATH = CONFIG_DIR / "client_secret.json"
TOKEN_PATH = CONFIG_DIR / "google_token.json"
ALCHEMIA_FOLDER_NAME = "Alchemia"

# Google Drive MIME types
GDOC_MIME = "application/vnd.google-apps.document"
GSHEET_MIME = "application/vnd.google-apps.spreadsheet"
GSLIDE_MIME = "application/vnd.google-apps.presentation"

# Export MIME mappings
EXPORT_MIMES = {
    GDOC_MIME: ("text/markdown", ".md"),
    GSHEET_MIME: ("text/csv", ".csv"),
    GSLIDE_MIME: ("text/plain", ".txt"),
}


def _check_dependencies() -> bool:
    """Check if Google API dependencies are installed."""
    try:
        import google.auth  # noqa: F401
        import googleapiclient  # noqa: F401

        return True
    except ImportError:
        return False


def _get_credentials():
    """Load or refresh OAuth2 credentials.

    Returns google.oauth2.credentials.Credentials or None.
    """
    if not _check_dependencies():
        return None

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(TOKEN_PATH),
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        except Exception:
            creds = None

    return creds


def authorize() -> bool:
    """Run the OAuth2 consent flow interactively.

    Requires client_secret.json at ~/.config/alchemia/client_secret.json.
    Opens a browser for the user to grant access, then stores the token.

    Returns True on success, False on failure.
    """
    if not _check_dependencies():
        print("  ERROR: google-api-python-client and google-auth-oauthlib required")
        print("  Run: pip install google-api-python-client google-auth-oauthlib")
        return False

    if not CLIENT_SECRET_PATH.exists():
        print(f"  ERROR: Client secret not found at {CLIENT_SECRET_PATH}")
        print("  Download from Google Cloud Console → APIs & Services → Credentials")
        return False

    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
        creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
        print(f"  Token saved to {TOKEN_PATH}")
        return True
    except Exception as e:
        print(f"  Authorization failed: {e}")
        return False


def _build_service():
    """Build a Google Drive API service client.

    Returns googleapiclient.discovery.Resource or None.
    """
    creds = _get_credentials()
    if not creds or not creds.valid:
        return None

    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=creds)


def _find_alchemia_folder(service) -> str | None:
    """Find the 'Alchemia' folder ID in Google Drive.

    Returns the folder ID or None if not found.
    """
    query = (
        f"name = '{ALCHEMIA_FOLDER_NAME}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id, name)", pageSize=5).execute()

    files = results.get("files", [])
    if files:
        return files[0]["id"]
    return None


def list_docs(folder_name: str | None = None) -> list[dict]:
    """List Google Docs in the Alchemia folder.

    Returns list of document metadata dicts with keys:
        id, name, mimeType, modifiedTime, createdTime
    """
    if not _check_dependencies():
        return []

    service = _build_service()
    if not service:
        return []

    folder_name = folder_name or ALCHEMIA_FOLDER_NAME
    folder_id = _find_alchemia_folder(service)
    if not folder_id:
        return []

    query = f"'{folder_id}' in parents and trashed = false"
    all_files = []
    page_token = None

    while True:
        results = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, createdTime)",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )

        all_files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return all_files


def export_doc(doc_id: str, mime_type: str) -> bytes | None:
    """Export a Google Doc as the specified MIME type.

    For Google Docs, use 'text/markdown' or 'text/plain'.
    For regular files, downloads the file content directly.

    Returns bytes content or None on failure.
    """
    service = _build_service()
    if not service:
        return None

    try:
        return service.files().export(fileId=doc_id, mimeType=mime_type).execute()
    except Exception:
        # Might be a regular file (not a Google Doc), try downloading
        try:
            return service.files().get_media(fileId=doc_id).execute()
        except Exception:
            return None


def sync_google_docs(output_dir: Path | None = None) -> list[dict]:
    """Sync all docs from the Alchemia folder to a local directory.

    Exports Google Docs as markdown, Sheets as CSV, etc.
    Regular files (PDF, images) are downloaded directly.

    Returns list of synced document info dicts.
    """
    output_dir = output_dir or Path("data/google-docs")
    output_dir.mkdir(parents=True, exist_ok=True)

    docs = list_docs()
    if not docs:
        return []

    results = []
    for doc in docs:
        doc_id = doc["id"]
        name = doc["name"]
        mime = doc.get("mimeType", "")
        modified = doc.get("modifiedTime", "")

        # Determine export format
        if mime in EXPORT_MIMES:
            export_mime, ext = EXPORT_MIMES[mime]
        else:
            # Regular file — skip or download
            ext = Path(name).suffix or ".bin"
            export_mime = None

        safe_name = _sanitize_filename(name)
        if not safe_name.endswith(ext):
            safe_name = safe_name + ext

        out_path = output_dir / safe_name

        # Skip if local copy is newer than remote
        if out_path.exists():
            local_mtime = datetime.fromtimestamp(out_path.stat().st_mtime, tz=timezone.utc)
            try:
                remote_mtime = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                if local_mtime >= remote_mtime:
                    results.append(
                        {
                            "name": name,
                            "status": "up_to_date",
                            "path": str(out_path),
                        }
                    )
                    continue
            except (ValueError, TypeError):
                pass  # Can't parse remote time, re-download

        # Export/download
        content = export_doc(doc_id, export_mime) if export_mime else None
        if content is None and export_mime is None:
            # Try direct download for non-Google files
            service = _build_service()
            if service:
                try:
                    content = service.files().get_media(fileId=doc_id).execute()
                except Exception:
                    pass

        if content:
            if isinstance(content, str):
                out_path.write_text(content, encoding="utf-8")
            else:
                out_path.write_bytes(content)

            results.append(
                {
                    "name": name,
                    "status": "synced",
                    "path": str(out_path),
                    "mime_type": mime,
                    "modified": modified,
                }
            )
        else:
            results.append(
                {
                    "name": name,
                    "status": "failed",
                    "error": "Could not export or download",
                }
            )

    return results


def _sanitize_filename(name: str) -> str:
    """Sanitize a filename for local storage."""
    # Replace problematic characters
    for char in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        name = name.replace(char, "-")
    return name.strip(". ")


def get_status() -> dict:
    """Get the current status of Google Docs integration.

    Returns a dict with:
        installed: bool — google packages available
        authenticated: bool — valid token exists
        folder_found: bool — Alchemia folder exists in Drive
        doc_count: int — number of docs in folder
    """
    status = {
        "installed": _check_dependencies(),
        "authenticated": False,
        "folder_found": False,
        "doc_count": 0,
    }

    if not status["installed"]:
        return status

    creds = _get_credentials()
    status["authenticated"] = creds is not None and creds.valid

    if status["authenticated"]:
        service = _build_service()
        if service:
            folder_id = _find_alchemia_folder(service)
            status["folder_found"] = folder_id is not None
            if folder_id:
                docs = list_docs()
                status["doc_count"] = len(docs)

    return status
