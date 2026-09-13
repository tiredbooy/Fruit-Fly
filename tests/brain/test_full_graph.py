import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from brain.data import DataIntegrityError, SourceAsset, SourceManifest
from brain.full_graph import FullGraphRepository


class FullGraphRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name)
        self.source = SourceManifest(
            dataset="male-cns:v1.0",
            sources={
                "annotations": SourceAsset("https://example/annotations.feather", "a" * 64),
                "weights": SourceAsset("https://example/weights.feather", "b" * 64),
                "neurotransmitters": SourceAsset("https://example/nt.feather", "c" * 64),
            },
        )
        self._write_valid_artifact()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_loads_valid_arrays_as_memory_maps(self) -> None:
        graph = FullGraphRepository(self.path).load(self.source)

        self.assertEqual(3, graph.metadata.neuron_count)
        self.assertEqual(2, graph.metadata.connected_neuron_count)
        self.assertEqual(2, graph.metadata.edge_count)
        self.assertIsInstance(graph.body_ids, np.memmap)
        self.assertIsInstance(graph.weights, np.memmap)
        np.testing.assert_array_equal(np.array([10, 20, 30]), graph.body_ids)

    def test_rejects_an_artifact_from_different_source_weights(self) -> None:
        metadata = json.loads((self.path / "metadata.json").read_text())
        metadata["source_sha256"]["weights"] = "d" * 64
        (self.path / "metadata.json").write_text(json.dumps(metadata))

        with self.assertRaisesRegex(DataIntegrityError, "source checksum"):
            FullGraphRepository(self.path).load(self.source)

    def test_rejects_unsorted_body_ids(self) -> None:
        np.save(self.path / "body_ids.npy", np.array([20, 10, 30], dtype=np.int64))

        with self.assertRaisesRegex(DataIntegrityError, "strictly increasing"):
            FullGraphRepository(self.path).load(self.source)

    def test_rejects_invalid_csr_boundaries(self) -> None:
        np.save(self.path / "indptr.npy", np.array([0, 2, 1, 2], dtype=np.int64))

        with self.assertRaisesRegex(DataIntegrityError, "CSR"):
            FullGraphRepository(self.path).load(self.source)

    def test_rejects_non_finite_weights(self) -> None:
        np.save(self.path / "weights.npy", np.array([0.5, np.nan], dtype=np.float32))

        with self.assertRaisesRegex(DataIntegrityError, "finite"):
            FullGraphRepository(self.path).load(self.source)

    def test_rejects_an_unsupported_dynamics_contract(self) -> None:
        metadata = json.loads((self.path / "metadata.json").read_text())
        metadata["dynamics"] = "unknown-dynamics"
        (self.path / "metadata.json").write_text(json.dumps(metadata))

        with self.assertRaisesRegex(DataIntegrityError, "dynamics"):
            FullGraphRepository(self.path).load(self.source)

    def _write_valid_artifact(self) -> None:
        metadata = {
            "schema_version": 1,
            "dataset": "male-cns:v1.0",
            "neuron_count": 3,
            "connected_neuron_count": 2,
            "edge_count": 2,
            "source_sha256": {
                "annotations": "a" * 64,
                "weights": "b" * 64,
                "neurotransmitters": "c" * 64,
            },
            "filter_name": "valid-superclass-v1",
            "polarity_policy": "ach-positive-gaba-glu-his-negative-modulators-zero-v1",
            "dynamics": "incoming-log1p-rate-v1",
            "transmitter_counts": {"acetylcholine": 1, "gaba": 1, "missing": 1},
        }
        (self.path / "metadata.json").write_text(json.dumps(metadata))
        np.save(self.path / "body_ids.npy", np.array([10, 20, 30], dtype=np.int64))
        np.save(self.path / "indptr.npy", np.array([0, 1, 2, 2], dtype=np.int64))
        np.save(self.path / "indices.npy", np.array([0, 1], dtype=np.int32))
        np.save(self.path / "weights.npy", np.array([0.5, -0.25], dtype=np.float32))
        np.save(self.path / "signs.npy", np.array([1.0, -1.0, 0.0], dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
