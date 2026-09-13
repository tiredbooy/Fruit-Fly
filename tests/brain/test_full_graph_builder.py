import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
import pyarrow.feather as feather
from scipy.sparse import csr_matrix

from brain.data import DataIntegrityError, SourceAsset, SourceManifest, file_sha256
from brain.full_graph import FullGraphRepository
from brain.full_graph_builder import ExpectedGraphCounts, FullGraphBuilder


class FullGraphBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        annotations = pd.DataFrame(
            {
                "bodyId": [1, 2, 3, 4, 5, 6, 7, 8],
                "superclass": ["sensory", "central", "tbc-neuron", None, "central", "central", "central", "central"],
            }
        )
        weights = pd.DataFrame(
            {
                "body_pre": [1, 5, 3, 1],
                "body_post": [2, 2, 2, 4],
                "weight": [3, 7, 100, 100],
            }
        )
        transmitters = pd.DataFrame(
            {
                "body": [1, 2, 5, 6, 7],
                "consensus_nt": ["acetylcholine", "gaba", "glutamate", "histamine", "dopamine"],
            }
        )
        feather.write_feather(annotations, self.raw / "annotations.feather")
        feather.write_feather(weights, self.raw / "weights.feather")
        feather.write_feather(transmitters, self.raw / "nt.feather")
        self.source = SourceManifest(
            dataset="male-cns:v1.0",
            sources={
                "annotations": self._asset("annotations.feather"),
                "weights": self._asset("weights.feather"),
                "neurotransmitters": self._asset("nt.feather"),
            },
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_builds_filtered_signed_normalized_graph_and_keeps_isolated_neurons(self) -> None:
        output = self.root / "full-graph"
        builder = FullGraphBuilder(
            self.source,
            self.raw,
            ExpectedGraphCounts(neurons=6, connected_neurons=3, edges=2),
        )

        metadata = builder.build(output)
        graph = FullGraphRepository(output).load(self.source)

        self.assertEqual(6, metadata.neuron_count)
        self.assertEqual(3, metadata.connected_neuron_count)
        self.assertEqual(2, metadata.edge_count)
        np.testing.assert_array_equal([1, 2, 5, 6, 7, 8], graph.body_ids)
        np.testing.assert_array_equal([1, -1, -1, -1, 0, 0], graph.signs)
        matrix = csr_matrix(
            (graph.weights, graph.indices, graph.indptr),
            shape=(6, 6),
        ).toarray()
        denominator = math.log1p(3.0) + math.log1p(7.0)
        self.assertAlmostEqual(math.log1p(3.0) / denominator, matrix[1, 0], places=6)
        self.assertAlmostEqual(-math.log1p(7.0) / denominator, matrix[1, 2], places=6)
        self.assertEqual(0.0, matrix[1, 3])

    def test_wrong_expected_counts_do_not_publish_an_artifact(self) -> None:
        output = self.root / "full-graph"
        builder = FullGraphBuilder(
            self.source,
            self.raw,
            ExpectedGraphCounts(neurons=7, connected_neurons=3, edges=2),
        )

        with self.assertRaisesRegex(DataIntegrityError, "neuron count"):
            builder.build(output)

        self.assertFalse(output.exists())

    def _asset(self, name: str) -> SourceAsset:
        return SourceAsset(
            url=f"https://example/{name}",
            sha256=file_sha256(self.raw / name),
        )


if __name__ == "__main__":
    unittest.main()
