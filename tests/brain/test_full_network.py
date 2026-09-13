import unittest
from dataclasses import replace

import numpy as np

from brain.data import DataIntegrityError
from brain.full_graph import FullGraph, FullGraphMetadata
from brain.full_network import FullConnectomeNetwork
from brain.network import ConnectomeNetwork, RuntimeCircuit, RuntimeEdge, RuntimeNode


class FullConnectomeNetworkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.circuit = RuntimeCircuit(
            dataset="male-cns:v1.0",
            nodes=(
                RuntimeNode(10, "sensory", "L", "acetylcholine"),
                RuntimeNode(20, "interneuron", "L", "acetylcholine"),
                RuntimeNode(30, "descending", "L", "acetylcholine"),
            ),
            edges=(RuntimeEdge(10, 20, 4), RuntimeEdge(20, 30, 9)),
            sensory_inputs={
                "smell_left": (10,),
                "smell_right": (),
                "vision_left": (),
                "vision_right": (),
            },
            motor_roles={"forward_left": 30},
        )
        self.graph = FullGraph(
            metadata=FullGraphMetadata(
                schema_version=1,
                dataset="male-cns:v1.0",
                neuron_count=4,
                connected_neuron_count=3,
                edge_count=2,
                source_sha256={},
                filter_name="test",
                polarity_policy="test",
                dynamics="incoming-log1p-rate-v1",
                transmitter_counts={"acetylcholine": 3, "missing": 1},
            ),
            body_ids=np.array([10, 20, 30, 40], dtype=np.int64),
            indptr=np.array([0, 0, 1, 2, 2], dtype=np.int64),
            indices=np.array([0, 1], dtype=np.int32),
            weights=np.array([1.0, 1.0], dtype=np.float32),
            signs=np.array([1.0, 1.0, 1.0, 0.0], dtype=np.float32),
        )

    def test_matches_compact_dynamics_for_the_same_circuit(self) -> None:
        compact = ConnectomeNetwork(self.circuit)
        full = FullConnectomeNetwork(self.graph, self.circuit)

        compact_snapshot = compact.step({10: 0.8}, substeps=4)
        full_snapshot = full.step({10: 0.8}, substeps=4)

        for body_id in (10, 20, 30):
            self.assertAlmostEqual(
                compact_snapshot.activity_by_body[body_id],
                full_snapshot.activity_by_body[body_id],
                places=6,
            )
        self.assertAlmostEqual(
            compact_snapshot.activity_by_role["forward_left"],
            full_snapshot.activity_by_role["forward_left"],
            places=6,
        )

    def test_snapshot_keeps_interface_neurons_and_limits_extra_telemetry(self) -> None:
        full = FullConnectomeNetwork(self.graph, self.circuit, telemetry_limit=1)

        snapshot = full.step({10: 1.0}, substeps=3)

        self.assertEqual({10, 20, 30}, set(snapshot.activity_by_body))
        self.assertEqual("sensory#10", snapshot.labels_by_body[10])
        self.assertEqual("descending#30", snapshot.labels_by_body[30])

    def test_rejects_an_interface_body_missing_from_the_full_graph(self) -> None:
        invalid = RuntimeCircuit(
            dataset=self.circuit.dataset,
            nodes=self.circuit.nodes,
            edges=self.circuit.edges,
            sensory_inputs={**self.circuit.sensory_inputs, "smell_right": (999,)},
            motor_roles=self.circuit.motor_roles,
        )

        with self.assertRaisesRegex(DataIntegrityError, "999"):
            FullConnectomeNetwork(self.graph, invalid)

    def test_rejects_external_activity_for_an_unknown_body(self) -> None:
        full = FullConnectomeNetwork(self.graph, self.circuit)

        with self.assertRaisesRegex(DataIntegrityError, "999"):
            full.step({999: 1.0})

    def test_total_telemetry_budget_retains_all_interfaces_and_strongest_extras(self) -> None:
        graph, circuit = self._large_observation_fixture()
        full = FullConnectomeNetwork(graph, circuit)
        snapshot = full.step({body_id: body_id / 200 for body_id in range(75, 200)}, substeps=1)

        self.assertEqual(128, len(snapshot.activity_by_body))
        self.assertEqual(set(range(75)) | set(range(147, 200)), set(snapshot.activity_by_body))
        self.assertTrue(all(snapshot.activity_by_body[body_id] == 0 for body_id in range(75)))

    def test_equal_activity_extras_prefer_lowest_body_ids(self) -> None:
        graph, circuit = self._large_observation_fixture()
        full = FullConnectomeNetwork(graph, circuit)
        snapshot = full.step({body_id: .5 for body_id in range(75, 200)}, substeps=1)

        self.assertEqual(set(range(128)), set(snapshot.activity_by_body))

    def test_configured_extra_limit_and_zero_preserve_the_interface(self) -> None:
        graph, circuit = self._large_observation_fixture()
        for limit, extras in ((0, set()), (2, {198, 199}), (1000, set(range(147, 200)))):
            with self.subTest(limit=limit):
                full = FullConnectomeNetwork(graph, circuit, telemetry_limit=limit)
                snapshot = full.step({body_id: body_id / 200 for body_id in range(75, 200)}, substeps=1)
                self.assertEqual(set(range(75)) | extras, set(snapshot.activity_by_body))

    def test_interface_exceeding_wire_budget_is_explicitly_rejected(self) -> None:
        graph, circuit = self._large_observation_fixture()
        circuit = replace(circuit, sensory_inputs={'smell_left': tuple(range(129))})

        with self.assertRaisesRegex(DataIntegrityError, '128'):
            FullConnectomeNetwork(graph, circuit)

    def _large_observation_fixture(self) -> tuple[FullGraph, RuntimeCircuit]:
        graph = replace(self.graph,
            metadata=replace(self.graph.metadata, neuron_count=200, connected_neuron_count=0, edge_count=0),
            body_ids=np.arange(200, dtype=np.int64), indptr=np.zeros(201, dtype=np.int64),
            indices=np.empty(0, dtype=np.int32), weights=np.empty(0, dtype=np.float32),
            signs=np.ones(200, dtype=np.float32))
        circuit = replace(self.circuit,
            nodes=tuple(RuntimeNode(body_id, 'fixture', None, 'acetylcholine') for body_id in range(70)),
            edges=(), sensory_inputs={'smell_left': (70, 71)},
            motor_roles={'forward_left': 72, 'forward_right': 73, 'steering_low_left': 74})
        return graph, circuit


if __name__ == "__main__":
    unittest.main()
