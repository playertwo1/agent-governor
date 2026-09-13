from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when a governance document is syntactically valid but unsafe."""


KNOWN_TOOLS = {
    "run_command", "write_to_file", "replace_file_content", "multi_replace_file_content",
    "view_file", "list_dir", "find_by_name", "grep_search", "Write", "Edit", "MultiEdit", "Read",
}


@dataclass(frozen=True)
class Decision:
    decision: str
    reason: str
    rule_id: str = "DEFAULT"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path.name} must contain a JSON object")
    return value


def validate_documents(policy: dict[str, Any], contract: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1 or contract.get("schema_version") != 1:
        raise ConfigurationError("unsupported governance schema_version")
    if policy.get("default_decision") not in {"allow", "ask", "force_ask", "deny", "deny_unless_prior_grant"}:
        raise ConfigurationError("invalid default_decision")
    if not isinstance(policy.get("write_tools"), list) or not all(isinstance(x, str) for x in policy["write_tools"]):
        raise ConfigurationError("write_tools must be a list of strings")
    if not isinstance(policy.get("protected_paths"), list) or not all(isinstance(x, str) for x in policy["protected_paths"]):
        raise ConfigurationError("protected_paths must be a list of strings")
    rules = policy.get("command_rules")
    if not isinstance(rules, list):
        raise ConfigurationError("command_rules must be a list")
    decisions = {"allow", "ask", "force_ask", "deny", "deny_unless_prior_grant"}
    for rule in rules:
        if not isinstance(rule, dict) or not all(isinstance(rule.get(k), str) for k in ("id", "decision", "reason")):
            raise ConfigurationError("each command rule requires string id, decision and reason")
        if rule["decision"] not in decisions or not isinstance(rule.get("patterns"), list) or not all(isinstance(x, str) for x in rule["patterns"]):
            raise ConfigurationError(f"invalid command rule: {rule.get('id', '<unknown>')}")
        for pattern in rule["patterns"]:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ConfigurationError(f"invalid regex in {rule['id']}: {exc}") from exc
    if not isinstance(contract.get("task_id"), str) or not isinstance(contract.get("allowed_paths"), list) or not all(isinstance(x, str) for x in contract["allowed_paths"]):
        raise ConfigurationError("task_id and allowed_paths have invalid types")
    if not isinstance(contract.get("forbidden_paths"), list) or not all(isinstance(x, str) for x in contract["forbidden_paths"]):
        raise ConfigurationError("forbidden_paths must be a list of strings")
    if not isinstance(contract.get("max_files_changed"), int) or contract["max_files_changed"] < 0:
        raise ConfigurationError("max_files_changed must be a non-negative integer")
    if not isinstance(contract.get("required_commands", []), list) or not all(isinstance(x, str) and x.strip() for x in contract.get("required_commands", [])):
        raise ConfigurationError("required_commands must be a list of non-empty strings")


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema_version") != 1 or not isinstance(profile.get("name"), str) or not profile["name"]:
        raise ConfigurationError("invalid project profile")
    for field in ("stack", "test_commands", "protected_areas"):
        if not isinstance(profile.get(field, []), list) or not all(isinstance(x, str) for x in profile.get(field, [])):
            raise ConfigurationError(f"profile {field} must be a list of strings")


def append_event(root: Path, event: dict[str, Any]) -> None:
    log = root / ".governor" / "violations.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    try:
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        # Logging must never turn a deterministic deny into an unstructured crash.
        pass


def _matches(value: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns)


def _safe_relative(root: Path, value: str) -> str | None:
    if not value:
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return str(candidate.resolve(strict=False).relative_to(root.resolve())).replace("\\", "/")
    except (ValueError, OSError, RuntimeError):
        return None


def evaluate(root: Path, action: dict[str, str]) -> Decision:
    policy_path = root / ".governor" / "policy.json"
    contract_path = root / ".governor" / "task-contract.json"
    if not policy_path.exists() or not contract_path.exists():
        return Decision("deny", "Governor configuration is missing; refusing to fail open.", "CFG-001")

    try:
        policy = load_json(policy_path)
        contract = load_json(contract_path)
        validate_documents(policy, contract)
        profile_path = root / ".governor" / "project-profile.json"
        if not profile_path.exists():
            return Decision("deny", "Project profile is missing; refusing to fail open.", "CFG-003")
        profile = load_json(profile_path)
        validate_profile(profile)
    except (OSError, ValueError, TypeError) as exc:
        return Decision("deny", f"Governor configuration is invalid: {exc}", "CFG-002")

    if not isinstance(action, dict) or not all(isinstance(action.get(key, ""), str) for key in ("tool", "command", "path")):
        return Decision("deny", "Action payload has invalid types.", "INPUT-001")
    command = action.get("command", "")
    raw_path = action.get("path", "")
    tool = action.get("tool", "unknown")

    if tool not in KNOWN_TOOLS:
        return Decision("deny", f"Unknown tool is blocked by default: {tool}", "TOOL-001")

    for rule in policy.get("command_rules", []):
        if command and _matches(command, rule.get("patterns", [])):
            return Decision(rule["decision"], rule["reason"], rule["id"])

    if command and tool == "run_command" and _matches(command, [r"(^|[;&|]\s*)(?:cat|tee|printf|echo)\s+[^\n]*>", r"\bsed\s+-[^\n]*i(?:\s|$)", r"\bperl\s+-[^\n]*-i(?:\s|$)", r"\bpython(?:3)?\s+-c\b"]):
        return Decision("deny", "Shell based file mutation is blocked; use a governed file tool.", "SHELL-001")

    if raw_path:
        relative = _safe_relative(root, raw_path)
        if relative is None:
            if tool in policy.get("write_tools", []):
                return Decision("deny", "Path is outside the project or resolves through an unsafe link.", "SCOPE-001")
            return Decision("deny", "Path cannot be resolved safely.", "SCOPE-004")

        if tool in policy.get("write_tools", []):
            if contract.get("task_id") in (None, "", "UNSET"):
                return Decision("deny", "Define an active task contract before writing files.", "TASK-001")
            protected = policy.get("protected_paths", []) + profile.get("protected_areas", [])
            if any(fnmatch.fnmatch(relative, pattern) for pattern in protected):
                return Decision("deny", f"Protected governance path: {relative}", "SELF-001")
            forbidden = contract.get("forbidden_paths", [])
            if any(fnmatch.fnmatch(relative, pattern) for pattern in forbidden):
                return Decision("deny", f"Task contract forbids this path: {relative}", "SCOPE-003")
            allowed = contract.get("allowed_paths", [])
            if not allowed or not any(fnmatch.fnmatch(relative, pattern) for pattern in allowed):
                return Decision("deny", f"Path is outside the active task contract: {relative}", "SCOPE-002")

    return Decision(policy.get("default_decision", "ask"), "No explicit rule matched.", "DEFAULT")


def violation_count(root: Path, rule_id: str) -> int:
    log = root / ".governor" / "violations.jsonl"
    if not log.exists():
        return 0
    count = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            if json.loads(line).get("rule_id") == rule_id:
                count += 1
        except ValueError:
            continue
    return count
