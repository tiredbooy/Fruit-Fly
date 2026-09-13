"""Validated, versioned persistence for learned synaptic multipliers."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
import os
from pathlib import Path
import tempfile


SCHEMA_VERSION = 1


class MemoryValidationError(ValueError):
    """Raised when persisted memory cannot be safely applied to its circuit."""


@dataclass(frozen=True, slots=True)
class SynapseMemory:
    body_pre: int
    body_post: int
    baseline_weight: int
    multiplier: float = 1.0

    @property
    def key(self) -> tuple[int, int]:
        return self.body_pre, self.body_post

    def __post_init__(self) -> None:
        if self.baseline_weight < 1:
            raise MemoryValidationError("baseline weight must be positive")
        if not math.isfinite(self.multiplier) or not 0.0 <= self.multiplier <= 1.0:
            raise MemoryValidationError("synaptic multiplier must be finite and within 0..1")


@dataclass(frozen=True, slots=True)
class MemoryState:
    schema_version: int
    dataset: str
    weights_sha256: str
    model: str
    reward_events: int
    total_reward: float
    synapses: tuple[SynapseMemory, ...]

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise MemoryValidationError(f"unsupported memory schema: {self.schema_version}")
        if self.reward_events < 0:
            raise MemoryValidationError("reward event count cannot be negative")
        if not math.isfinite(self.total_reward) or self.total_reward < 0.0:
            raise MemoryValidationError("total reward must be finite and non-negative")
        keys = tuple(item.key for item in self.synapses)
        if len(keys) != len(set(keys)):
            raise MemoryValidationError("memory contains duplicate synapses")

    @classmethod
    def fresh(
        cls,
        *,
        dataset: str,
        weights_sha256: str,
        model: str,
        plastic_edges: tuple[tuple[int, int, int], ...],
    ) -> "MemoryState":
        synapses = tuple(
            SynapseMemory(body_pre, body_post, weight)
            for body_pre, body_post, weight in sorted(plastic_edges)
        )
        return cls(SCHEMA_VERSION, dataset, weights_sha256, model, 0, 0.0, synapses)

    @property
    def association_strength(self) -> float:
        if not self.synapses:
            return 0.0
        return 1.0 - sum(item.multiplier for item in self.synapses) / len(self.synapses)

    def with_updates(
        self,
        updates: dict[tuple[int, int], float],
        *,
        reward: float,
    ) -> "MemoryState":
        if not math.isfinite(reward) or not 0.0 <= reward <= 1.0:
            raise MemoryValidationError("reward must be finite and within 0..1")
        known = {item.key for item in self.synapses}
        unknown = set(updates).difference(known)
        if unknown:
            raise MemoryValidationError(f"memory update contains unknown synapse: {min(unknown)}")
        changed = tuple(
            replace(item, multiplier=updates.get(item.key, item.multiplier))
            for item in self.synapses
        )
        return replace(
            self,
            reward_events=self.reward_events + int(reward > 0.0),
            total_reward=self.total_reward + reward,
            synapses=changed,
        )


class MemoryRepository:
    """JSON gateway that validates compatibility before returning memory state."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_or_create(self, template: MemoryState) -> MemoryState:
        if not self.path.is_file():
            return template
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
            loaded = self._from_document(document)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, MemoryValidationError):
                raise
            raise MemoryValidationError(f"invalid memory file: {error}") from error
        self._require_compatible(loaded, template)
        return loaded

    def save(self, state: MemoryState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        document = self._to_document(state)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as destination:
                temporary_path = Path(destination.name)
                json.dump(document, destination, indent=2, sort_keys=True, allow_nan=False)
                destination.write("\n")
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def reset_with_backup(self) -> Path | None:
        if not self.path.exists():
            return None
        backup = self.path.with_name(f"{self.path.name}.bak")
        os.replace(self.path, backup)
        return backup

    @staticmethod
    def _to_document(state: MemoryState) -> dict[str, object]:
        return {
            "schema_version": state.schema_version,
            "dataset": state.dataset,
            "weights_sha256": state.weights_sha256,
            "model": state.model,
            "reward_events": state.reward_events,
            "total_reward": state.total_reward,
            "synapses": [
                {
                    "body_pre": item.body_pre,
                    "body_post": item.body_post,
                    "baseline_weight": item.baseline_weight,
                    "multiplier": item.multiplier,
                }
                for item in state.synapses
            ],
        }

    @staticmethod
    def _from_document(document: dict[str, object]) -> MemoryState:
        raw_synapses = document["synapses"]
        if not isinstance(raw_synapses, list):
            raise MemoryValidationError("memory synapses must be a list")
        synapses = tuple(SynapseMemory(**item) for item in raw_synapses)
        return MemoryState(
            schema_version=document["schema_version"],
            dataset=document["dataset"],
            weights_sha256=document["weights_sha256"],
            model=document["model"],
            reward_events=document["reward_events"],
            total_reward=document["total_reward"],
            synapses=synapses,
        )

    @staticmethod
    def _require_compatible(loaded: MemoryState, template: MemoryState) -> None:
        for field_name in ("dataset", "weights_sha256", "model"):
            if getattr(loaded, field_name) != getattr(template, field_name):
                raise MemoryValidationError(f"memory {field_name} does not match this experiment")
        loaded_edges = {
            (item.body_pre, item.body_post, item.baseline_weight)
            for item in loaded.synapses
        }
        template_edges = {
            (item.body_pre, item.body_post, item.baseline_weight)
            for item in template.synapses
        }
        if loaded_edges != template_edges:
            raise MemoryValidationError("memory synapse set does not match this experiment")
