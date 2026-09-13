import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from brain.circuit import CircuitManifest, CircuitValidationError
from brain.data import MaleCNSAnnotations


class CircuitManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        annotations_path = root / "annotations.feather"
        pd.DataFrame(
            [
                {"bodyId": 10783, "type": "DNp09", "instance": "DNp09_L", "somaSide": "L", "statusLabel": "Roughly traced", "assignedOlHex1": None, "assignedOlHex2": None},
                {"bodyId": 11177, "type": "DNp09", "instance": "DNp09_R", "somaSide": "R", "statusLabel": "Roughly traced", "assignedOlHex1": None, "assignedOlHex2": None},
                {"bodyId": 60498, "type": "ORN_DM1", "instance": "ORN_DM1_R", "somaSide": None, "statusLabel": "Roughly traced", "assignedOlHex1": None, "assignedOlHex2": None},
                {"bodyId": 10350, "type": "L2", "instance": "L2_L", "somaSide": None, "statusLabel": "Reviewed", "assignedOlHex1": 12, "assignedOlHex2": 8},
            ]
        ).to_feather(annotations_path)
        self.annotations = MaleCNSAnnotations.from_feather(annotations_path, dataset="male-cns:v1.0")
        self.manifest_path = root / "circuit.json"
        self.manifest_path.write_text(
            json.dumps(
                {
                    "dataset": "male-cns:v1.0",
                    "roles": [
                        {"role": "forward_left", "body_id": 10783, "type": "DNp09", "side": "L", "evidence": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9435592/"},
                        {"role": "forward_right", "body_id": 11177, "type": "DNp09", "side": "R", "evidence": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9435592/"},
                    ],
                    "assumptions": {"minimum_connection_weight": 10},
                    "sensory_selectors": {
                        "food_odor": {"type": "ORN_DM1", "side_from_instance_suffix": True, "evidence": "https://example.test/odor"},
                        "grayscale_vision": {"types": ["L1", "L2"], "retinotopy_fields": ["assignedOlHex1", "assignedOlHex2"]},
                    },
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_validates_roles_against_annotation_type_and_side(self) -> None:
        manifest = CircuitManifest.from_json(self.manifest_path)

        manifest.validate(self.annotations)

        self.assertEqual(10, manifest.minimum_connection_weight)

    def test_rejects_a_role_with_an_invented_type(self) -> None:
        manifest = CircuitManifest.from_json(self.manifest_path)
        manifest.roles[0] = manifest.roles[0].with_type("InventedWalkingNeuron")

        with self.assertRaises(CircuitValidationError):
            manifest.validate(self.annotations)

    def test_resolves_sensory_populations_from_official_annotations(self) -> None:
        manifest = CircuitManifest.from_json(self.manifest_path)

        smell = manifest.resolve_sensory("food_odor", self.annotations)
        vision = manifest.resolve_sensory("grayscale_vision", self.annotations)

        self.assertEqual([(60498, "R")], [(item.body_id, item.effective_side) for item in smell])
        self.assertEqual([(10350, 12.0, 8.0)], [(item.body_id, item.optic_hex_1, item.optic_hex_2) for item in vision])


if __name__ == "__main__":
    unittest.main()
