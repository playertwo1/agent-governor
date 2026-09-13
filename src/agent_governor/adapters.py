from __future__ import annotations

from typing import Any


def normalize(payload: dict[str, Any]) -> dict[str, str]:
    """Normalize Antigravity, Claude-style, and generic hook payloads."""
    call = payload.get("toolCall") or {}
    tool = call.get("name") or payload.get("tool_name") or payload.get("tool") or "unknown"
    args = call.get("args") or payload.get("tool_input") or payload.get("input") or {}
    command = args.get("CommandLine") or args.get("command") or ""
    path = (
        args.get("TargetFile") or args.get("AbsolutePath") or args.get("path")
        or args.get("file_path") or args.get("DirectoryPath") or ""
    )
    return {"tool": str(tool), "command": str(command), "path": str(path)}


def antigravity_output(decision: str, reason: str) -> dict[str, str]:
    allowed = {"allow", "deny", "ask", "force_ask", "deny_unless_prior_grant"}
    return {"decision": decision if decision in allowed else "deny", "reason": reason}
