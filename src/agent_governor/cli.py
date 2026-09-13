from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .adapters import antigravity_output, normalize
from .engine import append_event, evaluate, load_json, violation_count
from .templates import write_templates


def root_path(value: str = ".") -> Path:
    return Path(value).resolve()


def hook(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    try:
        payload = json.load(sys.stdin)
    except ValueError as exc:
        print(json.dumps({"decision": "deny", "reason": f"Invalid hook input: {exc}"}))
        return 2
    action = normalize(payload)
    result = evaluate(root, action)
    if result.decision == "deny":
        append_event(root, {**result.as_dict(), "action": action})
        policy = load_json(root / ".governor" / "policy.json")
        maximum = policy.get("circuit_breaker", {}).get("max_same_rule_violations", 2)
        if violation_count(root, result.rule_id) >= maximum:
            result = type(result)("deny", f"Circuit breaker open after repeated {result.rule_id} violations. Human review required.", "CIRCUIT-001")
    print(json.dumps(antigravity_output(result.decision, f"[{result.rule_id}] {result.reason}"), ensure_ascii=False))
    return 2 if result.decision == "deny" else 0


def verify(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    contract = load_json(root / ".governor" / "task-contract.json")
    command = ["git", "diff", "--name-only", args.base]
    changed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True,
        capture_output=True, check=False
    ).stdout.splitlines()
    changed = sorted(set(changed + untracked))
    issues = []
    allowed = contract.get("allowed_paths", [])
    import fnmatch
    for name in changed:
        if any(fnmatch.fnmatch(name, pattern) for pattern in contract.get("forbidden_paths", [])):
            issues.append(f"forbidden path: {name}")
        if allowed and not any(fnmatch.fnmatch(name, pattern) for pattern in allowed):
            issues.append(f"outside scope: {name}")
    maximum = contract.get("max_files_changed", 10)
    if len(changed) > maximum:
        issues.append(f"changed {len(changed)} files; contract allows {maximum}")
    report = {"verdict": "FAIL" if issues else "PASS", "changed_files": changed, "findings": issues}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if issues else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="governor")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Install a project governance profile")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--profile", default="generic")
    pre = sub.add_parser("hook", help="Evaluate a PreToolUse JSON payload from stdin")
    pre.add_argument("--root", default=".")
    check = sub.add_parser("verify", help="Check the current diff against the task contract")
    check.add_argument("--root", default=".")
    check.add_argument("--base", default="HEAD")
    args = parser.parse_args()
    if args.command == "init":
        write_templates(root_path(args.path), args.profile)
        print(f"Governor initialized in {root_path(args.path)}")
        return
    raise SystemExit(hook(args) if args.command == "hook" else verify(args))


if __name__ == "__main__":
    main()
