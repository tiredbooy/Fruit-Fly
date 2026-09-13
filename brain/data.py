"""Validated access to pinned MaleCNS data releases."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather


class DataIntegrityError(ValueError):
    """Raised when a connectome asset does not match its declared source."""


@dataclass(frozen=True, slots=True)
class SourceAsset:
    url: str
    sha256: str

    @property
    def filename(self) -> str:
        return Path(urlparse(self.url).path).name


@dataclass(frozen=True, slots=True)
class SourceManifest:
    dataset: str
    sources: dict[str, SourceAsset]

    @classmethod
    def from_json(cls, path: Path) -> "SourceManifest":
        document = json.loads(path.read_text(encoding="utf-8"))
        sources = {
            name: SourceAsset(url=value["url"], sha256=value["sha256"])
            for name, value in document["sources"].items()
        }
        return cls(dataset=document["dataset"], sources=sources)

    def asset_path(self, name: str, raw_directory: Path) -> Path:
        try:
            return raw_directory / self.sources[name].filename
        except KeyError as error:
            raise DataIntegrityError(f"Unknown source asset: {name}") from error


@dataclass(frozen=True, slots=True)
class NeuronAnnotation:
    body_id: int
    type: str | None
    instance: str | None
    side: str | None
    status: str | None
    optic_hex_1: float | None
    optic_hex_2: float | None
    dataset: str
    neuron_class: str | None = None

    @property
    def effective_side(self) -> str | None:
        if self.side in {"L", "R", "M"}:
            return self.side
        if self.instance and self.instance.endswith(("_L", "_R", "_M")):
            return self.instance[-1]
        return None


class MaleCNSAnnotations:
    REQUIRED_COLUMNS = frozenset(
        {
            "bodyId",
            "type",
            "instance",
            "somaSide",
            "statusLabel",
            "assignedOlHex1",
            "assignedOlHex2",
        }
    )

    def __init__(self, records: dict[int, NeuronAnnotation], dataset: str) -> None:
        self._records = records
        self.dataset = dataset

    @classmethod
    def from_feather(
        cls,
        path: Path,
        *,
        dataset: str,
        expected_sha256: str | None = None,
    ) -> "MaleCNSAnnotations":
        if expected_sha256 and file_sha256(path) != expected_sha256:
            raise DataIntegrityError(f"Checksum mismatch for {path}")

        frame = pd.read_feather(path)
        missing = cls.REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            raise DataIntegrityError(f"Missing annotation columns: {sorted(missing)}")
        if frame["bodyId"].duplicated().any():
            raise DataIntegrityError("Duplicate bodyId values in annotation data")
        if "class" not in frame.columns:
            frame["class"] = None
        frame = frame.rename(columns={"class": "neuronClass"})

        records = {
            int(row.bodyId): NeuronAnnotation(
                body_id=int(row.bodyId),
                type=_optional_text(row.type),
                instance=_optional_text(row.instance),
                side=_optional_text(row.somaSide),
                status=_optional_text(row.statusLabel),
                optic_hex_1=_optional_number(row.assignedOlHex1),
                optic_hex_2=_optional_number(row.assignedOlHex2),
                dataset=dataset,
                neuron_class=_optional_text(row.neuronClass),
            )
            for row in frame.itertuples(index=False)
        }
        return cls(records, dataset)

    def require_body(self, body_id: int) -> NeuronAnnotation:
        try:
            return self._records[body_id]
        except KeyError as error:
            raise DataIntegrityError(f"Unknown MaleCNS bodyId: {body_id}") from error

    def bodies_of_type(self, neuron_type: str) -> tuple[NeuronAnnotation, ...]:
        return tuple(record for record in self._records.values() if record.type == neuron_type)

    def bodies_of_types(self, neuron_types: frozenset[str]) -> tuple[NeuronAnnotation, ...]:
        return tuple(record for record in self._records.values() if record.type in neuron_types)

    def __len__(self) -> int:
        return len(self._records)


class ConnectomeEdges:
    REQUIRED_COLUMNS = ("body_pre", "body_post", "weight")

    def __init__(self, table: pa.Table) -> None:
        self._table = table

    @classmethod
    def from_feather(
        cls,
        path: Path,
        *,
        expected_sha256: str | None = None,
    ) -> "ConnectomeEdges":
        if expected_sha256 and file_sha256(path) != expected_sha256:
            raise DataIntegrityError(f"Checksum mismatch for {path}")
        table = feather.read_table(path, columns=list(cls.REQUIRED_COLUMNS), memory_map=True)
        missing = set(cls.REQUIRED_COLUMNS).difference(table.column_names)
        if missing:
            raise DataIntegrityError(f"Missing connectivity columns: {sorted(missing)}")
        return cls(table)

    @property
    def count(self) -> int:
        return self._table.num_rows

    def row(self, index: int) -> tuple[int, int, int]:
        return tuple(int(self._table[column][index].as_py()) for column in self.REQUIRED_COLUMNS)

    def require_edges(self, expected: tuple[tuple[int, int, int], ...]) -> None:
        source_ids = pa.array(sorted({item[0] for item in expected}), type=pa.int64())
        matching_sources = pc.is_in(self._table["body_pre"], value_set=source_ids)
        subset = self._table.filter(matching_sources)
        observed = {
            (int(row.body_pre), int(row.body_post), int(row.weight))
            for row in subset.to_pandas().itertuples(index=False)
        }
        missing = set(expected).difference(observed)
        if missing:
            sample = sorted(missing)[0]
            raise DataIntegrityError(f"Runtime edge is absent from MaleCNS weights: {sample}")


class NeuronTransmitters:
    """Official per-body consensus transmitter calls used to sign connections."""

    REQUIRED_COLUMNS = ("body", "consensus_nt")
    KNOWN_POLARITIES = frozenset({"acetylcholine", "gaba"})

    def __init__(self, table: pa.Table) -> None:
        bodies = table["body"].to_pylist()
        calls = table["consensus_nt"].to_pylist()
        self._calls = {
            int(body): str(call)
            for body, call in zip(bodies, calls, strict=True)
            if call is not None and call != "unclear"
        }

    @classmethod
    def from_feather(
        cls,
        path: Path,
        *,
        expected_sha256: str | None = None,
    ) -> "NeuronTransmitters":
        if expected_sha256 and file_sha256(path) != expected_sha256:
            raise DataIntegrityError(f"Checksum mismatch for {path}")
        table = feather.read_table(path, columns=list(cls.REQUIRED_COLUMNS), memory_map=True)
        missing = set(cls.REQUIRED_COLUMNS).difference(table.column_names)
        if missing:
            raise DataIntegrityError(f"Missing neurotransmitter columns: {sorted(missing)}")
        return cls(table)

    def require_known(self, body_id: int) -> str:
        call = self._calls.get(body_id)
        if call not in self.KNOWN_POLARITIES:
            raise DataIntegrityError(
                f"Body {body_id} has no supported MaleCNS polarity: {call or 'missing'}"
            )
        return call

    def require_call(self, body_id: int, expected: str) -> str:
        call = self._calls.get(body_id)
        if call != expected:
            raise DataIntegrityError(
                f"Body {body_id} has MaleCNS transmitter {call or 'missing'}, expected {expected}"
            )
        return call


@dataclass(frozen=True, slots=True)
class LoadedMaleCNS:
    annotations: MaleCNSAnnotations
    edges: ConnectomeEdges
    transmitters: NeuronTransmitters


def load_release(manifest: SourceManifest, raw_directory: Path) -> LoadedMaleCNS:
    annotation_asset = manifest.sources["annotations"]
    weight_asset = manifest.sources["weights"]
    transmitter_asset = manifest.sources["neurotransmitters"]
    annotations = MaleCNSAnnotations.from_feather(
        manifest.asset_path("annotations", raw_directory),
        dataset=manifest.dataset,
        expected_sha256=annotation_asset.sha256,
    )
    edges = ConnectomeEdges.from_feather(
        manifest.asset_path("weights", raw_directory),
        expected_sha256=weight_asset.sha256,
    )
    transmitters = NeuronTransmitters.from_feather(
        manifest.asset_path("neurotransmitters", raw_directory),
        expected_sha256=transmitter_asset.sha256,
    )
    return LoadedMaleCNS(
        annotations=annotations,
        edges=edges,
        transmitters=transmitters,
    )


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    return str(value)


def _optional_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    return float(value)
