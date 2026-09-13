"""CPU sparse-rate simulation over the full official MaleCNS graph."""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix

from brain.data import DataIntegrityError
from brain.full_graph import FullGraph
from brain.network import RuntimeCircuit
from simulation.signals import NeuralSnapshot


MAX_VISIBLE_NEURONS = 128


class FullConnectomeNetwork:
    """Full sparse dynamics with at most 128 interface-first telemetry records."""

    def __init__(
        self,
        graph: FullGraph,
        circuit: RuntimeCircuit,
        leak: float = 0.30,
        telemetry_limit: int = 64,
    ) -> None:
        if graph.metadata.dataset != circuit.dataset:
            raise DataIntegrityError("Full graph and runtime circuit datasets do not match")
        if not 0.0 <= leak <= 1.0:
            raise ValueError("leak must be within 0..1")
        if telemetry_limit < 0:
            raise ValueError("telemetry_limit must not be negative")

        self.circuit = circuit
        self._body_ids = graph.body_ids
        self._matrix = csr_matrix(
            (graph.weights, graph.indices, graph.indptr),
            shape=(graph.metadata.neuron_count, graph.metadata.neuron_count),
            copy=False,
        )
        self._activity = np.zeros(graph.metadata.neuron_count, dtype=np.float32)
        self._leak = np.float32(leak)
        self._labels = {
            node.body_id: f"{node.type or 'untyped'}#{node.body_id}"
            for node in circuit.nodes
        }

        interface_ids = {
            node.body_id for node in circuit.nodes
        } | {
            body_id
            for body_ids in circuit.sensory_inputs.values()
            for body_id in body_ids
        } | set(circuit.motor_roles.values())
        if len(interface_ids) > MAX_VISIBLE_NEURONS:
            raise DataIntegrityError(
                f"Runtime interface exceeds the {MAX_VISIBLE_NEURONS}-neuron telemetry capacity"
            )
        self._telemetry_limit = min(telemetry_limit, MAX_VISIBLE_NEURONS - len(interface_ids))
        self._interface_indices = self._indices_for(interface_ids)
        self._motor_indices = {
            role: int(self._indices_for((body_id,))[0])
            for role, body_id in circuit.motor_roles.items()
        }

    def step(
        self,
        external: dict[int, float],
        *,
        substeps: int = 5,
    ) -> NeuralSnapshot:
        external_ids = tuple(external)
        external_indices = self._indices_for(external_ids)
        external_values = np.clip(
            np.fromiter((external[body_id] for body_id in external_ids), dtype=np.float32),
            0.0,
            1.0,
        )

        for _ in range(substeps):
            current = self._matrix @ self._activity
            driven = np.tanh(np.maximum(current, np.float32(0.0)))
            self._activity = self._leak * self._activity + (1.0 - self._leak) * driven
            self._activity[external_indices] = external_values

        activity_by_role = {
            role: float(self._activity[index])
            for role, index in self._motor_indices.items()
        }
        visible_indices = self._visible_indices()
        activity_by_body = {
            int(self._body_ids[index]): float(self._activity[index])
            for index in visible_indices
        }
        labels_by_body = {
            body_id: self._labels.get(body_id, f"body#{body_id}")
            for body_id in activity_by_body
        }
        return NeuralSnapshot(activity_by_body, activity_by_role, labels_by_body)

    def _indices_for(self, body_ids: object) -> np.ndarray:
        requested = np.fromiter(body_ids, dtype=np.int64)
        if requested.size == 0:
            return np.empty(0, dtype=np.int64)
        indices = np.searchsorted(self._body_ids, requested)
        in_bounds = indices < len(self._body_ids)
        matched = np.zeros(len(requested), dtype=np.bool_)
        matched[in_bounds] = self._body_ids[indices[in_bounds]] == requested[in_bounds]
        if not np.all(matched):
            missing = int(requested[np.flatnonzero(~matched)[0]])
            raise DataIntegrityError(f"Body {missing} is missing from the full MaleCNS graph")
        return indices.astype(np.int64, copy=False)

    def _visible_indices(self) -> np.ndarray:
        active = np.flatnonzero(self._activity > 0.0)
        active = active[~np.isin(active, self._interface_indices)]
        if self._telemetry_limit and len(active) > self._telemetry_limit:
            rates = self._activity[active]
            cutoff = np.partition(rates, -self._telemetry_limit)[-self._telemetry_limit]
            strongest = active[rates > cutoff]
            # Graph indices follow ascending official IDs; equal rates prefer smaller IDs.
            ties = active[rates == cutoff][:self._telemetry_limit - len(strongest)]
            active = np.concatenate((strongest, ties))
        elif self._telemetry_limit == 0:
            active = np.empty(0, dtype=np.int64)
        return np.unique(np.concatenate((self._interface_indices, active)))
