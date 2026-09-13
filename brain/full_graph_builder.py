"""Offline conversion of official MaleCNS tables into a sparse neural graph."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
from scipy.sparse import csr_matrix

from brain.data import DataIntegrityError, SourceManifest, file_sha256
from brain.full_graph import (
    DYNAMICS,
    FILTER_NAME,
    POLARITY_POLICY,
    FullGraphMetadata,
    FullGraphRepository,
    SCHEMA_VERSION,
)


OFFICIAL_NEURON_COUNT = 166_606
OFFICIAL_CONNECTED_NEURON_COUNT = 166_400
OFFICIAL_EDGE_COUNT = 25_574_615
@dataclass(frozen=True, slots=True)
class ExpectedGraphCounts:
    neurons: int = OFFICIAL_NEURON_COUNT
    connected_neurons: int = OFFICIAL_CONNECTED_NEURON_COUNT
    edges: int = OFFICIAL_EDGE_COUNT


class FullGraphBuilder:
    NEGATIVE_TRANSMITTERS = frozenset({"gaba", "glutamate", "histamine"})

    def __init__(
        self,
        source: SourceManifest,
        raw_directory: Path,
        expected: ExpectedGraphCounts = ExpectedGraphCounts(),
    ) -> None:
        self.source = source
        self.raw_directory = raw_directory
        self.expected = expected

    def build(self, output: Path) -> FullGraphMetadata:
        paths = self._verified_paths()
        body_ids = self._valid_body_ids(paths["annotations"])
        edge_table = self._valid_edges(paths["weights"], body_ids)
        connected = self._connected_count(edge_table)
        self._validate_counts(len(body_ids), connected, edge_table.num_rows)
        signs, transmitter_counts = self._signs(paths["neurotransmitters"], body_ids)
        matrix = self._matrix(edge_table, body_ids, signs)
        metadata = FullGraphMetadata(
            schema_version=SCHEMA_VERSION,
            dataset=self.source.dataset,
            neuron_count=len(body_ids),
            connected_neuron_count=connected,
            edge_count=matrix.nnz,
            source_sha256={name: asset.sha256 for name, asset in self.source.sources.items()},
            filter_name=FILTER_NAME,
            polarity_policy=POLARITY_POLICY,
            dynamics=DYNAMICS,
            transmitter_counts=dict(sorted(transmitter_counts.items())),
        )
        self._publish(output, metadata, body_ids, matrix, signs)
        return metadata

    def _verified_paths(self) -> dict[str, Path]:
        paths = {
            name: self.source.asset_path(name, self.raw_directory)
            for name in ("annotations", "weights", "neurotransmitters")
        }
        for name, path in paths.items():
            if not path.is_file():
                raise DataIntegrityError(f"Missing MaleCNS source file: {path}")
            if file_sha256(path) != self.source.sources[name].sha256:
                raise DataIntegrityError(f"Checksum mismatch for {path}")
        return paths

    def _valid_body_ids(self, path: Path) -> np.ndarray:
        frame = pd.read_feather(path, columns=["bodyId", "superclass"])
        if frame["bodyId"].duplicated().any():
            raise DataIntegrityError("Duplicate bodyId values in annotation data")
        valid = frame["superclass"].notna() & frame["superclass"].ne("")
        valid &= ~frame["superclass"].str.contains("tbc", na=False)
        return np.sort(frame.loc[valid, "bodyId"].to_numpy(dtype=np.int64))

    def _valid_edges(self, path: Path, body_ids: np.ndarray) -> pa.Table:
        table = feather.read_table(
            path,
            columns=["body_pre", "body_post", "weight"],
            memory_map=True,
        )
        ids = pa.array(body_ids)
        mask = pc.and_(
            pc.is_in(table["body_pre"], value_set=ids),
            pc.is_in(table["body_post"], value_set=ids),
        )
        filtered = table.filter(mask)
        if filtered.num_rows and pc.any(pc.less_equal(filtered["weight"], 0)).as_py():
            raise DataIntegrityError("Full brain structural weights must be positive")
        return filtered

    def _connected_count(self, edges: pa.Table) -> int:
        endpoints = pa.concat_arrays(
            [
                pc.unique(edges["body_pre"]),
                pc.unique(edges["body_post"]),
            ]
        )
        return len(pc.unique(endpoints))

    def _validate_counts(self, neurons: int, connected: int, edges: int) -> None:
        if neurons != self.expected.neurons:
            raise DataIntegrityError(
                f"Full brain neuron count {neurons:,} does not match expected {self.expected.neurons:,}"
            )
        if connected != self.expected.connected_neurons:
            raise DataIntegrityError(
                "Full brain connected-neuron count "
                f"{connected:,} does not match expected {self.expected.connected_neurons:,}"
            )
        if edges != self.expected.edges:
            raise DataIntegrityError(
                f"Full brain edge count {edges:,} does not match expected {self.expected.edges:,}"
            )

    def _signs(self, path: Path, body_ids: np.ndarray) -> tuple[np.ndarray, Counter[str]]:
        frame = pd.read_feather(path, columns=["body", "consensus_nt"])
        frame = frame[frame["body"].isin(body_ids)].copy()
        frame["consensus_nt"] = frame["consensus_nt"].astype("string").str.lower()
        informative = frame[
            frame["consensus_nt"].notna() & frame["consensus_nt"].ne("unclear")
        ]
        conflicts = informative.groupby("body")["consensus_nt"].nunique()
        if (conflicts > 1).any():
            body_id = int(conflicts[conflicts > 1].index[0])
            raise DataIntegrityError(f"Conflicting transmitter calls for body {body_id}")
        calls = informative.drop_duplicates("body").set_index("body")["consensus_nt"].to_dict()
        names = [str(calls.get(int(body_id), "missing")) for body_id in body_ids]
        signs = np.fromiter((self._sign(name) for name in names), dtype=np.float32)
        return signs, Counter(names)

    def _sign(self, transmitter: str) -> float:
        if transmitter == "acetylcholine":
            return 1.0
        if transmitter in self.NEGATIVE_TRANSMITTERS:
            return -1.0
        return 0.0

    def _matrix(
        self,
        edges: pa.Table,
        body_ids: np.ndarray,
        signs: np.ndarray,
    ) -> csr_matrix:
        pre_ids = edges["body_pre"].combine_chunks().to_numpy(zero_copy_only=False)
        post_ids = edges["body_post"].combine_chunks().to_numpy(zero_copy_only=False)
        raw = edges["weight"].combine_chunks().to_numpy(zero_copy_only=False)
        pre = np.searchsorted(body_ids, pre_ids).astype(np.int32)
        post = np.searchsorted(body_ids, post_ids).astype(np.int32)
        magnitudes = np.log1p(raw.astype(np.float32))
        incoming = np.bincount(post, weights=magnitudes, minlength=len(body_ids)).astype(np.float32)
        normalized = magnitudes / incoming[post]
        values = normalized * signs[pre]
        matrix = csr_matrix((values, (post, pre)), shape=(len(body_ids), len(body_ids)))
        matrix.sort_indices()
        if matrix.nnz != edges.num_rows:
            raise DataIntegrityError("Duplicate full brain edges changed the CSR edge count")
        return matrix

    def _publish(
        self,
        output: Path,
        metadata: FullGraphMetadata,
        body_ids: np.ndarray,
        matrix: csr_matrix,
        signs: np.ndarray,
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
        backup = output.with_name(f"{output.name}.bak")
        try:
            (temporary / "metadata.json").write_text(
                json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            np.save(temporary / "body_ids.npy", body_ids.astype(np.int64, copy=False))
            np.save(temporary / "indptr.npy", matrix.indptr.astype(np.int64, copy=False))
            np.save(temporary / "indices.npy", matrix.indices.astype(np.int32, copy=False))
            np.save(temporary / "weights.npy", matrix.data.astype(np.float32, copy=False))
            np.save(temporary / "signs.npy", signs.astype(np.float32, copy=False))
            FullGraphRepository(temporary).load(self.source)
            if backup.exists():
                shutil.rmtree(backup)
            if output.exists():
                os.replace(output, backup)
            os.replace(temporary, output)
        except Exception:
            if output.exists() is False and backup.exists():
                os.replace(backup, output)
            raise
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
