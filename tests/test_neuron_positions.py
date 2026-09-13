"""The exporter must preserve measured anatomy and omit missing positions."""
import unittest
from scripts.export_neuron_positions import measured_positions


class NeuronPositionTests(unittest.TestCase):
    def test_measured_ids_and_uniform_normalization(self):
        rows = [
            {"bodyId": 10001, "superclass": "descending", "somaLocation": [10, 20, 30]},
            {"bodyId": 10002, "superclass": "ascending", "somaLocation": [30, 30, 40]},
            {"bodyId": 10003, "superclass": "tbc", "somaLocation": [0, 0, 0]},
            {"bodyId": 10004, "superclass": "central", "somaLocation": None},
            {"bodyId": 10005, "superclass": "central", "somaLocation": [float("nan"), 0, 0]},
        ]
        points, eligible = measured_positions(rows)
        self.assertEqual(eligible, 4)
        self.assertEqual(points, [[10001, -1.0, -0.5, -0.5], [10002, 1.0, 0.5, 0.5]])

    def test_no_measurements_stays_empty(self):
        self.assertEqual(measured_positions([]), ([], 0))
