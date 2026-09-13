from __future__ import annotations

import json
from pathlib import Path


POLICY = {
    "schema_version": 1,
    "default_decision": "allow",
    "write_tools": ["write_to_file", "replace_file_content", "multi_replace_file_content", "Write", "Edit", "MultiEdit"],
    "protected_paths": [".governor/**", ".agents/hooks/**", ".github/workflows/governor.yml"],
    "command_rules": [
        {"id": "CMD-001", "decision": "deny", "reason": "Destructive filesystem command blocked.", "patterns": [r"(^|[;&|]\s*)rm\s+-[^\n]*r[^\n]*f", r"\bmkfs\b", r"\bdd\s+if="]},
        {"id": "GIT-001", "decision": "deny", "reason": "Destructive Git history operation blocked.", "patterns": [r"git\s+push\b.*(--force|-f)\b", r"git\s+reset\s+--hard", r"git\s+clean\s+-[^\n]*f"]},
        {"id": "BYPASS-001", "decision": "deny", "reason": "Verification bypass blocked.", "patterns": [r"--no-verify", r"\bskip[_-]?tests?\b"]},
        {"id": "DEP-001", "decision": "force_ask", "reason": "Dependency changes require human approval.", "patterns": [r"\b(npm|pnpm|yarn)\s+(add|install)\b", r"\bpip\s+install\b", r"\bgradle\b.*depend"]},
        {"id": "PUSH-001", "decision": "force_ask", "reason": "Publishing changes requires human approval.", "patterns": [r"git\s+push\b"]}
    ],
    "circuit_breaker": {"max_same_rule_violations": 2}
}

CONTRACT = {
    "schema_version": 1,
    "task_id": "UNSET",
    "objective": "Define the current task before allowing writes.",
    "allowed_paths": [],
    "forbidden_paths": [".governor/**"],
    "max_files_changed": 10,
    "required_commands": [],
    "required_evidence": [],
    "architecture_changes": False,
    "dependency_changes": False
}

PROFILE = {"schema_version": 1, "name": "generic", "stack": [], "test_commands": [], "protected_areas": []}


def write_templates(root: Path, profile: str = "generic") -> None:
    directory = root / ".governor"
    directory.mkdir(parents=True, exist_ok=True)
    values = {"policy.json": POLICY, "task-contract.json": CONTRACT, "project-profile.json": {**PROFILE, "name": profile}}
    for name, value in values.items():
        target = directory / name
        if not target.exists():
            target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (directory / "violations.jsonl").touch(exist_ok=True)
