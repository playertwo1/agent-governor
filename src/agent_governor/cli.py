from __future__ import annotations

import argparse
import json
import subprocess
import sys
import fnmatch
import shutil
import hashlib
from pathlib import Path

from .adapters import antigravity_output, normalize
from .engine import append_event, evaluate, load_json, violation_count
from .templates import write_templates
from .state import TaskState
from .evidence import run_required


def root_path(value: str = ".") -> Path:
    return Path(value).resolve()


def hook(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError) as exc:
        print(json.dumps({"decision": "deny", "reason": f"Invalid hook input: {exc}"}))
        return 2
    try:
        action = normalize(payload)
        contract = load_json(root / ".governor" / "task-contract.json")
        task_id = contract.get("task_id", "")
        state = TaskState(root / ".governor" / "state.db")
        if task_id not in ("", "UNSET") and state.is_blocked(task_id):
            result = type("SafeDecision", (), {"decision": "deny", "rule_id": "CIRCUIT-002", "reason": "Active task is blocked; administrative review is required."})()
        elif task_id not in ("", "UNSET") and action.get("tool") in {"write_to_file", "replace_file_content", "multi_replace_file_content", "Write", "Edit", "MultiEdit", "run_command"}:
            try:
                task_status = state.inspect(task_id)["status"]
            except ValueError:
                task_status = "MISSING"
            if task_status != "ACTIVE":
                result = type("SafeDecision", (), {"decision": "deny", "rule_id": "TASK-002", "reason": "Task must be ACTIVE before mutations are allowed."})()
            else:
                result = evaluate(root, action)
        else:
            result = evaluate(root, action)
        if result.decision == "deny":
            append_event(root, {**result.as_dict(), "action": {"tool": action.get("tool"), "has_command": bool(action.get("command")), "has_path": bool(action.get("path"))}})
            policy = load_json(root / ".governor" / "policy.json")
            maximum = policy.get("circuit_breaker", {}).get("max_same_rule_violations", 2)
            if violation_count(root, result.rule_id) >= maximum:
                result = type(result)("deny", f"Circuit breaker open after repeated {result.rule_id} violations. Human review required.", "CIRCUIT-001")
            if task_id not in ("", "UNSET") and result.rule_id not in {"CIRCUIT-002", "CIRCUIT-001"}:
                if state.record_violation(task_id, maximum):
                    result = type(result)("deny", "Circuit breaker open after repeated task violations. Human review required.", "CIRCUIT-002")
    except Exception:
        result = type("SafeDecision", (), {"decision": "deny", "rule_id": "INTERNAL-001", "reason": "Governor failed safely; human review required."})()
    print(json.dumps(antigravity_output(result.decision, f"[{result.rule_id}] {result.reason}"), ensure_ascii=False))
    return 2 if result.decision == "deny" else 0


def verify(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    try:
        contract = load_json(root / ".governor" / "task-contract.json")
        diff = subprocess.run(["git", "diff", "--name-only", "-z", args.base, "--"], cwd=root, capture_output=True, check=False)
        if diff.returncode != 0:
            print(json.dumps({"verdict": "FAIL", "findings": ["git diff failed; base reference may be invalid"]}, ensure_ascii=False, indent=2))
            return 1
        untracked_result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root, capture_output=True, check=False)
        if untracked_result.returncode != 0:
            print(json.dumps({"verdict": "FAIL", "findings": ["git ls-files failed"]}, ensure_ascii=False, indent=2))
            return 1
        changed = [x for x in diff.stdout.decode(errors="surrogateescape").split("\0") if x]
        untracked = [x for x in untracked_result.stdout.decode(errors="surrogateescape").split("\0") if x]
    except OSError as exc:
        print(json.dumps({"verdict": "FAIL", "findings": [f"git unavailable: {exc}"]}, ensure_ascii=False, indent=2))
        return 1
    changed = sorted(set(changed + untracked))
    issues = []
    allowed = contract.get("allowed_paths", [])
    for name in changed:
        if any(fnmatch.fnmatch(name, pattern) for pattern in contract.get("forbidden_paths", [])):
            issues.append(f"forbidden path: {name}")
        if not allowed or not any(fnmatch.fnmatch(name, pattern) for pattern in allowed):
            issues.append(f"outside scope: {name}")
    maximum = contract.get("max_files_changed", 10)
    if len(changed) > maximum:
        issues.append(f"changed {len(changed)} files; contract allows {maximum}")
    report = {"verdict": "FAIL" if issues else "PASS", "changed_files": changed, "findings": issues}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if issues else 0


def task_command(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    try:
        state = TaskState(root / ".governor" / "state.db")
        if args.task_action == "create":
            contract_path = root / ".governor" / "task-contract.json"
            contract = load_json(contract_path)
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
            contract.update({"task_id": args.task_id, "objective": args.objective, "allowed_paths": args.allowed_paths, "forbidden_paths": args.forbidden_paths, "required_commands": args.required_commands, "max_files_changed": args.max_files, "base_commit": commit.stdout.strip() if commit.returncode == 0 else "NO_COMMIT", "policy_sha256": hashlib.sha256((root / ".governor" / "policy.json").read_bytes()).hexdigest()})
            contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            state.create(args.task_id, args.objective)
            print(json.dumps({"task_id": args.task_id, "status": "DRAFT"}, ensure_ascii=False))
            return 0
        if args.task_action == "activate":
            state.transition(args.task_id, "ACTIVE")
            print(json.dumps({"task_id": args.task_id, "status": "ACTIVE"}, ensure_ascii=False))
            return 0
        print(json.dumps(state.inspect(args.task_id), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


def validate_command(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    try:
        contract = load_json(root / ".governor" / "task-contract.json")
        task_id = contract.get("task_id", "")
        if task_id in ("", "UNSET"):
            print(json.dumps({"status": "FAIL", "reason": "No active task contract."}, ensure_ascii=False))
            return 1
        receipt, passed = run_required(root, task_id, contract.get("required_commands", []), args.timeout)
        if passed:
            try:
                TaskState(root / ".governor" / "state.db").transition(task_id, "READY_FOR_AUDIT")
            except ValueError:
                pass
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "reason": "Validation failed safely.", "error_type": type(exc).__name__}, ensure_ascii=False))
        return 1


def doctor_command(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    checks = {}
    checks["policy"] = (root / ".governor" / "policy.json").is_file()
    checks["contract"] = (root / ".governor" / "task-contract.json").is_file()
    checks["profile"] = (root / ".governor" / "project-profile.json").is_file()
    checks["antigravity_hook"] = (root / ".agents" / "hooks.json").is_file()
    try:
        if checks["policy"] and checks["contract"]:
            from .engine import validate_documents
            validate_documents(load_json(root / ".governor" / "policy.json"), load_json(root / ".governor" / "task-contract.json"))
            checks["schema"] = True
        else:
            checks["schema"] = False
    except Exception:
        checks["schema"] = False
    report = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "root": str(root)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


def install_command(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    target = root / ".agents" / "hooks.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    backup_path = None
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise ValueError("hooks.json must be an object")
        except (OSError, ValueError) as exc:
            print(json.dumps({"status": "FAIL", "reason": "Existing hooks.json is invalid.", "error_type": type(exc).__name__}))
            return 1
        backup_path = target.with_suffix(".json.bak")
        shutil.copy2(target, backup_path)
    existing["agent-governor"] = {"enabled": True, "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "governor hook --root .", "timeout": 10}]}]}
    target.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "path": str(target), "backup": str(backup_path) if backup_path else None}, ensure_ascii=False))
    return 0


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
    task = sub.add_parser("task", help="Create and manage a persistent task contract")
    task.add_argument("task_action", choices=["create", "inspect", "activate"])
    task.add_argument("task_id")
    task.add_argument("--objective", default="")
    task.add_argument("--allowed-path", dest="allowed_paths", action="append", default=[])
    task.add_argument("--forbidden-path", dest="forbidden_paths", action="append", default=[".governor/**"])
    task.add_argument("--required-command", dest="required_commands", action="append", default=[])
    task.add_argument("--max-files", type=int, default=10)
    task.add_argument("--root", default=".")
    validate = sub.add_parser("validate", help="Run required commands and create a fingerprinted receipt")
    validate.add_argument("--root", default=".")
    validate.add_argument("--timeout", type=int, default=900)
    doctor = sub.add_parser("doctor", help="Inspect project configuration and hook installation")
    doctor.add_argument("--root", default=".")
    install = sub.add_parser("install", help="Install an integration without overwriting existing hooks")
    install.add_argument("integration", choices=["antigravity"])
    install.add_argument("--root", default=".")
    args = parser.parse_args()
    if args.command == "init":
        write_templates(root_path(args.path), args.profile)
        print(f"Governor initialized in {root_path(args.path)}")
        return
    if args.command == "hook":
        raise SystemExit(hook(args))
    if args.command == "verify":
        raise SystemExit(verify(args))
    if args.command == "validate":
        raise SystemExit(validate_command(args))
    if args.command == "doctor":
        raise SystemExit(doctor_command(args))
    if args.command == "install":
        raise SystemExit(install_command(args))
    raise SystemExit(task_command(args))


if __name__ == "__main__":
    main()
