"""Validated, memory-mapped representation of the full MaleCNS graph."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from brain.data import DataIntegrityError, SourceManifest


SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class FullGraphMetadata:
    schema_version: int
    dataset: str
    neuron_count: int
    connected_neuron_count: int
    edge_count: int
    source_sha256: dict[str, str]
    filter_name: str
    polarity_policy: str
    dynamics: str
    transmitter_counts: dict[str, int]

    @classmethod
    def from_document(cls, document: dict[str, object]) -> "FullGraphMetadata":
        try:
            return cls(
                schema_version=int(document["schema_version"]),
                dataset=str(document["dataset"]),
                neuron_count=int(document["neuron_count"]),
                connected_neuron_count=int(document["connected_neuron_count"]),
                edge_count=int(document["edge_count"]),
                source_sha256=dict(document["source_sha256"]),
                filter_name=str(document["filter_name"]),
                polarity_policy=str(document["polarity_policy"]),
                dynamics=str(document["dynamics"]),
                transmitter_counts={
                    str(name): int(count)
                    for name, count in dict(document["transmitter_counts"]).items()
                },
            )
        except (KeyError, TypeError, ValueError) as error:
            raise DataIntegrityError("Full brain metadata is malformed") from error


@dataclass(frozen=True, slots=True)
class FullGraph:
    metadata: FullGraphMetadata
    body_ids: np.ndarray
    indptr: np.ndarray
    indices: np.ndarray
    weights: np.ndarray
    signs: np.ndarray


class FullGraphRepository:
    ARRAY_DTYPES = {
        "body_ids": np.dtype(np.int64),
        "indptr": np.dtype(np.int64),
        "indices": np.dtype(np.int32),
        "weights": np.dtype(np.float32),
        "signs": np.dtype(np.float32),
    }

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, source: SourceManifest) -> FullGraph:
        try:
            document = json.loads((self.path / "metadata.json").read_text(encoding="utf-8"))
            arrays = {
                name: np.load(self.path / f"{name}.npy", mmap_mode="r", allow_pickle=False)
                for name in self.ARRAY_DTYPES
            }
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise DataIntegrityError(
                "Full brain artifact is missing or unreadable; run 'make brain-build' first"
            ) from error
        metadata = FullGraphMetadata.from_document(document)
        graph = FullGraph(metadata=metadata, **arrays)
        self._validate_metadata(metadata, source)
        self._validate_arrays(graph)
        return graph

    def _validate_metadata(self, metadata: FullGraphMetadata, source: SourceManifest) -> None:
        if metadata.schema_version != SCHEMA_VERSION:
            raise DataIntegrityError("Full brain artifact schema is incompatible")
        if metadata.dataset != source.dataset:
            raise DataIntegrityError("Full brain artifact dataset does not match")
        expected = {name: asset.sha256 for name, asset in source.sources.items()}
        if metadata.source_sha256 != expected:
            raise DataIntegrityError("Full brain artifact source checksum does not match")
        if metadata.neuron_count <= 0 or metadata.edge_count < 0:
            raise DataIntegrityError("Full brain artifact counts are invalid")
        if not 0 <= metadata.connected_neuron_count <= metadata.neuron_count:
            raise DataIntegrityError("Full brain connected-neuron count is invalid")

    def _validate_arrays(self, graph: FullGraph) -> None:
        arrays = {
            "body_ids": graph.body_ids,
            "indptr": graph.indptr,
            "indices": graph.indices,
            "weights": graph.weights,
            "signs": graph.signs,
        }
        for name, expected_dtype in self.ARRAY_DTYPES.items():
            if arrays[name].dtype != expected_dtype:
                raise DataIntegrityError(f"Full brain {name} dtype is invalid")
            if arrays[name].ndim != 1:
                raise DataIntegrityError(f"Full brain {name} must be one-dimensional")
        self._validate_shapes(graph)
        if np.any(np.diff(graph.body_ids) <= 0):
            raise DataIntegrityError("Full brain body IDs must be strictly increasing")
        if not np.all(np.isfinite(graph.weights)):
            raise DataIntegrityError("Full brain weights must be finite")
        if not np.all(np.isin(graph.signs, (-1.0, 0.0, 1.0))):
            raise DataIntegrityError("Full brain signs contain unsupported values")

    def _validate_shapes(self, graph: FullGraph) -> None:
        neurons = graph.metadata.neuron_count
        edges = graph.metadata.edge_count
        if len(graph.body_ids) != neurons or len(graph.signs) != neurons:
            raise DataIntegrityError("Full brain neuron array shapes are invalid")
        if len(graph.indptr) != neurons + 1:
            raise DataIntegrityError("Full brain CSR row count is invalid")
        if len(graph.indices) != edges or len(graph.weights) != edges:
            raise DataIntegrityError("Full brain CSR edge count is invalid")
        if graph.indptr[0] != 0 or graph.indptr[-1] != edges:
            raise DataIntegrityError("Full brain CSR boundaries are invalid")
        if np.any(np.diff(graph.indptr) < 0):
            raise DataIntegrityError("Full brain CSR boundaries are not monotonic")
        if edges and (np.min(graph.indices) < 0 or np.max(graph.indices) >= neurons):
            raise DataIntegrityError("Full brain CSR indices are out of range")
        connected = np.zeros(neurons, dtype=np.bool_)
        connected[graph.indices] = True
        connected[np.flatnonzero(np.diff(graph.indptr))] = True
        if int(np.count_nonzero(connected)) != graph.metadata.connected_neuron_count:
            raise DataIntegrityError("Full brain connected-neuron count does not match arrays")
