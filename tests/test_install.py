import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent_governor.cli import install_command, uninstall_command
from agent_governor.templates import write_templates


class InstallTests(unittest.TestCase):
    def test_install_preserves_existing_and_uninstall_removes_only_governor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_templates(root)
            hooks = root / ".agents" / "hooks.json"
            hooks.parent.mkdir(parents=True)
            hooks.write_text(json.dumps({"my-hook": {"enabled": True}}), encoding="utf-8")
            self.assertEqual(0, install_command(SimpleNamespace(root=str(root))))
            installed = json.loads(hooks.read_text())
            self.assertIn("my-hook", installed)
            self.assertIn("agent-governor", installed)
            self.assertEqual(0, uninstall_command(SimpleNamespace(root=str(root))))
            self.assertEqual({"my-hook": {"enabled": True}}, json.loads(hooks.read_text()))


if __name__ == "__main__":
    unittest.main()
