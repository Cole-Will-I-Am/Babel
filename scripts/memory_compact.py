#!/usr/bin/env python3
"""Compact Babel per-agent runtime logs into tracked markdown summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def summarize_event(event: dict[str, Any]) -> tuple[str, str, int, int, bool]:
    timestamp = str(event.get("timestamp", "unknown"))
    stage = str(event.get("stage", "unknown"))
    response = event.get("response", {})
    if not isinstance(response, dict):
        response = {}
    summary = str(response.get("summary", "")).strip()
    if not summary:
        summary = "(no summary)"
    blocking = response.get("blocking_issues", [])
    required = response.get("required_changes", [])
    block_count = len(blocking) if isinstance(blocking, list) else 0
    req_count = len(required) if isinstance(required, list) else 0
    signoff = bool(response.get("signoff", False))
    return timestamp, f"{stage}: {summary}", block_count, req_count, signoff


def render_summary(identity: dict[str, Any], events: list[dict[str, Any]], notes_tail: str) -> str:
    lines: list[str] = []
    lines.append(f"# {identity['display_name']} Summary")
    lines.append("")
    lines.append(f"- Agent id: `{identity['id']}`")
    lines.append(f"- Model: `{identity['model']}`")
    lines.append(f"- Total events: `{len(events)}`")
    lines.append("")

    if not events:
        lines.append("No events logged yet.")
        lines.append("")
    else:
        last = events[-1]
        lines.append(f"- Last event timestamp: `{last.get('timestamp', 'unknown')}`")
        lines.append(f"- Last stage: `{last.get('stage', 'unknown')}`")
        lines.append("")
        lines.append("## Recent Activity")
        lines.append("")
        for event in events[-12:]:
            timestamp, summary, block_count, req_count, signoff = summarize_event(event)
            lines.append(f"- `{timestamp}` {summary}")
            lines.append(f"  blockers={block_count} required_changes={req_count} signoff={signoff}")
        lines.append("")

    lines.append("## Notes Tail")
    lines.append("")
    lines.append(notes_tail.strip() if notes_tail.strip() else "(no notes)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact Babel memory logs.")
    parser.add_argument("--config", default="orchestrator/round_config.json")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    config = load_json(config_path)

    identities = config.get("identities", {})
    if not isinstance(identities, dict):
        raise SystemExit("config identities must be an object")

    for agent_id, rel in identities.items():
        identity = load_json(repo_root / str(rel))
        memory = identity.get("memory", {})
        if not isinstance(memory, dict):
            continue
        event_log = repo_root / str(memory.get("event_log", ""))
        summary_path = repo_root / str(memory.get("summary", ""))
        notes_path = repo_root / f"memory/agents/{agent_id}/notes.md"
        events = read_jsonl(event_log)
        notes_tail = notes_path.read_text(encoding="utf-8")[-4000:] if notes_path.exists() else ""
        summary = render_summary(identity, events, notes_tail)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
        print(f"updated {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
