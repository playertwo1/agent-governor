from __future__ import annotations

import json
from pathlib import Path


POLICY = {
    "schema_version": 1,
    "default_decision": "allow",
    "write_tools": ["write_to_file", "replace_file_content", "multi_replace_file_content", "Write", "Edit", "MultiEdit"],
    "protected_paths": [".governor/**", ".agents/hooks/**", ".agents/hooks.json", ".github/workflows/governor.yml"],
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

PROFILES = {
    "generic": {"stack": [], "test_commands": [], "protected_areas": []},
    "python": {"stack": ["python"], "test_commands": ["python -m unittest discover -s tests -v"], "protected_areas": [".venv/**", "**/.env*", "**/secrets/**"]},
    "node": {"stack": ["node"], "test_commands": ["npm test"], "protected_areas": ["node_modules/**", "**/.env*", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"]},
    "android-kotlin": {"stack": ["android", "kotlin", "gradle"], "test_commands": ["./gradlew test", "./gradlew lint"], "protected_areas": ["**/keystore.properties", "**/*.jks", "**/*.keystore", "**/.env*"]},
    "n8n-telegram": {"stack": ["n8n", "telegram"], "test_commands": [], "protected_areas": ["**/.env*", "**/*token*", "**/*secret*"]},
}


def write_templates(root: Path, profile: str = "generic") -> None:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    directory = root / ".governor"
    directory.mkdir(parents=True, exist_ok=True)
    profile_data = {**PROFILE, **PROFILES[profile], "name": profile}
    values = {"policy.json": POLICY, "task-contract.json": CONTRACT, "project-profile.json": profile_data}
    for name, value in values.items():
        target = directory / name
        if not target.exists():
            target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    runtime_ignore = directory / ".gitignore"
    if not runtime_ignore.exists():
        runtime_ignore.write_text("state.db\nviolations.jsonl\nevidence/\n", encoding="utf-8")
    (directory / "violations.jsonl").touch(exist_ok=True)
