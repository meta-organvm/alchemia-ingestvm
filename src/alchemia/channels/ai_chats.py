"""AI Chat parser — extract content from ChatGPT, Claude, and Gemini exports."""

import json
from datetime import datetime, timezone
from pathlib import Path


def parse_chatgpt_export(export_dir: Path) -> list[dict]:
    """Parse ChatGPT data export (from Settings → Data Controls → Export).

    The export is a zip containing conversations.json with all chats.
    """
    convos_file = export_dir / "conversations.json"
    if not convos_file.exists():
        return []

    with open(convos_file, encoding="utf-8") as f:
        conversations = json.load(f)

    results = []
    for convo in conversations:
        title = convo.get("title", "Untitled")
        create_time = convo.get("create_time")
        messages = convo.get("mapping", {})

        # Extract key message content
        content_parts = []
        for msg_id, msg_data in messages.items():
            message = msg_data.get("message")
            if not message:
                continue
            role = message.get("author", {}).get("role", "")
            parts = message.get("content", {}).get("parts", [])
            text = " ".join(str(p) for p in parts if isinstance(p, str))
            if text and len(text) > 50:  # Skip trivial messages
                content_parts.append({"role": role, "text": text[:500]})

        if content_parts:
            results.append(
                {
                    "source": "chatgpt",
                    "title": title,
                    "created": (
                        datetime.fromtimestamp(create_time, tz=timezone.utc).isoformat()
                        if create_time
                        else None
                    ),
                    "message_count": len(content_parts),
                    "preview": content_parts[0]["text"][:200] if content_parts else "",
                }
            )

    return results


def parse_claude_sessions(claude_dir: Path | None = None) -> list[dict]:
    """Parse Claude Code session transcripts (.jsonl files).

    Claude Code stores sessions at ~/.claude/projects/<id>/<session>.jsonl
    """
    claude_dir = claude_dir or Path("~/.claude/projects").expanduser()
    if not claude_dir.exists():
        return []

    results = []
    for jsonl_file in claude_dir.rglob("*.jsonl"):
        try:
            messages = []
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        if isinstance(msg, dict) and msg.get("type") == "human":
                            text = ""
                            content = msg.get("message", {}).get("content", "")
                            if isinstance(content, str):
                                text = content
                            elif isinstance(content, list):
                                text = " ".join(
                                    p.get("text", "")
                                    for p in content
                                    if isinstance(p, dict) and p.get("type") == "text"
                                )
                            if text and len(text) > 20:
                                messages.append(text[:300])
                    except json.JSONDecodeError:
                        continue

            if messages:
                results.append(
                    {
                        "source": "claude",
                        "session_file": str(jsonl_file),
                        "message_count": len(messages),
                        "preview": messages[0][:200] if messages else "",
                    }
                )
        except OSError:
            continue

    return results


def parse_gemini_visits(intake_dir: Path) -> list[dict]:
    """Parse Gemini visit JSON files (_gemini_visit_*.json)."""
    results = []
    for gfile in intake_dir.glob("_gemini_visit_*.json"):
        try:
            with open(gfile, encoding="utf-8") as f:
                data = json.load(f)

            # Gemini exports vary in structure; extract what we can
            if isinstance(data, list):
                for item in data[:10]:  # Limit to first 10 entries
                    if isinstance(item, dict):
                        results.append(
                            {
                                "source": "gemini",
                                "file": str(gfile),
                                "preview": str(item)[:200],
                            }
                        )
            elif isinstance(data, dict):
                results.append(
                    {
                        "source": "gemini",
                        "file": str(gfile),
                        "preview": str(data)[:200],
                    }
                )
        except (json.JSONDecodeError, OSError):
            continue

    return results
