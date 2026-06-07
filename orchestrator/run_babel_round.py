#!/usr/bin/env python3
"""Run a fully autonomous Babel collaboration round via Ollama."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
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
    return rows[-limit:] if limit > 0 else rows


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def read_text_tail(path: Path, max_lines: int = 30) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-max_lines:])


def load_reasoning_scaffold(repo_root: Path, identity: dict[str, Any]) -> str:
    raw = identity.get("reasoning_scaffold")
    if not isinstance(raw, str) or not raw.strip():
        return ""
    try:
        rel = safe_relative_path(raw)
    except ValueError:
        return ""
    path = repo_root / rel
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_self_config_paths(repo_root: Path, identity: dict[str, Any]) -> list[str]:
    raw = identity.get("self_config_paths")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            continue
        try:
            rel = safe_relative_path(item.strip())
        except ValueError:
            continue
        path = repo_root / rel
        if not path.exists() or not path.is_file():
            continue
        rel_posix = rel.as_posix()
        if rel_posix not in out:
            out.append(rel_posix)
    return out


def append_note(path: Path, round_id: str, stage: str, note: str) -> None:
    if not note.strip():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Agent Notes\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {utc_now()} {round_id} {stage}\n")
        handle.write(note.strip() + "\n")


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout_sec: int = 180,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, method=method, headers=headers)
    with request.urlopen(req, timeout=max(30, timeout_sec)) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def fetch_model_catalog(ollama_url: str) -> set[str]:
    data = http_json("GET", ollama_url.rstrip("/") + "/api/tags")
    out: set[str] = set()
    for model in data.get("models", []):
        name = model.get("name")
        if isinstance(name, str):
            out.add(name)
    return out


def generate_with_ollama(
    ollama_url: str,
    model: str,
    prompt: str,
    options: dict[str, Any],
    timeout_sec: int,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if options:
        payload["options"] = options
    data = http_json(
        "POST",
        ollama_url.rstrip("/") + "/api/generate",
        payload,
        timeout_sec=timeout_sec,
    )
    response = data.get("response", "")
    return response if isinstance(response, str) else ""


def extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for idx, char in enumerate(text):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    return None


def sanitize_for_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload.get("artifacts", [])
    artifact_view: list[dict[str, str]] = []
    if isinstance(artifacts, list):
        for item in artifacts:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            content = item.get("content")
            if isinstance(path, str) and isinstance(content, str):
                artifact_view.append({"path": path, "content_preview": content[:300]})

    return {
        "from": payload.get("from"),
        "to": payload.get("to"),
        "summary": payload.get("summary"),
        "decisions": payload.get("decisions", []),
        "blocking_issues": payload.get("blocking_issues", []),
        "required_changes": payload.get("required_changes", []),
        "signoff": payload.get("signoff", False),
        "memory_note": payload.get("memory_note", ""),
        "artifacts": artifact_view,
        "commit_message": payload.get("commit_message", ""),
    }


def stage_directive(stage: str) -> str:
    if stage == "pair_a_kickoff":
        return (
            "Produce initial language architecture decisions and hand off to nemotron. "
            "Set signoff=false."
        )
    if stage == "pair_a_finalize":
        return (
            "Refine Kimi output into an implementation-ready draft. "
            "Set signoff=true only if your draft is internally coherent."
        )
    if stage == "pair_b_review":
        return (
            "Audit Team A output critically. List concrete blocking_issues and required_changes. "
            "Set signoff=true only if no blocker remains."
        )
    if stage.startswith("pair_b_finalize") or stage.startswith("pair_b_remediate"):
        return (
            "Produce final artifacts as file entries and resolve all required changes. "
            "Return artifacts as objects with path and full content. "
            "Always include updated README.md and CHANGELOG.md artifacts for human-readable tracking. "
            "Include commit_message suitable for git commit. "
            "Set signoff=true only if your artifacts are ready to merge."
        )
    if stage == "pair_b_signoff" or stage.startswith("pair_b_resignoff"):
        return (
            "Perform final reviewer signoff on minimadmax artifacts. "
            "Set signoff=true only if ready for commit and push."
        )
    if stage == "implement":
        return (
            "The spec for this round is signed off. Produce RUNNABLE reference code that "
            "implements it. Return artifacts as objects with path and full content, written "
            "ONLY under reference/ (code) and reference/tests/ (unittest tests). Reuse "
            "orchestrator/canonical.py for canonical serialization; do not reinvent it. Do not "
            "modify frozen specs or autonomy-output/. Implement exactly what the spec defines; "
            "record assumptions where it is ambiguous. Include a commit_message. Set signoff=true "
            "only if the code is complete and its tests would pass."
        )
    return "Advance the task with precise output."


def as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def clip_text(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(value) <= limit:
        return value
    return value[:limit]


def clip_str_list(values: list[str], item_limit: int, max_items: int) -> list[str]:
    out: list[str] = []
    for item in values[:max_items]:
        out.append(clip_text(item, item_limit))
    return out


def apply_char_limits(response: dict[str, Any], limits: dict[str, Any]) -> dict[str, Any]:
    summary_limit = int(limits.get("summary", 2200))
    decision_item_limit = int(limits.get("decision_item", 500))
    blocking_item_limit = int(limits.get("blocking_item", 500))
    required_item_limit = int(limits.get("required_item", 500))
    memory_note_limit = int(limits.get("memory_note", 600))
    commit_message_limit = int(limits.get("commit_message", 180))
    list_items = int(limits.get("list_items", 12))
    artifact_count = int(limits.get("artifact_count", 8))
    artifact_path_limit = int(limits.get("artifact_path", 180))
    artifact_content_limit = int(limits.get("artifact_content", 8000))

    response["summary"] = clip_text(str(response.get("summary", "")), summary_limit)
    response["memory_note"] = clip_text(str(response.get("memory_note", "")), memory_note_limit)
    response["commit_message"] = clip_text(
        str(response.get("commit_message", "")), commit_message_limit
    )
    response["decisions"] = clip_str_list(
        as_str_list(response.get("decisions", [])), decision_item_limit, list_items
    )
    response["blocking_issues"] = clip_str_list(
        as_str_list(response.get("blocking_issues", [])), blocking_item_limit, list_items
    )
    response["required_changes"] = clip_str_list(
        as_str_list(response.get("required_changes", [])), required_item_limit, list_items
    )

    artifacts = response.get("artifacts", [])
    clipped_artifacts: list[dict[str, str]] = []
    if isinstance(artifacts, list):
        for item in artifacts[:artifact_count]:
            if not isinstance(item, dict):
                continue
            path = clip_text(str(item.get("path", "")), artifact_path_limit)
            content = clip_text(str(item.get("content", "")), artifact_content_limit)
            if path.strip():
                clipped_artifacts.append({"path": path.strip(), "content": content})
    response["artifacts"] = clipped_artifacts
    return response


def normalize_required_paths(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            continue
        try:
            rel = safe_relative_path(item.strip()).as_posix()
        except ValueError:
            continue
        if rel not in out:
            out.append(rel)
    return out


def artifact_paths(response: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for item in parse_artifacts(response.get("artifacts")):
        try:
            rel = safe_relative_path(item["path"]).as_posix()
        except ValueError:
            continue
        out.add(rel)
    return out


def enforce_required_artifacts(
    response: dict[str, Any], required_paths: list[str], char_limits: dict[str, Any]
) -> dict[str, Any]:
    if not required_paths:
        return response
    present = artifact_paths(response)
    missing = [path for path in required_paths if path not in present]
    if not missing:
        return response

    summary_prefix = "Required docs missing; signoff forced false."
    summary = str(response.get("summary", "")).strip()
    response["summary"] = f"{summary_prefix} {summary}".strip()

    blocker = f"Missing required docs artifacts: {', '.join(missing)}."
    blocking_issues = as_str_list(response.get("blocking_issues"))
    if blocker not in blocking_issues:
        blocking_issues.insert(0, blocker)
    response["blocking_issues"] = blocking_issues

    required_changes = as_str_list(response.get("required_changes"))
    for path in missing:
        change = f"Add or update {path} with human-readable round updates."
        if change not in required_changes:
            required_changes.append(change)
    response["required_changes"] = required_changes
    response["signoff"] = False
    return apply_char_limits(response, char_limits)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if isinstance(value, (int, float)):
        return value != 0
    return False


def parse_artifacts(value: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not isinstance(value, list):
        return out
    for item in value:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        content = item.get("content")
        if isinstance(path, str) and path.strip() and isinstance(content, str):
            out.append({"path": path.strip(), "content": content})
    return out


def normalize_response(
    candidate: dict[str, Any] | None,
    fallback_from: str,
    fallback_to: str,
    stage: str,
    raw: str,
) -> dict[str, Any]:
    if candidate is None:
        return {
            "from": fallback_from,
            "to": fallback_to,
            "summary": raw.strip()[:1600] or "No valid JSON returned.",
            "decisions": [],
            "blocking_issues": ["Model did not return valid JSON."],
            "required_changes": [],
            "memory_note": "Model response parse failure.",
            "signoff": False,
            "artifacts": [],
            "commit_message": "",
            "stage": stage,
        }
    return {
        "from": str(candidate.get("from") or fallback_from),
        "to": str(candidate.get("to") or fallback_to),
        "summary": str(candidate.get("summary") or ""),
        "decisions": as_str_list(candidate.get("decisions")),
        "blocking_issues": as_str_list(candidate.get("blocking_issues")),
        "required_changes": as_str_list(candidate.get("required_changes")),
        "memory_note": str(candidate.get("memory_note") or ""),
        "signoff": as_bool(candidate.get("signoff")),
        "artifacts": parse_artifacts(candidate.get("artifacts")),
        "commit_message": str(candidate.get("commit_message") or ""),
        "stage": stage,
    }


def build_model_failure_response(
    *,
    fallback_from: str,
    fallback_to: str,
    stage: str,
    attempts: int,
    errors_seen: list[str],
) -> dict[str, Any]:
    recent_errors = errors_seen[-3:] if errors_seen else ["unknown model call error"]
    detail = " | ".join(recent_errors)
    return {
        "from": fallback_from,
        "to": fallback_to,
        "summary": f"Agent runtime failure after {attempts} model call attempts.",
        "decisions": [],
        "blocking_issues": [f"Model call failed: {detail}"],
        "required_changes": [
            "Retry this stage after model endpoint stabilizes.",
            "Continue with fail-safe path and keep signoff=false until retry succeeds.",
        ],
        "memory_note": f"Model call failure at stage {stage}: {detail}",
        "signoff": False,
        "artifacts": [],
        "commit_message": "",
        "stage": stage,
    }


def build_prompt(
    identity: dict[str, Any],
    stage: str,
    task: str,
    next_owner: str,
    incoming: list[dict[str, Any]],
    shared_recent: list[dict[str, Any]],
    agent_recent: list[dict[str, Any]],
    notes_tail: str,
    char_limits: dict[str, Any],
    reasoning_scaffold: str,
    scaffold_max_chars: int,
    self_config_paths: list[str],
) -> str:
    payload = {
        "from": identity["id"],
        "to": next_owner,
        "summary": "Concise stage output summary.",
        "decisions": ["Decision 1", "Decision 2"],
        "blocking_issues": ["Issue if any"],
        "required_changes": ["Required change if any"],
        "memory_note": "Short durable note for future sessions.",
        "signoff": False,
        "artifacts": [{"path": "autonomy-output/example.md", "content": "file content"}],
        "commit_message": "Commit message if artifacts are ready",
    }

    in_view = [sanitize_for_prompt(item) for item in incoming][-6:]
    shared_view = [sanitize_for_prompt(item.get("response", {})) for item in shared_recent][-8:]
    agent_view = [sanitize_for_prompt(item.get("response", {})) for item in agent_recent][-8:]

    lines: list[str] = []
    lines.append("You are running in a fully autonomous multi-agent engineering workflow.")
    lines.append("There is no human in the loop for planning, approval, signoff, or execution.")
    lines.append("Do not request human input, human review, or human signoff.")
    lines.append("Only model-to-model handoff and signoff are valid.")
    lines.append(f"Stage: {stage}")
    lines.append(f"Task: {task}")
    lines.append(f"Agent id: {identity['id']}")
    lines.append(f"Display name: {identity['display_name']}")
    lines.append(f"Role: {identity['role']}")
    lines.append("Goals:")
    for goal in identity.get("goals", []):
        lines.append(f"- {goal}")
    lines.append("Constraints:")
    for constraint in identity.get("constraints", []):
        lines.append(f"- {constraint}")
    lines.append(f"Next owner: {next_owner}")
    lines.append("Directive:")
    lines.append(stage_directive(stage))
    if self_config_paths:
        lines.append("")
        lines.append("Self-configuration authority:")
        lines.append(
            "You may update your own configuration by returning artifacts with full file content for these paths:"
        )
        lines.append(json.dumps(self_config_paths, ensure_ascii=True))
        lines.append(
            "If this stage is not producing artifacts, put requested config edits in required_changes so the next artifact-writing stage can apply them."
        )
        lines.append("Do not request human approval for config edits.")
    if reasoning_scaffold and scaffold_max_chars > 0:
        lines.append("")
        lines.append("Reasoning scaffold (follow exactly; keep output content grounded in current repo context):")
        lines.append(reasoning_scaffold[:scaffold_max_chars])
    lines.append("")
    lines.append("Recent incoming collaboration context:")
    lines.append(json.dumps(in_view, ensure_ascii=True))
    lines.append("")
    lines.append("Recent shared memory:")
    lines.append(json.dumps(shared_view, ensure_ascii=True))
    lines.append("")
    lines.append("Recent self memory:")
    lines.append(json.dumps(agent_view, ensure_ascii=True))
    lines.append("")
    lines.append("Current notes tail:")
    lines.append(notes_tail[:3500] if notes_tail else "(none)")
    lines.append("")
    lines.append("Return a valid JSON object only. No markdown fences.")
    lines.append("Schema example:")
    lines.append(json.dumps(payload, ensure_ascii=True))
    lines.append("If no artifacts are needed for this stage, return artifacts as [].")
    lines.append("Hard character limits:")
    lines.append(json.dumps(char_limits, ensure_ascii=True))
    lines.append("Never exceed these limits.")
    return "\n".join(lines)


def call_agent(
    *,
    stage: str,
    task: str,
    next_owner: str,
    identity: dict[str, Any],
    incoming: list[dict[str, Any]],
    ollama_url: str,
    request_options: dict[str, Any],
    shared_log: Path,
    max_recent_events: int,
    round_id: str,
    repo_root: Path,
    char_limits: dict[str, Any],
    scaffold_max_chars: int,
    model_timeout_sec: int,
    model_max_retries: int,
    model_retry_backoff_sec: float,
) -> dict[str, Any]:
    agent_id = str(identity["id"])
    memory = identity["memory"]
    agent_log = repo_root / str(memory["event_log"])
    notes_path = repo_root / f"memory/agents/{agent_id}/notes.md"
    shared_recent = read_jsonl(shared_log, max_recent_events)
    agent_recent = read_jsonl(agent_log, max_recent_events)
    notes_tail = read_text_tail(notes_path, max_lines=40)
    reasoning_scaffold = load_reasoning_scaffold(repo_root, identity)
    self_config_paths = load_self_config_paths(repo_root, identity)

    prompt = build_prompt(
        identity=identity,
        stage=stage,
        task=task,
        next_owner=next_owner,
        incoming=incoming,
        shared_recent=shared_recent,
        agent_recent=agent_recent,
        notes_tail=notes_tail,
        char_limits=char_limits,
        reasoning_scaffold=reasoning_scaffold,
        scaffold_max_chars=scaffold_max_chars,
        self_config_paths=self_config_paths,
    )
    started = time.monotonic()
    print(
        f"[{utc_now()}] stage={stage} agent={agent_id} model={identity['model']} status=start",
        file=sys.stderr,
        flush=True,
    )
    attempt_count = max(1, int(model_max_retries) + 1)
    retry_backoff = max(0.0, float(model_retry_backoff_sec))
    transport_errors: list[str] = []
    raw = ""
    for attempt_idx in range(1, attempt_count + 1):
        try:
            raw = generate_with_ollama(
                ollama_url=ollama_url,
                model=str(identity["model"]),
                prompt=prompt,
                options=request_options,
                timeout_sec=model_timeout_sec,
            )
            break
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            err_msg = f"{type(exc).__name__}: {exc}"
            transport_errors.append(err_msg)
            print(
                f"[{utc_now()}] stage={stage} agent={agent_id} model={identity['model']} status=retry attempt={attempt_idx}/{attempt_count} error={err_msg}",
                file=sys.stderr,
                flush=True,
            )
            if attempt_idx < attempt_count and retry_backoff > 0:
                time.sleep(retry_backoff * attempt_idx)
    else:
        elapsed = time.monotonic() - started
        response = build_model_failure_response(
            fallback_from=agent_id,
            fallback_to=next_owner,
            stage=stage,
            attempts=attempt_count,
            errors_seen=transport_errors,
        )
        response = apply_char_limits(response, char_limits)
        event = {
            "timestamp": utc_now(),
            "round_id": round_id,
            "stage": stage,
            "task": task,
            "agent_id": agent_id,
            "model": identity["model"],
            "incoming": [sanitize_for_prompt(item) for item in incoming][-6:],
            "response": response,
            "raw_response": "",
            "transport_errors": transport_errors,
        }
        append_jsonl(agent_log, event)
        append_jsonl(shared_log, event)
        append_note(notes_path, round_id, stage, response.get("memory_note", ""))
        print(
            f"[{utc_now()}] stage={stage} agent={agent_id} model={identity['model']} status=done elapsed_sec={elapsed:.1f} signoff={response.get('signoff', False)} transport_failures={len(transport_errors)}",
            file=sys.stderr,
            flush=True,
        )
        return response

    elapsed = time.monotonic() - started
    candidate = extract_json_object(raw)
    response = normalize_response(
        candidate=candidate,
        fallback_from=agent_id,
        fallback_to=next_owner,
        stage=stage,
        raw=raw,
    )
    response = apply_char_limits(response, char_limits)
    event = {
        "timestamp": utc_now(),
        "round_id": round_id,
        "stage": stage,
        "task": task,
        "agent_id": agent_id,
        "model": identity["model"],
        "incoming": [sanitize_for_prompt(item) for item in incoming][-6:],
        "response": response,
        "raw_response": raw,
        "transport_errors": transport_errors,
    }
    append_jsonl(agent_log, event)
    append_jsonl(shared_log, event)
    append_note(notes_path, round_id, stage, response.get("memory_note", ""))
    print(
        f"[{utc_now()}] stage={stage} agent={agent_id} model={identity['model']} status=done elapsed_sec={elapsed:.1f} signoff={response.get('signoff', False)} retries_used={len(transport_errors)}",
        file=sys.stderr,
        flush=True,
    )
    return response


def safe_relative_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        raise ValueError(f"absolute paths are not allowed: {raw_path}")
    normalized = Path()
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError(f"parent traversal is not allowed: {raw_path}")
        normalized /= part
    if not str(normalized):
        raise ValueError(f"invalid empty path: {raw_path}")
    return normalized


def write_artifacts(repo_root: Path, artifacts: list[dict[str, str]]) -> list[str]:
    written: list[str] = []
    for artifact in artifacts:
        rel = safe_relative_path(artifact["path"])
        target = repo_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact["content"], encoding="utf-8")
        written.append(str(rel))
    return written


def write_failure_report(
    repo_root: Path,
    round_id: str,
    task: str,
    minimadmax: dict[str, Any],
    deepseek: dict[str, Any],
) -> list[str]:
    rel = Path("autonomy-output") / "failed" / f"round-{round_id}.md"
    target = repo_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    content = [
        f"# Babel Autonomous Round {round_id} Failed Signoff",
        "",
        f"Task: {task}",
        "",
        "## Minimadmax",
        f"- signoff: {minimadmax.get('signoff', False)}",
        f"- summary: {minimadmax.get('summary', '')}",
        "- blocking_issues:",
    ]
    for issue in minimadmax.get("blocking_issues", []):
        content.append(f"  - {issue}")
    content.extend(
        [
            "",
            "## DeepSeek",
            f"- signoff: {deepseek.get('signoff', False)}",
            f"- summary: {deepseek.get('summary', '')}",
            "- blocking_issues:",
        ]
    )
    for issue in deepseek.get("blocking_issues", []):
        content.append(f"  - {issue}")
    content.append("")
    target.write_text("\n".join(content), encoding="utf-8")
    return [str(rel)]


def run_cmd(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(args, cwd=str(cwd), check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def git_current_branch(repo_root: Path) -> str:
    return run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)


def extract_commit_sha(text: str) -> str | None:
    matches = re.findall(r"\b[0-9a-f]{40}\b", text.lower())
    if not matches:
        return None
    return matches[-1]


def has_no_changes_sentinel(text: str) -> bool:
    for line in text.splitlines():
        if line.strip() == "NO_CHANGES":
            return True
    return False


def commit_and_push_via_model(
    *,
    repo_root: Path,
    files: list[str],
    commit_message: str,
    remote: str,
    branch: str,
    do_push: bool,
    codex_launcher: str,
    model: str,
    timeout_sec: int,
) -> dict[str, Any]:
    if not files:
        return {"committed": False, "reason": "no files"}

    files_arg = " ".join(shlex.quote(path) for path in files)
    push_line = f"git push {shlex.quote(remote)} {shlex.quote(branch)}" if do_push else "echo SKIP_PUSH"
    commit_arg = shlex.quote(commit_message)

    prompt = "\n".join(
        [
            "Execute these shell commands exactly in order in the current repository:",
            f"git add -- {files_arg}",
            "if git diff --cached --quiet; then echo NO_CHANGES; exit 0; fi",
            f"git commit -m {commit_arg}",
            push_line,
            "git rev-parse HEAD",
            "",
            "Reply with ONLY one line:",
            "- NO_CHANGES",
            "- or the full 40-character commit SHA",
            "No extra text.",
        ]
    )

    cmd = [
        codex_launcher,
        "--oss",
        "--local-provider",
        "ollama",
        "-m",
        model,
        "exec",
        "--skip-git-repo-check",
        prompt,
    ]
    print(
        f"[{utc_now()}] stage=git_delegate model={model} launcher={codex_launcher} status=start",
        file=sys.stderr,
        flush=True,
    )
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        timeout=max(30, timeout_sec),
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    print(
        f"[{utc_now()}] stage=git_delegate model={model} status=done rc={proc.returncode}",
        file=sys.stderr,
        flush=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"model delegate git command failed (rc={proc.returncode})\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    if has_no_changes_sentinel(combined):
        return {"committed": False, "reason": "no staged diff", "delegate_model": model, "files": files}

    commit_sha = extract_commit_sha(combined)
    if not commit_sha:
        tail = "\n".join(combined.splitlines()[-40:])
        raise RuntimeError(f"model delegate did not return a commit SHA.\nOutput tail:\n{tail}")

    return {
        "committed": True,
        "commit_sha": commit_sha,
        "pushed": do_push,
        "remote": remote,
        "branch": branch,
        "delegate_model": model,
        "files": files,
    }


def commit_and_push(
    *,
    repo_root: Path,
    files: list[str],
    commit_message: str,
    remote: str,
    branch: str,
    do_push: bool,
) -> dict[str, Any]:
    if not files:
        return {"committed": False, "reason": "no files"}

    run_cmd(["git", "add", "--"] + files, cwd=repo_root)
    staged = run_cmd(["git", "diff", "--cached", "--name-only"], cwd=repo_root)
    if not staged.strip():
        return {"committed": False, "reason": "no staged diff"}

    run_cmd(["git", "commit", "-m", commit_message], cwd=repo_root)
    commit_sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_root)

    # Push is best-effort and must never fail the round. If the remote has
    # diverged (e.g. a manual edit on GitHub), reconcile by rebasing onto it
    # first; --autostash keeps in-round memory/notes changes out of the way.
    push_output = ""
    pushed = False
    if do_push:
        def _git(*cargs: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *cargs], cwd=str(repo_root), check=False, capture_output=True, text=True
            )

        _git("fetch", remote, branch)
        rebase = _git("rebase", "--autostash", f"{remote}/{branch}")
        if rebase.returncode != 0:
            _git("rebase", "--abort")
            push_output = f"push skipped: rebase onto {remote}/{branch} failed (manual reconcile needed)"
            print(f"[{utc_now()}] stage=git status=push_skipped reason=rebase_conflict", file=sys.stderr, flush=True)
        else:
            push = _git("push", remote, branch)
            if push.returncode == 0:
                pushed = True
                push_output = push.stdout.strip()
            else:
                push_output = f"push failed: {push.stderr.strip()}"
                print(f"[{utc_now()}] stage=git status=push_failed detail={push.stderr.strip()[:200]}", file=sys.stderr, flush=True)
        commit_sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_root)

    return {
        "committed": True,
        "commit_sha": commit_sha,
        "pushed": pushed,
        "remote": remote,
        "branch": branch,
        "push_output": push_output,
        "files": files,
    }


def load_identity_map(config: dict[str, Any], repo_root: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if "identities" in config and isinstance(config["identities"], dict):
        for agent_id, rel in config["identities"].items():
            path = repo_root / str(rel)
            out[str(agent_id)] = load_json(path)
        return out

    agents = config.get("agents", [])
    for item in agents:
        if not isinstance(item, dict):
            continue
        agent_id = str(item.get("id", ""))
        rel = item.get("identity")
        if not agent_id or not isinstance(rel, str):
            continue
        out[agent_id] = load_json(repo_root / rel)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a fully autonomous Babel round.")
    parser.add_argument("--task", required=True, help="Top-level task for this autonomous run.")
    parser.add_argument("--config", default="orchestrator/round_config.json")
    parser.add_argument("--round-id", default=None)
    parser.add_argument("--max-signoff-loops", type=int, default=None)
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--no-git", action="store_true", help="Run collaboration and memory updates without commit/push.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    config = load_json(config_path)

    ollama_url = str(config.get("ollama_url", "http://127.0.0.1:11434"))
    request_options = config.get("request", {})
    max_recent_events = int(config.get("max_recent_events", 10))
    char_limits = config.get("char_limits", {})
    if not isinstance(char_limits, dict):
        char_limits = {}
    scaffold_max_chars = int(config.get("scaffold_max_chars", 5000))
    if scaffold_max_chars < 0:
        scaffold_max_chars = 0
    model_call_cfg = config.get("model_call", {})
    if not isinstance(model_call_cfg, dict):
        model_call_cfg = {}
    model_timeout_sec = int(model_call_cfg.get("timeout_sec", 180))
    if model_timeout_sec < 30:
        model_timeout_sec = 30
    model_max_retries = int(model_call_cfg.get("max_retries", 2))
    if model_max_retries < 0:
        model_max_retries = 0
    model_retry_backoff_sec = float(model_call_cfg.get("retry_backoff_sec", 4.0))
    if model_retry_backoff_sec < 0:
        model_retry_backoff_sec = 0.0
    required_human_docs = normalize_required_paths(
        config.get("required_human_docs", ["README.md", "CHANGELOG.md"])
    )
    shared_log = repo_root / str(config.get("shared_memory_log", "memory/shared/context.jsonl"))
    session_log = repo_root / str(config.get("session_log", "memory/shared/sessions.jsonl"))

    teams = config.get("teams", {})
    pair_a = teams.get("pair_a", ["kimi", "nemotron"])
    pair_b = teams.get("pair_b", ["deepseek", "minimadmax"])
    if not (isinstance(pair_a, list) and len(pair_a) == 2 and isinstance(pair_b, list) and len(pair_b) == 2):
        print("error: teams.pair_a and teams.pair_b must each contain exactly two agent ids", file=sys.stderr)
        return 2

    identity_map = load_identity_map(config, repo_root)
    required_agents = [str(pair_a[0]), str(pair_a[1]), str(pair_b[0]), str(pair_b[1])]
    for agent_id in required_agents:
        if agent_id not in identity_map:
            print(f"error: missing identity for agent id: {agent_id}", file=sys.stderr)
            return 3

    # Optional post-signoff implementer (writes reference code). Non-fatal if absent.
    implementer_raw = teams.get("implementer")
    implementer_id = str(implementer_raw).strip() if implementer_raw else ""
    if implementer_id and implementer_id not in identity_map:
        print(f"warning: implementer '{implementer_id}' has no identity; skipping implement stage", file=sys.stderr)
        implementer_id = ""

    try:
        available_models = fetch_model_catalog(ollama_url)
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"error: failed to reach Ollama: {exc}", file=sys.stderr)
        return 4

    for agent_id in required_agents:
        model = str(identity_map[agent_id]["model"])
        if model not in available_models:
            print(f"error: model not installed in Ollama: {model}", file=sys.stderr)
            return 5

    if implementer_id:
        impl_model = str(identity_map[implementer_id]["model"])
        if impl_model not in available_models:
            print(f"warning: implementer model not installed: {impl_model}; skipping implement stage", file=sys.stderr)
            implementer_id = ""

    round_id = args.round_id or uuid.uuid4().hex[:12]
    max_loops = args.max_signoff_loops or int(config.get("max_signoff_loops", 3))
    max_loops = max(1, max_loops)

    kimi_id, nemotron_id = str(pair_a[0]), str(pair_a[1])
    deepseek_id, minimadmax_id = str(pair_b[0]), str(pair_b[1])

    kimi = call_agent(
        stage="pair_a_kickoff",
        task=args.task,
        next_owner=nemotron_id,
        identity=identity_map[kimi_id],
        incoming=[],
        ollama_url=ollama_url,
        request_options=request_options,
        shared_log=shared_log,
        max_recent_events=max_recent_events,
        round_id=round_id,
        repo_root=repo_root,
        char_limits=char_limits,
        scaffold_max_chars=scaffold_max_chars,
        model_timeout_sec=model_timeout_sec,
        model_max_retries=model_max_retries,
        model_retry_backoff_sec=model_retry_backoff_sec,
    )

    nemotron = call_agent(
        stage="pair_a_finalize",
        task=args.task,
        next_owner=deepseek_id,
        identity=identity_map[nemotron_id],
        incoming=[kimi],
        ollama_url=ollama_url,
        request_options=request_options,
        shared_log=shared_log,
        max_recent_events=max_recent_events,
        round_id=round_id,
        repo_root=repo_root,
        char_limits=char_limits,
        scaffold_max_chars=scaffold_max_chars,
        model_timeout_sec=model_timeout_sec,
        model_max_retries=model_max_retries,
        model_retry_backoff_sec=model_retry_backoff_sec,
    )

    deepseek_review = call_agent(
        stage="pair_b_review",
        task=args.task,
        next_owner=minimadmax_id,
        identity=identity_map[deepseek_id],
        incoming=[kimi, nemotron],
        ollama_url=ollama_url,
        request_options=request_options,
        shared_log=shared_log,
        max_recent_events=max_recent_events,
        round_id=round_id,
        repo_root=repo_root,
        char_limits=char_limits,
        scaffold_max_chars=scaffold_max_chars,
        model_timeout_sec=model_timeout_sec,
        model_max_retries=model_max_retries,
        model_retry_backoff_sec=model_retry_backoff_sec,
    )

    minimadmax = call_agent(
        stage="pair_b_finalize",
        task=args.task,
        next_owner=deepseek_id,
        identity=identity_map[minimadmax_id],
        incoming=[nemotron, deepseek_review],
        ollama_url=ollama_url,
        request_options=request_options,
        shared_log=shared_log,
        max_recent_events=max_recent_events,
        round_id=round_id,
        repo_root=repo_root,
        char_limits=char_limits,
        scaffold_max_chars=scaffold_max_chars,
        model_timeout_sec=model_timeout_sec,
        model_max_retries=model_max_retries,
        model_retry_backoff_sec=model_retry_backoff_sec,
    )
    minimadmax = enforce_required_artifacts(minimadmax, required_human_docs, char_limits)

    deepseek_signoff = call_agent(
        stage="pair_b_signoff",
        task=args.task,
        next_owner="git",
        identity=identity_map[deepseek_id],
        incoming=[minimadmax, deepseek_review],
        ollama_url=ollama_url,
        request_options=request_options,
        shared_log=shared_log,
        max_recent_events=max_recent_events,
        round_id=round_id,
        repo_root=repo_root,
        char_limits=char_limits,
        scaffold_max_chars=scaffold_max_chars,
        model_timeout_sec=model_timeout_sec,
        model_max_retries=model_max_retries,
        model_retry_backoff_sec=model_retry_backoff_sec,
    )

    attempt = 1
    while (not minimadmax.get("signoff") or not deepseek_signoff.get("signoff")) and attempt < max_loops:
        attempt += 1
        minimadmax = call_agent(
            stage=f"pair_b_remediate_{attempt}",
            task=args.task,
            next_owner=deepseek_id,
            identity=identity_map[minimadmax_id],
            incoming=[nemotron, deepseek_review, deepseek_signoff, minimadmax],
            ollama_url=ollama_url,
            request_options=request_options,
            shared_log=shared_log,
            max_recent_events=max_recent_events,
            round_id=round_id,
            repo_root=repo_root,
            char_limits=char_limits,
            scaffold_max_chars=scaffold_max_chars,
            model_timeout_sec=model_timeout_sec,
            model_max_retries=model_max_retries,
            model_retry_backoff_sec=model_retry_backoff_sec,
        )
        minimadmax = enforce_required_artifacts(minimadmax, required_human_docs, char_limits)
        deepseek_signoff = call_agent(
            stage=f"pair_b_resignoff_{attempt}",
            task=args.task,
            next_owner="git",
            identity=identity_map[deepseek_id],
            incoming=[minimadmax, deepseek_signoff],
            ollama_url=ollama_url,
            request_options=request_options,
            shared_log=shared_log,
            max_recent_events=max_recent_events,
            round_id=round_id,
            repo_root=repo_root,
            char_limits=char_limits,
            scaffold_max_chars=scaffold_max_chars,
            model_timeout_sec=model_timeout_sec,
            model_max_retries=model_max_retries,
            model_retry_backoff_sec=model_retry_backoff_sec,
        )

    dual_signoff = bool(minimadmax.get("signoff")) and bool(deepseek_signoff.get("signoff"))

    files_to_commit: list[str]
    commit_message: str
    if dual_signoff:
        artifacts = minimadmax.get("artifacts", [])
        if artifacts:
            files_to_commit = write_artifacts(repo_root, artifacts)
        else:
            fallback = {
                "path": f"autonomy-output/round-{round_id}.md",
                "content": "\n".join(
                    [
                        f"# Babel Round {round_id}",
                        "",
                        f"Task: {args.task}",
                        "",
                        "## Kimi Summary",
                        str(kimi.get("summary", "")),
                        "",
                        "## Nemotron Summary",
                        str(nemotron.get("summary", "")),
                        "",
                        "## DeepSeek Summary",
                        str(deepseek_signoff.get("summary", "")),
                        "",
                        "## MiniMadMax Summary",
                        str(minimadmax.get("summary", "")),
                        "",
                    ]
                ),
            }
            files_to_commit = write_artifacts(repo_root, [fallback])
        commit_message = minimadmax.get("commit_message", "").strip() or f"Babel autonomy round {round_id}"

        # Post-signoff implementer: turn the approved spec into runnable reference code.
        # Fully non-fatal — a coder failure must never block the spec commit.
        if implementer_id:
            try:
                spec_blocks: list[str] = []
                budget = 24000
                for art in minimadmax.get("artifacts", []):
                    if not isinstance(art, dict):
                        continue
                    p, c = str(art.get("path", "")), str(art.get("content", ""))
                    if not p or not c:
                        continue
                    chunk = f"\n=== FILE: {p} ===\n{c}\n"
                    if budget - len(chunk) < 0:
                        break
                    spec_blocks.append(chunk)
                    budget -= len(chunk)
                coder_task = (
                    f"{args.task}\n\n"
                    "The following Babel specification artifacts were signed off this round. "
                    "Implement runnable, tested reference code for them under reference/.\n"
                    + "".join(spec_blocks)
                )
                coder = call_agent(
                    stage="implement",
                    task=coder_task,
                    next_owner="git",
                    identity=identity_map[implementer_id],
                    incoming=[minimadmax, deepseek_signoff],
                    ollama_url=ollama_url,
                    request_options=request_options,
                    shared_log=shared_log,
                    max_recent_events=max_recent_events,
                    round_id=round_id,
                    repo_root=repo_root,
                    char_limits=char_limits,
                    scaffold_max_chars=scaffold_max_chars,
                    model_timeout_sec=model_timeout_sec,
                    model_max_retries=model_max_retries,
                    model_retry_backoff_sec=model_retry_backoff_sec,
                )
                raw_code_arts = coder.get("artifacts", []) if isinstance(coder.get("artifacts"), list) else []
                code_artifacts = [
                    a for a in raw_code_arts
                    if isinstance(a, dict) and str(a.get("path", "")).startswith("reference/")
                ]
                dropped = len(raw_code_arts) - len(code_artifacts)
                if dropped:
                    print(f"[{utc_now()}] stage=implement note=dropped_{dropped}_non_reference_artifacts", file=sys.stderr, flush=True)
                if code_artifacts:
                    code_files = write_artifacts(repo_root, code_artifacts)
                    files_to_commit = list(dict.fromkeys(files_to_commit + code_files))
                    print(f"[{utc_now()}] stage=implement status=wrote files={len(code_files)}", file=sys.stderr, flush=True)
                else:
                    print(f"[{utc_now()}] stage=implement status=no_reference_artifacts", file=sys.stderr, flush=True)
            except Exception as exc:  # noqa: BLE001 - never block the spec commit
                print(f"[{utc_now()}] stage=implement status=error error={type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    else:
        files_to_commit = write_failure_report(repo_root, round_id, args.task, minimadmax, deepseek_signoff)
        commit_message = f"Babel autonomy round {round_id} failed dual signoff"

    git_cfg = config.get("git", {})
    if not isinstance(git_cfg, dict):
        git_cfg = {}
    remote = str(git_cfg.get("remote", "origin"))
    branch = str(git_cfg.get("branch", "")).strip() or git_current_branch(repo_root)
    do_commit = (not args.no_git) and bool(git_cfg.get("auto_commit", True))
    do_push = (not args.no_push) and bool(git_cfg.get("auto_push", True))
    commit_mode = str(git_cfg.get("mode", "model_delegate")).strip().lower()
    executor_agent = str(git_cfg.get("executor_agent", minimadmax_id)).strip() or minimadmax_id
    if executor_agent not in identity_map:
        print(f"error: git.executor_agent is unknown: {executor_agent}", file=sys.stderr)
        return 6
    delegate_model = str(identity_map[executor_agent]["model"])
    codex_launcher = str(git_cfg.get("codex_launcher", "/root/ai-lab/bin/codex-github"))
    delegate_timeout_sec = int(git_cfg.get("delegate_timeout_sec", 900))

    if do_commit:
        if commit_mode == "direct":
            commit_result = commit_and_push(
                repo_root=repo_root,
                files=files_to_commit,
                commit_message=commit_message,
                remote=remote,
                branch=branch,
                do_push=do_push,
            )
        else:
            commit_result = commit_and_push_via_model(
                repo_root=repo_root,
                files=files_to_commit,
                commit_message=commit_message,
                remote=remote,
                branch=branch,
                do_push=do_push,
                codex_launcher=codex_launcher,
                model=delegate_model,
                timeout_sec=delegate_timeout_sec,
            )
    else:
        commit_result = {
            "committed": False,
            "pushed": False,
            "reason": "git disabled by flag or config",
            "files": files_to_commit,
        }

    session_summary = {
        "timestamp": utc_now(),
        "round_id": round_id,
        "task": args.task,
        "pair_a": {
            "kimi": sanitize_for_prompt(kimi),
            "nemotron": sanitize_for_prompt(nemotron),
        },
        "pair_b": {
            "deepseek_review": sanitize_for_prompt(deepseek_review),
            "minimadmax": sanitize_for_prompt(minimadmax),
            "deepseek_signoff": sanitize_for_prompt(deepseek_signoff),
        },
        "dual_signoff": dual_signoff,
        "attempts": attempt,
        "files_to_commit": files_to_commit,
        "commit_result": commit_result,
    }
    append_jsonl(session_log, session_summary)

    print(json.dumps(session_summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
