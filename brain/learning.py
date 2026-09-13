"""PAM-gated appetitive plasticity over official mushroom-body edges."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

from brain.data import ConnectomeEdges, DataIntegrityError, MaleCNSAnnotations, NeuronTransmitters
from brain.memory import MemoryState


@dataclass(frozen=True, slots=True)
class LearningEdge:
    body_pre: int
    body_post: int
    weight: int

    def __post_init__(self) -> None:
        if self.weight < 1:
            raise ValueError("learning edge weight must be positive")


@dataclass(frozen=True, slots=True)
class LearningCircuit:
    dataset: str
    source_weights_sha256: str
    projection_neurons: dict[str, int]
    mbon01_neurons: dict[str, int]
    pam01_neurons: tuple[int, ...]
    pn_kc_edges: tuple[LearningEdge, ...]
    plastic_edges: tuple[LearningEdge, ...]
    orn_pn_edges: tuple[LearningEdge, ...] = ()
    model: str = "pam01-kc-mbon01-v1"
    projection_type: str = "DM1_lPN"
    odor_type: str = "ORN_DM1"

    @classmethod
    def from_json(
        cls,
        path: Path,
        *,
        annotations: MaleCNSAnnotations,
        transmitters: NeuronTransmitters,
        edges: ConnectomeEdges | None,
        expected_weights_sha256: str,
    ) -> "LearningCircuit":
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["dataset"] != annotations.dataset:
            raise DataIntegrityError("Learning circuit and annotations do not match")
        if document["source_weights_sha256"] != expected_weights_sha256:
            raise DataIntegrityError("Learning circuit weights checksum does not match")
        circuit = cls(
            dataset=str(document["dataset"]),
            source_weights_sha256=str(document["source_weights_sha256"]),
            projection_neurons=_side_mapping(document["projection_neurons"]),
            mbon01_neurons=_side_mapping(document["mbon01_neurons"]),
            pam01_neurons=tuple(int(value) for value in document["pam01_neurons"]),
            orn_pn_edges=_read_edges(document["orn_pn_edges"]),
            pn_kc_edges=_read_edges(document["pn_kc_edges"]),
            plastic_edges=_read_edges(document["plastic_edges"]),
            model=str(document["model"]),
            projection_type=str(document.get("projection_type", "DM1_lPN")),
            odor_type=str(document.get("odor_type", "ORN_DM1")),
        )
        expected_count = int(document["selection"]["kenyon_cells_per_side"])
        circuit._validate(annotations, transmitters, expected_count)
        if edges is not None:
            all_edges = circuit.orn_pn_edges + circuit.pn_kc_edges + circuit.plastic_edges
            edges.require_edges(
                tuple((edge.body_pre, edge.body_post, edge.weight) for edge in all_edges)
            )
        return circuit

    def _validate(
        self,
        annotations: MaleCNSAnnotations,
        transmitters: NeuronTransmitters,
        expected_count: int,
    ) -> None:
        if set(self.projection_neurons) != {"L", "R"}:
            raise DataIntegrityError("Learning circuit requires bilateral projection neurons")
        if set(self.mbon01_neurons) != {"L", "R"}:
            raise DataIntegrityError("Learning circuit requires bilateral MBON01 neurons")
        for side, body_id in self.projection_neurons.items():
            _require_annotation(annotations, body_id, self.projection_type, side=side)
            transmitters.require_call(body_id, "acetylcholine")
        for side, body_id in self.mbon01_neurons.items():
            _require_annotation(annotations, body_id, "MBON01", neuron_class="MBON", side=side)
            transmitters.require_call(body_id, "glutamate")
        for body_id in self.pam01_neurons:
            _require_annotation(annotations, body_id, "PAM01", neuron_class="DAN")
            transmitters.require_call(body_id, "dopamine")
        kc_ids = {edge.body_post for edge in self.pn_kc_edges}
        for body_id in kc_ids:
            annotation = annotations.require_body(body_id)
            if annotation.neuron_class != "Kenyon_Cell":
                raise DataIntegrityError(f"Learning body {body_id} is not an official Kenyon cell")
            transmitters.require_call(body_id, "acetylcholine")
        self._validate_edge_structure(kc_ids, expected_count, annotations)

    def _validate_edge_structure(
        self,
        kc_ids: set[int],
        expected_count: int,
        annotations: MaleCNSAnnotations,
    ) -> None:
        projection_ids = set(self.projection_neurons.values())
        mbon_ids = set(self.mbon01_neurons.values())
        if any(edge.body_post not in projection_ids for edge in self.orn_pn_edges):
            raise DataIntegrityError("ORN edge does not terminate at a selected projection neuron")
        for edge in self.orn_pn_edges:
            _require_annotation(annotations, edge.body_pre, self.odor_type)
        if any(edge.body_pre not in projection_ids for edge in self.pn_kc_edges):
            raise DataIntegrityError("Kenyon edge does not originate at a selected projection neuron")
        if any(edge.body_pre not in kc_ids or edge.body_post not in mbon_ids for edge in self.plastic_edges):
            raise DataIntegrityError("Plastic edge is not a selected KC-to-MBON01 connection")
        plastic_kcs = {edge.body_pre for edge in self.plastic_edges}
        if plastic_kcs != kc_ids:
            raise DataIntegrityError("Every selected Kenyon cell must have one plastic edge")
        for side, projection_id in self.projection_neurons.items():
            count = sum(edge.body_pre == projection_id for edge in self.pn_kc_edges)
            if count != expected_count:
                raise DataIntegrityError(
                    f"Learning circuit has {count} {side} Kenyon cells, expected {expected_count}"
                )


@dataclass(frozen=True, slots=True)
class LearningConfig:
    eligibility_decay: float = 0.92
    learning_rate: float = 0.08
    minimum_multiplier: float = 0.35
    salience_gain: float = 1.0
    active_kc_fraction: float = 0.10

    def __post_init__(self) -> None:
        for name in ("eligibility_decay", "learning_rate", "active_kc_fraction"):
            value = getattr(self, name)
            if not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not 0.0 <= self.minimum_multiplier < 1.0:
            raise ValueError("minimum_multiplier must be within 0..1")
        if self.salience_gain < 0.0:
            raise ValueError("salience_gain cannot be negative")


@dataclass(frozen=True, slots=True)
class RecallState:
    kc_activity: dict[int, float]
    mbon_response: dict[str, float]
    active_kcs: int
    mean_eligibility: float
    learned_salience: float


@dataclass(frozen=True, slots=True)
class LearningState:
    memory: MemoryState
    reward: float
    association_strength: float
    mean_eligibility: float
    active_kcs: int
    changed: bool
    pam_activity: float


class MushroomBodyLearning:
    """Stateful eligibility traces with immutable persistent memory snapshots."""

    def __init__(
        self,
        circuit: LearningCircuit,
        memory: MemoryState,
        config: LearningConfig | None = None,
    ) -> None:
        expected = {
            (edge.body_pre, edge.body_post, edge.weight)
            for edge in circuit.plastic_edges
        }
        actual = {
            (item.body_pre, item.body_post, item.baseline_weight)
            for item in memory.synapses
        }
        if expected != actual:
            raise ValueError("learning circuit and memory synapses do not match")
        self.circuit = circuit
        self.memory = memory
        self.config = config or LearningConfig()
        self._eligibility = {edge.body_pre: 0.0 for edge in circuit.plastic_edges}
        self._active_kcs = 0

    @property
    def learned_salience(self) -> float:
        return 1.0 + self.config.salience_gain * self.memory.association_strength

    def recall(self, *, smell_left: float, smell_right: float) -> RecallState:
        smells = {"L": _clamp01(smell_left), "R": _clamp01(smell_right)}
        activity: dict[int, float] = {}
        for side, projection_id in self.circuit.projection_neurons.items():
            edges = tuple(
                edge for edge in self.circuit.pn_kc_edges if edge.body_pre == projection_id
            )
            activity.update(self._sparse_activity(edges, smells[side]))
        for body_id in self._eligibility:
            previous = self._eligibility[body_id]
            current = activity.get(body_id, 0.0)
            decay = self.config.eligibility_decay
            self._eligibility[body_id] = decay * previous + (1.0 - decay) * current
        self._active_kcs = sum(value > 0.0 for value in activity.values())
        return RecallState(
            kc_activity=activity,
            mbon_response=self._mbon_response(activity),
            active_kcs=self._active_kcs,
            mean_eligibility=self._mean_eligibility(),
            learned_salience=self.learned_salience,
        )

    def reinforce(self, reward: float) -> LearningState:
        bounded_reward = _clamp01(reward)
        if bounded_reward == 0.0:
            return self._learning_state(0.0, changed=False)
        old = {item.key: item.multiplier for item in self.memory.synapses}
        updates = {}
        for edge in self.circuit.plastic_edges:
            key = edge.body_pre, edge.body_post
            eligibility = self._eligibility[edge.body_pre]
            depression = (
                self.config.learning_rate
                * bounded_reward
                * eligibility
                * (old[key] - self.config.minimum_multiplier)
            )
            updates[key] = max(self.config.minimum_multiplier, old[key] - depression)
        self.memory = self.memory.with_updates(updates, reward=bounded_reward)
        changed = any(updates[key] < old[key] for key in updates)
        return self._learning_state(bounded_reward, changed=changed)

    def _sparse_activity(
        self,
        edges: tuple[LearningEdge, ...],
        smell: float,
    ) -> dict[int, float]:
        if smell == 0.0 or not edges:
            return {edge.body_post: 0.0 for edge in edges}
        maximum = max(math.log1p(edge.weight) for edge in edges)
        ranked = sorted(
            (
                (edge.body_post, smell * math.log1p(edge.weight) / maximum)
                for edge in edges
            ),
            key=lambda item: (-item[1], item[0]),
        )
        active_count = max(1, math.ceil(len(ranked) * self.config.active_kc_fraction))
        active_ids = {body_id for body_id, _ in ranked[:active_count]}
        return {body_id: value if body_id in active_ids else 0.0 for body_id, value in ranked}

    def _mbon_response(self, activity: dict[int, float]) -> dict[str, float]:
        multipliers = {item.key: item.multiplier for item in self.memory.synapses}
        response = {}
        for side, mbon_id in self.circuit.mbon01_neurons.items():
            edges = tuple(edge for edge in self.circuit.plastic_edges if edge.body_post == mbon_id)
            total = sum(math.log1p(edge.weight) for edge in edges)
            response[side] = sum(
                activity.get(edge.body_pre, 0.0)
                * math.log1p(edge.weight)
                * multipliers[(edge.body_pre, edge.body_post)]
                for edge in edges
            ) / total if total else 0.0
        return response

    def _mean_eligibility(self) -> float:
        if not self._eligibility:
            return 0.0
        return sum(self._eligibility.values()) / len(self._eligibility)

    def _learning_state(self, reward: float, *, changed: bool) -> LearningState:
        return LearningState(
            memory=self.memory,
            reward=reward,
            association_strength=self.memory.association_strength,
            mean_eligibility=self._mean_eligibility(),
            active_kcs=self._active_kcs,
            changed=changed,
            pam_activity=reward,
        )


def _clamp01(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("learning signal must be finite")
    return min(1.0, max(0.0, value))


def _read_edges(items: list[dict[str, int]]) -> tuple[LearningEdge, ...]:
    edges = tuple(LearningEdge(**item) for item in items)
    triples = {(edge.body_pre, edge.body_post, edge.weight) for edge in edges}
    if len(triples) != len(edges):
        raise DataIntegrityError("Learning circuit contains duplicate edges")
    return edges


def _side_mapping(value: dict[str, int]) -> dict[str, int]:
    return {str(side): int(body_id) for side, body_id in value.items()}


def _require_annotation(
    annotations: MaleCNSAnnotations,
    body_id: int,
    neuron_type: str,
    *,
    neuron_class: str | None = None,
    side: str | None = None,
) -> None:
    annotation = annotations.require_body(body_id)
    if annotation.type != neuron_type:
        raise DataIntegrityError(f"Body {body_id} is not official type {neuron_type}")
    if neuron_class is not None and annotation.neuron_class != neuron_class:
        raise DataIntegrityError(f"Body {body_id} is not official class {neuron_class}")
    if side is not None and annotation.effective_side != side:
        raise DataIntegrityError(f"Body {body_id} is not on side {side}")
