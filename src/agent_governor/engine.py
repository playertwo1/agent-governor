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


def evaluate(root: Path, action: dict[str, str]) -> Decision:
    policy_path = root / ".governor" / "policy.json"
    contract_path = root / ".governor" / "task-contract.json"
    if not policy_path.exists() or not contract_path.exists():
        return Decision("deny", "Governor configuration is missing; refusing to fail open.", "CFG-001")

    try:
        policy = load_json(policy_path)
        contract = load_json(contract_path)
        validate_documents(policy, contract)
    except (OSError, ValueError, TypeError) as exc:
        return Decision("deny", f"Governor configuration is invalid: {exc}", "CFG-002")

    command = action.get("command", "")
    path = action.get("path", "").replace("\\", "/")
    tool = action.get("tool", "unknown")

    for rule in policy.get("command_rules", []):
        if command and _matches(command, rule.get("patterns", [])):
            return Decision(rule["decision"], rule["reason"], rule["id"])

    if path:
        relative = path
        try:
            relative = str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
        except ValueError:
            if tool in policy.get("write_tools", []):
                return Decision("deny", "Writes outside the project are forbidden.", "SCOPE-001")

        if tool in policy.get("write_tools", []):
            if contract.get("task_id") in (None, "", "UNSET"):
                return Decision("deny", "Define an active task contract before writing files.", "TASK-001")
            protected = policy.get("protected_paths", [])
            if any(fnmatch.fnmatch(relative, pattern) for pattern in protected):
                return Decision("deny", f"Protected governance path: {relative}", "SELF-001")
            forbidden = contract.get("forbidden_paths", [])
            if any(fnmatch.fnmatch(relative, pattern) for pattern in forbidden):
                return Decision("deny", f"Task contract forbids this path: {relative}", "SCOPE-003")
            allowed = contract.get("allowed_paths", [])
            if allowed and not any(fnmatch.fnmatch(relative, pattern) for pattern in allowed):
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
