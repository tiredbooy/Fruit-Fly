"""Provenance-checked roles for a MaleCNS circuit."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from brain.data import MaleCNSAnnotations, NeuronAnnotation


class CircuitValidationError(ValueError):
    """Raised when a circuit role is unsupported by its pinned annotations."""


@dataclass(frozen=True, slots=True)
class CircuitRole:
    role: str
    body_id: int
    type: str
    side: str
    evidence: str

    def with_type(self, neuron_type: str) -> "CircuitRole":
        return replace(self, type=neuron_type)


@dataclass(slots=True)
class CircuitManifest:
    dataset: str
    roles: list[CircuitRole]
    assumptions: dict[str, object]
    sensory_selectors: dict[str, dict[str, object]]

    @classmethod
    def from_json(cls, path: Path) -> "CircuitManifest":
        document = json.loads(path.read_text(encoding="utf-8"))
        roles = [CircuitRole(**role) for role in document["roles"]]
        return cls(
            dataset=str(document["dataset"]),
            roles=roles,
            assumptions=dict(document.get("assumptions", {})),
            sensory_selectors=dict(document.get("sensory_selectors", {})),
        )

    @property
    def minimum_connection_weight(self) -> int:
        value = self.assumptions.get("minimum_connection_weight")
        if not isinstance(value, int) or value < 1:
            raise CircuitValidationError("minimum_connection_weight must be a positive integer")
        return value

    def validate(self, annotations: MaleCNSAnnotations) -> None:
        if annotations.dataset != self.dataset:
            raise CircuitValidationError("Circuit and annotation datasets do not match")
        if len({role.role for role in self.roles}) != len(self.roles):
            raise CircuitValidationError("Circuit role names must be unique")

        for role in self.roles:
            annotation = annotations.require_body(role.body_id)
            if annotation.type != role.type or annotation.side != role.side:
                raise CircuitValidationError(
                    f"Role {role.role} does not match body {role.body_id} annotations"
                )
            if not role.evidence.startswith("https://"):
                raise CircuitValidationError(f"Role {role.role} requires an evidence URL")

        self.minimum_connection_weight

    def resolve_sensory(
        self,
        name: str,
        annotations: MaleCNSAnnotations,
    ) -> tuple[NeuronAnnotation, ...]:
        if annotations.dataset != self.dataset:
            raise CircuitValidationError("Circuit and annotation datasets do not match")
        try:
            selector = self.sensory_selectors[name]
        except KeyError as error:
            raise CircuitValidationError(f"Unknown sensory selector: {name}") from error

        configured_types = selector.get("types")
        if configured_types is None:
            configured_types = [selector.get("type")]
        neuron_types = frozenset(item for item in configured_types if isinstance(item, str))
        if not neuron_types:
            raise CircuitValidationError(f"Sensory selector {name} has no official types")

        matches = annotations.bodies_of_types(neuron_types)
        if selector.get("retinotopy_fields"):
            matches = tuple(
                item
                for item in matches
                if item.optic_hex_1 is not None and item.optic_hex_2 is not None
            )
        if selector.get("side_from_instance_suffix"):
            matches = tuple(item for item in matches if item.effective_side in {"L", "R"})
        if not matches:
            raise CircuitValidationError(f"Sensory selector {name} resolved no neurons")
        return matches
