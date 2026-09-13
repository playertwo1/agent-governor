from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


STATUSES = {"DRAFT", "ACTIVE", "PAUSED", "BLOCKED", "READY_FOR_AUDIT", "APPROVED", "DONE"}
TRANSITIONS = {
    "DRAFT": {"ACTIVE", "PAUSED"}, "ACTIVE": {"PAUSED", "BLOCKED", "READY_FOR_AUDIT"},
    "PAUSED": {"ACTIVE"}, "BLOCKED": {"PAUSED"}, "READY_FOR_AUDIT": {"APPROVED", "ACTIVE"},
    "APPROVED": {"DONE"}, "DONE": set(),
}


class TaskState:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, objective TEXT NOT NULL, status TEXT NOT NULL, violations INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA busy_timeout=5000")
        return db

    def create(self, task_id: str, objective: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO tasks(task_id, objective, status, violations, created_at, updated_at) VALUES(?,?,?,?,COALESCE((SELECT created_at FROM tasks WHERE task_id=?),?),?)", (task_id, objective, "DRAFT", 0, task_id, now, now))

    def transition(self, task_id: str, target: str) -> None:
        if target not in STATUSES:
            raise ValueError(f"invalid status: {target}")
        with self._connect() as db:
            row = db.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not row:
                raise ValueError(f"unknown task: {task_id}")
            if target not in TRANSITIONS[row[0]]:
                raise ValueError(f"invalid transition {row[0]} -> {target}")
            db.execute("UPDATE tasks SET status=?, updated_at=? WHERE task_id=?", (target, datetime.now(timezone.utc).isoformat(), task_id))

    def inspect(self, task_id: str) -> dict[str, object]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            raise ValueError(f"unknown task: {task_id}")
        return dict(row)

    def record_violation(self, task_id: str, maximum: int) -> bool:
        with self._connect() as db:
            row = db.execute("SELECT violations, status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not row:
                return False
            violations = row[0] + 1
            status = "BLOCKED" if violations >= maximum else row[1]
            db.execute("UPDATE tasks SET violations=?, status=?, updated_at=? WHERE task_id=?", (violations, status, datetime.now(timezone.utc).isoformat(), task_id))
            return status == "BLOCKED"

    def is_blocked(self, task_id: str) -> bool:
        try:
            return self.inspect(task_id)["status"] == "BLOCKED"
        except ValueError:
            return False
