from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def project_fingerprint(root: Path) -> str:
    """Hash paths and bytes visible to Git, including untracked files."""
    listing = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=root,
        capture_output=True, check=False,
    )
    if listing.returncode != 0:
        raise RuntimeError("cannot fingerprint project: git ls-files failed")
    digest = hashlib.sha256()
    paths = sorted(p for p in listing.stdout.split(b"\0") if p)
    for raw in paths:
        relative = raw.decode("utf-8", errors="surrogateescape")
        if relative == ".governor" or relative.startswith(".governor/"):
            continue
        target = root / relative
        if not target.is_file():
            continue
        digest.update(raw)
        digest.update(b"\0")
        with target.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest()


def run_required(root: Path, task_id: str, commands: list[str], timeout: int = 900) -> tuple[dict, bool]:
    if not commands:
        return {"task_id": task_id, "status": "FAIL", "reason": "No required commands are declared."}, False
    before = project_fingerprint(root)
    policy_hash = hashlib.sha256((root / ".governor" / "policy.json").read_bytes()).hexdigest()
    contract_hash = hashlib.sha256((root / ".governor" / "task-contract.json").read_bytes()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    base_commit = commit.stdout.strip() if commit.returncode == 0 else "NO_COMMIT"
    results = []
    all_passed = True
    for command in commands:
        started = time.monotonic()
        try:
            completed = subprocess.run(shlex.split(command, posix=(os.name != "nt")), cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
            result = {"command": command, "returncode": completed.returncode, "duration_seconds": round(time.monotonic() - started, 3), "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest()}
            if completed.returncode != 0:
                all_passed = False
        except (OSError, ValueError) as exc:
            result = {"command": command, "error": type(exc).__name__, "duration_seconds": round(time.monotonic() - started, 3)}
            all_passed = False
        except subprocess.TimeoutExpired:
            result = {"command": command, "error": "TimeoutExpired", "duration_seconds": round(time.monotonic() - started, 3)}
            all_passed = False
        results.append(result)
        if not all_passed:
            break
    after = project_fingerprint(root)
    receipt = {"schema_version": 1, "task_id": task_id, "created_at": datetime.now(timezone.utc).isoformat(), "status": "PASS" if all_passed else "FAIL", "base_commit": base_commit, "policy_sha256": policy_hash, "contract_sha256": contract_hash, "fingerprint_before": before, "fingerprint_after": after, "commands": results}
    evidence_dir = root / ".governor" / "evidence" / task_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = evidence_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt["path"] = str(receipt_path.relative_to(root)).replace("\\", "/")
    return receipt, all_passed and before == after
