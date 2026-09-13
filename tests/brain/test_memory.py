import json
import math
import tempfile
import unittest
from pathlib import Path

from brain.memory import MemoryRepository, MemoryState, MemoryValidationError


class MemoryStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.template = MemoryState.fresh(
            dataset="male-cns:v1.0",
            weights_sha256="abc123",
            model="pam01-kc-mbon01-v1",
            plastic_edges=((101, 201, 20), (102, 201, 30)),
        )

    def test_fresh_memory_has_unmodified_synapses(self) -> None:
        self.assertEqual((1.0, 1.0), tuple(item.multiplier for item in self.template.synapses))
        self.assertEqual(0.0, self.template.association_strength)
        self.assertEqual(0, self.template.reward_events)

    def test_update_changes_only_named_synapse_and_records_reward(self) -> None:
        changed = self.template.with_updates({(101, 201): 0.8}, reward=0.5)

        self.assertEqual((0.8, 1.0), tuple(item.multiplier for item in changed.synapses))
        self.assertAlmostEqual(0.1, changed.association_strength)
        self.assertEqual(1, changed.reward_events)
        self.assertAlmostEqual(0.5, changed.total_reward)

    def test_rejects_invalid_multiplier(self) -> None:
        for invalid in (-0.1, 1.1, math.nan):
            with self.subTest(invalid=invalid):
                with self.assertRaises(MemoryValidationError):
                    self.template.with_updates({(101, 201): invalid}, reward=0.0)


class MemoryRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "memory.json"
        self.repository = MemoryRepository(self.path)
        self.template = MemoryState.fresh(
            dataset="male-cns:v1.0",
            weights_sha256="abc123",
            model="pam01-kc-mbon01-v1",
            plastic_edges=((101, 201, 20),),
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_save_and_load_round_trip_is_atomic(self) -> None:
        expected = self.template.with_updates({(101, 201): 0.75}, reward=0.4)

        self.repository.save(expected)
        loaded = self.repository.load_or_create(self.template)

        self.assertEqual(expected, loaded)
        self.assertEqual([], list(self.path.parent.glob("*.tmp")))

    def test_missing_file_returns_clean_template(self) -> None:
        self.assertEqual(self.template, self.repository.load_or_create(self.template))

    def test_rejects_memory_from_another_dataset(self) -> None:
        self.repository.save(self.template)
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["dataset"] = "another-dataset"
        self.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(MemoryValidationError, "dataset"):
            self.repository.load_or_create(self.template)

    def test_rejects_changed_baseline_edge(self) -> None:
        self.repository.save(self.template)
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["synapses"][0]["baseline_weight"] = 99
        self.path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(MemoryValidationError, "synapse set"):
            self.repository.load_or_create(self.template)

    def test_reset_moves_existing_memory_to_backup(self) -> None:
        self.repository.save(self.template)

        backup = self.repository.reset_with_backup()

        self.assertFalse(self.path.exists())
        self.assertIsNotNone(backup)
        self.assertTrue(backup.is_file())


if __name__ == "__main__":
    unittest.main()
