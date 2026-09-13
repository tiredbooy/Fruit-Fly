import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from brain.learning import (
    LearningCircuit,
    LearningConfig,
    LearningEdge,
    MushroomBodyLearning,
)
from brain.memory import MemoryState
from brain.data import ConnectomeEdges, MaleCNSAnnotations, NeuronTransmitters


class MushroomBodyLearningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.circuit = LearningCircuit(
            dataset="male-cns:v1.0",
            source_weights_sha256="abc123",
            projection_neurons={"L": 10, "R": 20},
            mbon01_neurons={"L": 100, "R": 200},
            pam01_neurons=(300, 301),
            pn_kc_edges=(
                LearningEdge(10, 11, 40),
                LearningEdge(10, 12, 20),
                LearningEdge(20, 21, 30),
                LearningEdge(20, 22, 10),
            ),
            plastic_edges=(
                LearningEdge(11, 100, 25),
                LearningEdge(12, 100, 25),
                LearningEdge(21, 200, 25),
                LearningEdge(22, 200, 25),
            ),
        )
        memory = MemoryState.fresh(
            dataset=self.circuit.dataset,
            weights_sha256=self.circuit.source_weights_sha256,
            model="pam01-kc-mbon01-v1",
            plastic_edges=tuple(
                (edge.body_pre, edge.body_post, edge.weight)
                for edge in self.circuit.plastic_edges
            ),
        )
        config = LearningConfig(
            eligibility_decay=0.5,
            learning_rate=0.5,
            minimum_multiplier=0.35,
            salience_gain=1.0,
            active_kc_fraction=0.5,
        )
        self.learner = MushroomBodyLearning(self.circuit, memory, config)

    def test_recall_uses_sparse_kenyon_cell_activity(self) -> None:
        recall = self.learner.recall(smell_left=1.0, smell_right=0.0)

        self.assertEqual(1, recall.active_kcs)
        self.assertGreater(recall.kc_activity[11], 0.0)
        self.assertEqual(0.0, recall.kc_activity[12])
        self.assertEqual(1.0, recall.learned_salience)

    def test_zero_reward_does_not_change_memory(self) -> None:
        self.learner.recall(smell_left=1.0, smell_right=0.0)

        event = self.learner.reinforce(0.0)

        self.assertFalse(event.changed)
        self.assertEqual(0, event.memory.reward_events)

    def test_reward_changes_only_eligible_synapses(self) -> None:
        self.learner.recall(smell_left=1.0, smell_right=0.0)

        event = self.learner.reinforce(1.0)
        multipliers = {item.key: item.multiplier for item in event.memory.synapses}

        self.assertTrue(event.changed)
        self.assertLess(multipliers[(11, 100)], 1.0)
        self.assertEqual(1.0, multipliers[(12, 100)])
        self.assertEqual(1.0, multipliers[(21, 200)])
        self.assertGreater(event.association_strength, 0.0)

    def test_eligibility_decays_without_odor(self) -> None:
        first = self.learner.recall(smell_left=1.0, smell_right=0.0)
        second = self.learner.recall(smell_left=0.0, smell_right=0.0)

        self.assertGreater(first.mean_eligibility, second.mean_eligibility)
        self.assertGreater(second.mean_eligibility, 0.0)

    def test_repeated_reward_never_crosses_minimum_multiplier(self) -> None:
        for _ in range(200):
            self.learner.recall(smell_left=1.0, smell_right=1.0)
            event = self.learner.reinforce(1.0)

        self.assertGreaterEqual(
            min(item.multiplier for item in event.memory.synapses),
            0.35,
        )


class LearningCircuitManifestTest(unittest.TestCase):
    def test_loads_only_officially_annotated_learning_roles_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for body_id, neuron_type, instance, neuron_class, transmitter in (
                (1, "ORN_DM1", "ORN_DM1_L", "sensory", "acetylcholine"),
                (2, "ORN_DM1", "ORN_DM1_R", "sensory", "acetylcholine"),
                (10, "DM1_lPN", "DM1_lPN_L", "projection", "acetylcholine"),
                (20, "DM1_lPN", "DM1_lPN_R", "projection", "acetylcholine"),
                (11, "KCg-m", "KCg-m_L", "Kenyon_Cell", "acetylcholine"),
                (21, "KCg-m", "KCg-m_R", "Kenyon_Cell", "acetylcholine"),
                (100, "MBON01", "MBON01_L", "MBON", "glutamate"),
                (200, "MBON01", "MBON01_R", "MBON", "glutamate"),
                (300, "PAM01", "PAM01_L", "DAN", "dopamine"),
                (301, "PAM01", "PAM01_R", "DAN", "dopamine"),
            ):
                rows.append(
                    {
                        "bodyId": body_id,
                        "type": neuron_type,
                        "instance": instance,
                        "somaSide": None,
                        "statusLabel": "Reviewed",
                        "assignedOlHex1": None,
                        "assignedOlHex2": None,
                        "class": neuron_class,
                        "transmitter": transmitter,
                    }
                )
            annotation_path = root / "annotations.feather"
            pd.DataFrame(rows).drop(columns="transmitter").to_feather(annotation_path)
            transmitter_path = root / "transmitters.feather"
            pd.DataFrame(
                {"body": [row["bodyId"] for row in rows], "consensus_nt": [row["transmitter"] for row in rows]}
            ).to_feather(transmitter_path)
            edge_rows = [
                {"body_pre": 1, "body_post": 10, "weight": 12},
                {"body_pre": 2, "body_post": 20, "weight": 13},
                {"body_pre": 10, "body_post": 11, "weight": 14},
                {"body_pre": 20, "body_post": 21, "weight": 15},
                {"body_pre": 11, "body_post": 100, "weight": 16},
                {"body_pre": 21, "body_post": 200, "weight": 17},
            ]
            edge_path = root / "weights.feather"
            pd.DataFrame(edge_rows).to_feather(edge_path)
            manifest_path = root / "learning.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "dataset": "male-cns:v1.0",
                        "source_weights_sha256": "abc123",
                        "model": "pam01-kc-mbon01-v1",
                        "selection": {"kenyon_cells_per_side": 1},
                        "projection_neurons": {"L": 10, "R": 20},
                        "mbon01_neurons": {"L": 100, "R": 200},
                        "pam01_neurons": [300, 301],
                        "orn_pn_edges": edge_rows[:2],
                        "pn_kc_edges": edge_rows[2:4],
                        "plastic_edges": edge_rows[4:],
                    }
                ),
                encoding="utf-8",
            )

            circuit = LearningCircuit.from_json(
                manifest_path,
                annotations=MaleCNSAnnotations.from_feather(annotation_path, dataset="male-cns:v1.0"),
                transmitters=NeuronTransmitters.from_feather(transmitter_path),
                edges=ConnectomeEdges.from_feather(edge_path),
                expected_weights_sha256="abc123",
            )

            self.assertEqual((300, 301), circuit.pam01_neurons)
            self.assertEqual(2, len(circuit.plastic_edges))


if __name__ == "__main__":
    unittest.main()
