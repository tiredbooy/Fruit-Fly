from dataclasses import replace
from pathlib import Path
import unittest

from brain.gym_circuit import build_gym_documents, load_gym_circuits
from brain.data import SourceManifest, load_release

ROOT = Path(__file__).resolve().parents[2]


class OfficialGymCircuitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SourceManifest.from_json(ROOT / 'data/malecns/v1.0/source-manifest.json')
        cls.release = load_release(cls.source, ROOT / 'data/raw/malecns/v1.0')

    def test_reproducible_dm2_edges_and_disjoint_learning_are_official(self):
        runtime, food, gym = load_gym_circuits(ROOT, release=self.release)
        self.assertEqual({'L': 11092, 'R': 12171}, gym.projection_neurons)
        self.assertEqual(48, len(gym.plastic_edges))
        self.assertFalse({e.body_pre for e in food.plastic_edges} & {e.body_pre for e in gym.plastic_edges})
        self.assertIn('gym_left', runtime.sensory_inputs)
        self.assertIn('smell_left', runtime.sensory_inputs)
        self.assertEqual('pam01-kc-mbon01-v1', food.model)
        import json
        generated_runtime, generated_learning = build_gym_documents(ROOT)
        self.assertEqual(json.loads((ROOT / 'data/circuits/gym-v1-runtime.json').read_text()), generated_runtime)
        self.assertEqual(json.loads((ROOT / 'data/circuits/gym-v1-learning.json').read_text()), generated_learning)

    def test_dm1_default_rejects_dm2_annotations(self):
        _, _, gym = load_gym_circuits(ROOT, release=self.release)
        with self.assertRaises(ValueError):
            replace(gym, projection_type='DM1_lPN')._validate(
                self.release.annotations, self.release.transmitters, 24)
