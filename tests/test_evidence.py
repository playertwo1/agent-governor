import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_governor.evidence import run_required
from agent_governor.templates import write_templates


class EvidenceTests(unittest.TestCase):
    def test_successful_receipt_is_invalidated_by_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "sample.txt").write_text("one", encoding="utf-8")
            write_templates(root)
            receipt, passed = run_required(root, "T-1", ["python -c pass"])
            self.assertTrue(passed)
            self.assertEqual("PASS", receipt["status"])
            (root / "sample.txt").write_text("two", encoding="utf-8")
            self.assertNotEqual(receipt["fingerprint_after"], __import__("agent_governor.evidence", fromlist=["project_fingerprint"]).project_fingerprint(root))

    def test_missing_command_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            write_templates(root)
            receipt, passed = run_required(root, "T-1", ["command-that-does-not-exist"])
            self.assertFalse(passed)
            self.assertEqual("FAIL", receipt["status"])


if __name__ == "__main__":
    unittest.main()
