"""Tests for channels/ai_chats.py — ChatGPT, Claude, and Gemini parsing."""

import json

from alchemia.channels.ai_chats import (
    parse_chatgpt_export,
    parse_claude_sessions,
    parse_gemini_visits,
)


def test_chatgpt_missing_file(tmp_path):
    assert parse_chatgpt_export(tmp_path) == []


def test_chatgpt_with_conversations(tmp_path):
    conversations = [
        {
            "title": "Convo 1",
            "create_time": 1700000000,
            "mapping": {
                "m1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["This is a long enough message that exceeds fifty characters easily."]},
                    },
                },
            },
        },
        {
            "title": "Convo 2",
            "create_time": 1700001000,
            "mapping": {
                "m2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Another long message that is well over the fifty character minimum threshold."]},
                    },
                },
            },
        },
    ]
    (tmp_path / "conversations.json").write_text(json.dumps(conversations))

    result = parse_chatgpt_export(tmp_path)
    assert len(result) == 2
    assert result[0]["source"] == "chatgpt"
    assert result[0]["title"] == "Convo 1"
    assert result[0]["message_count"] == 1


def test_chatgpt_filters_short_messages(tmp_path):
    conversations = [
        {
            "title": "Short",
            "create_time": None,
            "mapping": {
                "m1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["hi"]},
                    },
                },
            },
        },
    ]
    (tmp_path / "conversations.json").write_text(json.dumps(conversations))

    result = parse_chatgpt_export(tmp_path)
    assert result == []


def test_claude_sessions_empty_dir(tmp_path):
    assert parse_claude_sessions(tmp_path) == []


def test_claude_sessions_with_jsonl(tmp_path):
    session_dir = tmp_path / "project" / "session"
    session_dir.mkdir(parents=True)
    jsonl = session_dir / "abc.jsonl"
    lines = [
        json.dumps({"type": "human", "message": {"content": "Please help me with this longer request that is over twenty characters."}}),
        json.dumps({"type": "human", "message": {"content": "Another request that is also fairly long and well over the threshold."}}),
    ]
    jsonl.write_text("\n".join(lines))

    result = parse_claude_sessions(tmp_path)
    assert len(result) == 1
    assert result[0]["source"] == "claude"
    assert result[0]["message_count"] == 2


def test_claude_sessions_skips_short_messages(tmp_path):
    session_dir = tmp_path / "project"
    session_dir.mkdir()
    jsonl = session_dir / "short.jsonl"
    jsonl.write_text(json.dumps({"type": "human", "message": {"content": "hi"}}))

    result = parse_claude_sessions(tmp_path)
    assert result == []


def test_gemini_visits_no_files(tmp_path):
    assert parse_gemini_visits(tmp_path) == []


def test_gemini_visits_with_list_data(tmp_path):
    data = [{"query": "test query", "response": "test response"}]
    (tmp_path / "_gemini_visit_001.json").write_text(json.dumps(data))

    result = parse_gemini_visits(tmp_path)
    assert len(result) == 1
    assert result[0]["source"] == "gemini"


def test_gemini_visits_with_dict_data(tmp_path):
    data = {"query": "test", "response": "response"}
    (tmp_path / "_gemini_visit_002.json").write_text(json.dumps(data))

    result = parse_gemini_visits(tmp_path)
    assert len(result) == 1
    assert result[0]["source"] == "gemini"


def test_gemini_visits_invalid_json(tmp_path):
    (tmp_path / "_gemini_visit_003.json").write_text("{bad json")

    result = parse_gemini_visits(tmp_path)
    assert result == []
