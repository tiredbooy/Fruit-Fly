"""Exact compact-network regressions against the pre-optimization update loop."""

from dataclasses import replace
import math
from pathlib import Path
import unittest

from brain.data import SourceManifest, load_release
from brain.network import ConnectomeNetwork, RuntimeCircuit
from brain.neuron import rate_response
from simulation.signals import NeuralSnapshot


def load_official_circuits() -> tuple[RuntimeCircuit, ...]:
    """Load both pinned runtime circuits and validate every selected edge."""
    root = Path(__file__).resolve().parents[2]
    source = SourceManifest.from_json(root / "data/malecns/v1.0/source-manifest.json")
    release = load_release(source, root / "data/raw/malecns/v1.0")
    circuits = []
    for name in ("foraging-v1-runtime.json", "gym-v1-runtime.json"):
        circuit = RuntimeCircuit.from_json(
            root / "data/circuits" / name,
            annotations=release.annotations,
            transmitters=release.transmitters,
            expected_weights_sha256=source.sources["weights"].sha256,
        )
        release.edges.require_edges(tuple(
            (edge.body_pre, edge.body_post, edge.weight) for edge in circuit.edges
        ))
        circuits.append(circuit)
    return tuple(circuits)


class OriginalConnectomeNetwork:
    """Frozen reference of the compact implementation before static caching."""

    def __init__(self, circuit: RuntimeCircuit, leak: float = 0.30) -> None:
        self.circuit = circuit
        self._leak = leak
        self._activity = {node.body_id: 0.0 for node in circuit.nodes}
        self._sign = {
            node.body_id: -1.0 if node.transmitter == "gaba" else 1.0
            for node in circuit.nodes
        }
        self._incoming_scale: dict[int, float] = {}
        for edge in circuit.edges:
            self._incoming_scale[edge.body_post] = (
                self._incoming_scale.get(edge.body_post, 0.0) + math.log1p(edge.weight)
            )

    def step(self, external: dict[int, float], *, substeps: int = 5) -> NeuralSnapshot:
        for _ in range(substeps):
            currents = {body_id: 0.0 for body_id in self._activity}
            for edge in self.circuit.edges:
                normalized_weight = math.log1p(edge.weight) / self._incoming_scale[edge.body_post]
                currents[edge.body_post] += (
                    self._activity[edge.body_pre]
                    * normalized_weight
                    * self._sign[edge.body_pre]
                )
            next_activity = {}
            for body_id, previous in self._activity.items():
                driven = rate_response(currents[body_id])
                next_activity[body_id] = self._leak * previous + (1.0 - self._leak) * driven
            for body_id, value in external.items():
                if body_id in next_activity:
                    next_activity[body_id] = min(1.0, max(0.0, value))
            self._activity = next_activity

        role_activity = {
            role: self._activity.get(body_id, 0.0)
            for role, body_id in self.circuit.motor_roles.items()
        }
        labels = {
            node.body_id: f"{node.type or 'untyped'}#{node.body_id}"
            for node in self.circuit.nodes
        }
        return NeuralSnapshot(dict(self._activity), role_activity, labels)


class OfficialNetworkEquivalenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.circuits = load_official_circuits()

    def test_every_snapshot_matches_original_with_varied_inputs_and_substeps(self) -> None:
        for circuit in self.circuits:
            for leak in (0.0, 0.3, 1.0):
                actual = ConnectomeNetwork(circuit, leak=leak)
                original = OriginalConnectomeNetwork(circuit, leak=leak)
                for step in range(30):
                    levels = (0.0, 0.13, 0.7, 1.0, -0.2, 1.4)
                    external = {
                        node.body_id: levels[(index + step) % len(levels)]
                        for index, node in enumerate(circuit.nodes)
                        if (index + step) % 4 == 0
                    }
                    external[-1] = 0.5
                    substeps = (0, 1, 2, 5, 9, -1)[step % 6]
                    with self.subTest(nodes=len(circuit.nodes), leak=leak, step=step):
                        self.assertEqual(
                            original.step(external, substeps=substeps),
                            actual.step(external, substeps=substeps),
                        )

    def test_external_values_are_clamped_each_substep_and_unknown_ids_ignored(self) -> None:
        for circuit in self.circuits:
            network = ConnectomeNetwork(circuit)
            known = [node.body_id for node in circuit.nodes[:6]]
            values = (-0.3, 1.2, 0.23, -math.inf, math.inf, math.nan)
            external = dict(zip(known, values, strict=True))
            external[-1] = 1.0
            snapshot = network.step(external)
            self.assertEqual(
                [0.0, 1.0, 0.23, 0.0, 1.0, 0.0],
                [snapshot.activity_by_body[body_id] for body_id in known],
            )
            self.assertNotIn(-1, snapshot.activity_by_body)

    def test_snapshot_mutations_do_not_change_network_or_other_instances(self) -> None:
        for circuit in self.circuits:
            network = ConnectomeNetwork(circuit)
            untouched = ConnectomeNetwork(circuit)
            original = OriginalConnectomeNetwork(circuit)
            external = {node.body_id: 0.61 for node in circuit.nodes[:8]}
            original.step(external)
            snapshot = network.step(external)
            snapshot.activity_by_body.clear()
            snapshot.activity_by_role.clear()
            snapshot.labels_by_body.clear()
            external.clear()

            self.assertEqual(original.step({}), network.step({}))
            self.assertEqual(
                OriginalConnectomeNetwork(circuit).step({}, substeps=0),
                untouched.step({}, substeps=0),
            )

    def test_later_updates_leave_previous_snapshot_unchanged(self) -> None:
        for circuit in self.circuits:
            network = ConnectomeNetwork(circuit)
            original = OriginalConnectomeNetwork(circuit)
            snapshot = network.step({})
            expected = original.step({})
            network.step({node.body_id: 1.0 for node in circuit.nodes})
            self.assertEqual(expected, snapshot)

    def test_motor_role_mapping_remains_dynamic(self) -> None:
        for source in self.circuits:
            circuit = replace(source, motor_roles=dict(source.motor_roles))
            network = ConnectomeNetwork(circuit)
            node = circuit.nodes[0]
            circuit.motor_roles["test_observation"] = node.body_id
            snapshot = network.step({node.body_id: 0.41})
            self.assertEqual(0.41, snapshot.activity_by_role["test_observation"])
