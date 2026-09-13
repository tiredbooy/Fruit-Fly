import hashlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from brain.data import (
    ConnectomeEdges,
    DataIntegrityError,
    MaleCNSAnnotations,
    NeuronTransmitters,
    SourceManifest,
    file_sha256,
)


class MaleCNSDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "annotations.feather"
        pd.DataFrame(
            [
                {
                    "bodyId": 10783,
                    "type": "DNp09",
                    "instance": "DNp09_L",
                    "somaSide": "L",
                    "statusLabel": "Roughly traced",
                    "assignedOlHex1": None,
                    "assignedOlHex2": None,
                    "class": "descending_neuron",
                },
                {
                    "bodyId": 11177,
                    "type": "DNp09",
                    "instance": "DNp09_R",
                    "somaSide": "R",
                    "statusLabel": "Roughly traced",
                    "assignedOlHex1": None,
                    "assignedOlHex2": None,
                    "class": "descending_neuron",
                },
            ]
        ).to_feather(self.path)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_reads_official_annotation_fields_without_changing_ids(self) -> None:
        annotations = MaleCNSAnnotations.from_feather(self.path, dataset="male-cns:v1.0")

        left = annotations.require_body(10783)

        self.assertEqual("DNp09", left.type)
        self.assertEqual("DNp09_L", left.instance)
        self.assertEqual("L", left.side)
        self.assertEqual("descending_neuron", left.neuron_class)
        self.assertEqual("male-cns:v1.0", left.dataset)

    def test_rejects_a_checksum_that_does_not_match_the_source(self) -> None:
        with self.assertRaises(DataIntegrityError):
            MaleCNSAnnotations.from_feather(
                self.path,
                dataset="male-cns:v1.0",
                expected_sha256="0" * 64,
            )

    def test_computes_sha256_from_file_bytes(self) -> None:
        expected = hashlib.sha256(self.path.read_bytes()).hexdigest()

        self.assertEqual(expected, file_sha256(self.path))

    def test_loads_edge_rows_without_changing_official_body_ids(self) -> None:
        edge_path = Path(self.directory.name) / "weights.feather"
        pd.DataFrame(
            [{"body_pre": 60498, "body_post": 10360, "weight": 12}]
        ).to_feather(edge_path)

        edges = ConnectomeEdges.from_feather(edge_path)

        self.assertEqual(1, edges.count)
        self.assertEqual((60498, 10360, 12), edges.row(0))
        edges.require_edges(((60498, 10360, 12),))

        with self.assertRaises(DataIntegrityError):
            edges.require_edges(((60498, 10360, 99),))

    def test_source_manifest_resolves_canonical_raw_filenames(self) -> None:
        manifest_path = Path(self.directory.name) / "source-manifest.json"
        manifest_path.write_text(
            '{"dataset":"male-cns:v1.0","sources":{'
            '"annotations":{"url":"https://example.test/body.feather","sha256":"aa"},'
            '"weights":{"url":"https://example.test/weights.feather","sha256":"bb"}}}',
            encoding="utf-8",
        )

        manifest = SourceManifest.from_json(manifest_path)

        self.assertEqual("body.feather", manifest.sources["annotations"].filename)
        self.assertEqual("weights.feather", manifest.sources["weights"].filename)

    def test_reads_official_consensus_neurotransmitter(self) -> None:
        transmitter_path = Path(self.directory.name) / "transmitters.feather"
        pd.DataFrame(
            [
                {"body": 60498, "consensus_nt": "acetylcholine"},
                {"body": 10005, "consensus_nt": "gaba"},
                {"body": 42, "consensus_nt": "unclear"},
            ]
        ).to_feather(transmitter_path)

        transmitters = NeuronTransmitters.from_feather(transmitter_path)

        self.assertEqual("acetylcholine", transmitters.require_known(60498))
        self.assertEqual("gaba", transmitters.require_known(10005))
        self.assertEqual("acetylcholine", transmitters.require_call(60498, "acetylcholine"))
        with self.assertRaises(DataIntegrityError):
            transmitters.require_known(42)
        with self.assertRaises(DataIntegrityError):
            transmitters.require_call(60498, "dopamine")


if __name__ == "__main__":
    unittest.main()
