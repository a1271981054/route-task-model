#!/usr/bin/env python3
"""Store a small, local, redacted routing snapshot for each Codex lifecycle event."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


MAX_TRANSCRIPT_TAIL = 12000
OUTPUT_DIR = Path.home() / ".codex" / "route-context"

SECRET_PATTERNS = (
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(secret|password|token)\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "[REDACTED_OPENAI_KEY]"),
)


def redact(value: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def read_input() -> dict:
    try:
        value = json.load(sys.stdin)
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def transcript_tail(path_value: object) -> str | None:
    if not isinstance(path_value, str) or not path_value:
        return None
    path = Path(path_value).expanduser()
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            handle.seek(max(0, handle.tell() - MAX_TRANSCRIPT_TAIL))
            data = handle.read(MAX_TRANSCRIPT_TAIL)
        return redact(data.decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


def main() -> int:
    event = read_input()
    session_id = str(event.get("session_id") or "unknown")
    snapshot = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "event": event.get("hook_event_name"),
        "session_id": session_id,
        "turn_id": event.get("turn_id"),
        "model": event.get("model"),
        "cwd": event.get("cwd"),
        "permission_mode": event.get("permission_mode"),
        "source": event.get("source"),
        "agent_id": event.get("agent_id"),
        "agent_type": event.get("agent_type"),
        "transcript_path": event.get("transcript_path"),
        "transcript_tail": transcript_tail(event.get("transcript_path")),
    }

    try:
        OUTPUT_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = OUTPUT_DIR / f"{session_id}.jsonl"
        encoded = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
        with target.open("a", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.write("\n")
        target.chmod(0o600)
        latest_tmp = OUTPUT_DIR / ".latest.json.tmp"
        latest_tmp.write_text(encoded + "\n", encoding="utf-8")
        latest_tmp.chmod(0o600)
        os.replace(latest_tmp, OUTPUT_DIR / "latest.json")
    except OSError:
        # Snapshotting must never block or alter the Codex turn.
        return 0

    if event.get("hook_event_name") == "UserPromptSubmit":
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": (
                            "Before any tool call, apply the route-task-model skill. "
                            "Emit exactly one concise Chinese [Route] line showing "
                            "任务类型、中文模型名、中文推理等级和执行方式. Use the "
                            "automatic Spark -> GPT-5.4 -> GPT-5.5 -> GPT-5.6-Luna "
                            "ladder. GPT-5.6-Terra is automatic only for broad, "
                            "tool-heavy work with at least two concrete signals. "
                            "Never select GPT-5.6-Sol without explicit user approval."
                        ),
                    }
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
