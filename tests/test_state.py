import tempfile
import unittest
from pathlib import Path

from agent_governor.state import TaskState


class StateTests(unittest.TestCase):
    def test_persistent_state_and_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            first = TaskState(path)
            first.create("T-1", "test")
            first.transition("T-1", "ACTIVE")
            self.assertEqual("ACTIVE", TaskState(path).inspect("T-1")["status"])

    def test_invalid_transition_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            state = TaskState(Path(directory) / "state.db")
            state.create("T-1", "test")
            with self.assertRaises(ValueError):
                state.transition("T-1", "DONE")

    def test_circuit_breaker_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            state = TaskState(path)
            state.create("T-1", "test")
            state.transition("T-1", "ACTIVE")
            self.assertFalse(state.record_violation("T-1", 2))
            self.assertTrue(state.record_violation("T-1", 2))
            self.assertTrue(TaskState(path).is_blocked("T-1"))


if __name__ == "__main__":
    unittest.main()
