import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTest(unittest.TestCase):
    def test_required_documentation_and_make_targets_exist(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("MaleCNS provenance", agents)
        self.assertIn("Documentation maintenance", agents)
        self.assertIn("make run", readme)
        for target in ("run:", "run-fresh:", "test:", "data-status:", "help:"):
            self.assertIn(target, makefile)

    def test_architecture_science_status_and_decision_are_documented(self) -> None:
        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
        science = (ROOT / "docs/science/learning-memory.md").read_text(encoding="utf-8")
        status = (ROOT / "docs/status.md").read_text(encoding="utf-8")
        decision = (ROOT / "docs/decisions/0001-learning-memory.md").read_text(encoding="utf-8")

        self.assertIn("world must not import brain", architecture)
        self.assertIn("KC-to-MBON01", science)
        self.assertIn("pam01-kc-mbon01-v1", science)
        self.assertIn("Known limitations", status)
        self.assertIn("Decision", decision)


if __name__ == "__main__":
    unittest.main()
