"""Sparse rate simulation over a provenance-pinned MaleCNS subgraph."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

from brain.data import MaleCNSAnnotations, NeuronTransmitters
from brain.neuron import rate_response
from simulation.signals import NeuralSnapshot


@dataclass(frozen=True, slots=True)
class RuntimeNode:
    body_id: int
    type: str | None
    side: str | None
    transmitter: str


@dataclass(frozen=True, slots=True)
class RuntimeEdge:
    body_pre: int
    body_post: int
    weight: int


@dataclass(frozen=True, slots=True)
class RuntimeCircuit:
    dataset: str
    nodes: tuple[RuntimeNode, ...]
    edges: tuple[RuntimeEdge, ...]
    sensory_inputs: dict[str, tuple[int, ...]]
    motor_roles: dict[str, int]

    @classmethod
    def from_json(
        cls,
        path: Path,
        *,
        annotations: MaleCNSAnnotations,
        transmitters: NeuronTransmitters,
        expected_weights_sha256: str,
    ) -> "RuntimeCircuit":
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["dataset"] != annotations.dataset:
            raise ValueError("Runtime circuit and MaleCNS annotations do not match")
        if document["source_weights_sha256"] != expected_weights_sha256:
            raise ValueError("Runtime circuit was extracted from a different weights file")

        edge_records = tuple(RuntimeEdge(**item) for item in document["edges"])
        body_ids = {
            body_id
            for edge in edge_records
            for body_id in (edge.body_pre, edge.body_post)
        }
        nodes = []
        for body_id in sorted(body_ids):
            annotation = annotations.require_body(body_id)
            nodes.append(
                RuntimeNode(
                    body_id=body_id,
                    type=annotation.type,
                    side=annotation.effective_side,
                    transmitter=transmitters.require_known(body_id),
                )
            )
        return cls(
            dataset=str(document["dataset"]),
            nodes=tuple(nodes),
            edges=edge_records,
            sensory_inputs={
                name: tuple(int(body_id) for body_id in values)
                for name, values in document["sensory_inputs"].items()
            },
            motor_roles={name: int(body_id) for name, body_id in document["motor_roles"].items()},
        )


class ConnectomeNetwork:
    """A leaky synchronous network; connectivity and signs come from MaleCNS."""

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
            self._incoming_scale[edge.body_post] = self._incoming_scale.get(edge.body_post, 0.0) + math.log1p(edge.weight)

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
