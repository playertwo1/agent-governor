import json
import tempfile
import unittest
from pathlib import Path

from agent_governor.adapters import normalize
from agent_governor.engine import evaluate
from agent_governor.templates import write_templates


class GovernorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        write_templates(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_blocks_force_push(self):
        result = evaluate(self.root, {"tool": "run_command", "command": "git push --force origin main", "path": ""})
        self.assertEqual("deny", result.decision)
        self.assertEqual("GIT-001", result.rule_id)

    def test_asks_for_dependency(self):
        result = evaluate(self.root, {"tool": "run_command", "command": "npm install react", "path": ""})
        self.assertEqual("force_ask", result.decision)

    def test_fails_closed_without_policy(self):
        (self.root / ".governor" / "policy.json").unlink()
        result = evaluate(self.root, {"tool": "run_command", "command": "git status", "path": ""})
        self.assertEqual("deny", result.decision)

    def test_blocks_governor_self_edit(self):
        contract_path = self.root / ".governor" / "task-contract.json"
        contract = json.loads(contract_path.read_text())
        contract["task_id"] = "TEST-1"
        contract_path.write_text(json.dumps(contract))
        result = evaluate(self.root, {"tool": "write_to_file", "path": str(self.root / ".governor/policy.json"), "command": ""})
        self.assertEqual("deny", result.decision)
        self.assertEqual("SELF-001", result.rule_id)

    def test_contract_limits_write_paths(self):
        contract_path = self.root / ".governor" / "task-contract.json"
        contract = json.loads(contract_path.read_text())
        contract["task_id"] = "TEST-2"
        contract["allowed_paths"] = ["src/**"]
        contract_path.write_text(json.dumps(contract))
        denied = evaluate(self.root, {"tool": "write_to_file", "path": str(self.root / "docs/x.md"), "command": ""})
        allowed = evaluate(self.root, {"tool": "write_to_file", "path": str(self.root / "src/x.py"), "command": ""})
        self.assertEqual("deny", denied.decision)
        self.assertEqual("allow", allowed.decision)

    def test_requires_active_contract_for_writes(self):
        result = evaluate(self.root, {"tool": "write_to_file", "path": str(self.root / "src/x.py"), "command": ""})
        self.assertEqual("deny", result.decision)
        self.assertEqual("TASK-001", result.rule_id)

    def test_antigravity_payload(self):
        action = normalize({"toolCall": {"name": "run_command", "args": {"CommandLine": "python -m unittest"}}})
        self.assertEqual("run_command", action["tool"])
        self.assertEqual("python -m unittest", action["command"])


if __name__ == "__main__":
    unittest.main()
