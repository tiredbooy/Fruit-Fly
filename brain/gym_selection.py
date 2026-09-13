"""Bounded official edge scans and deterministic acetylcholine route selection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow.feather as feather


MINIMUM_WEIGHT = 10


@dataclass(frozen=True)
class Edge:
    pre: int
    post: int
    weight: int


def effective_side(row: object) -> str | None:
    for value in (getattr(row, "somaSide"), getattr(row, "rootSide")):
        if value in {"L", "R", "M"}:
            return value
    instance = getattr(row, "instance")
    if isinstance(instance, str) and instance.endswith(("_L", "_R", "_M")):
        return instance[-1]
    return None


class WeightScanner:
    """Scan the large Feather table in bounded record-batch chunks."""

    def __init__(self, path: Path) -> None:
        self.table = feather.read_table(
            path,
            columns=["body_pre", "body_post", "weight"],
            memory_map=True,
        )

    def select(
        self,
        *,
        pre_ids: set[int] | None = None,
        post_ids: set[int] | None = None,
        minimum_weight: int = MINIMUM_WEIGHT,
    ) -> list[Edge]:
        if pre_ids is None and post_ids is None:
            raise ValueError("At least one endpoint filter is required")
        pre_values = np.fromiter(sorted(pre_ids or ()), dtype=np.int64)
        post_values = np.fromiter(sorted(post_ids or ()), dtype=np.int64)
        selected: list[Edge] = []
        pre_chunks = self.table["body_pre"].chunks
        post_chunks = self.table["body_post"].chunks
        weight_chunks = self.table["weight"].chunks
        for pre_chunk, post_chunk, weight_chunk in zip(
            pre_chunks, post_chunks, weight_chunks, strict=True
        ):
            pres = pre_chunk.to_numpy(zero_copy_only=False)
            posts = post_chunk.to_numpy(zero_copy_only=False)
            weights = weight_chunk.to_numpy(zero_copy_only=False)
            mask = weights >= minimum_weight
            if pre_ids is not None:
                mask &= np.isin(pres, pre_values)
            if post_ids is not None:
                mask &= np.isin(posts, post_values)
            for pre, post, weight in zip(
                pres[mask], posts[mask], weights[mask], strict=True
            ):
                selected.append(Edge(int(pre), int(post), int(weight)))
        return selected


def choose_path(paths: list[tuple[Edge, ...]]) -> tuple[Edge, ...] | None:
    if not paths:
        return None
    return min(
        paths,
        key=lambda path: (
            len(path),
            -min(edge.weight for edge in path),
            -np.prod([edge.weight for edge in path], dtype=np.float64),
            tuple(edge.pre for edge in path) + (path[-1].post,),
        ),
    )


def route_paths(
    scanner: WeightScanner,
    sources: set[int],
    targets: set[int],
    ach_ids: set[int],
) -> list[tuple[Edge, ...]]:
    """Enumerate acetylcholine-only source-to-target paths of at most four hops."""
    reverse_one = [
        edge
        for edge in scanner.select(post_ids=targets)
        if edge.pre in ach_ids and edge.post in ach_ids
    ]
    reverse_one_nodes = {edge.pre for edge in reverse_one}
    reverse_two = [
        edge
        for edge in scanner.select(post_ids=reverse_one_nodes)
        if edge.pre in ach_ids and edge.post in ach_ids
    ]
    reverse_two_nodes = {edge.pre for edge in reverse_two}

    forward_one = [
        edge
        for edge in scanner.select(pre_ids=sources)
        if edge.pre in ach_ids and edge.post in ach_ids
    ]
    forward_one_nodes = {edge.post for edge in forward_one}
    forward_two = [
        edge
        for edge in scanner.select(
            pre_ids=forward_one_nodes,
            post_ids=reverse_one_nodes | reverse_two_nodes | targets,
        )
        if edge.pre in ach_ids and edge.post in ach_ids
    ]

    r1_by_pre: dict[int, list[Edge]] = defaultdict(list)
    r2_by_pre: dict[int, list[Edge]] = defaultdict(list)
    f2_by_pre: dict[int, list[Edge]] = defaultdict(list)
    for edge in reverse_one:
        r1_by_pre[edge.pre].append(edge)
    for edge in reverse_two:
        r2_by_pre[edge.pre].append(edge)
    for edge in forward_two:
        f2_by_pre[edge.pre].append(edge)

    paths: set[tuple[Edge, ...]] = set()
    for first in forward_one:
        if first.post in targets:
            paths.add((first,))
        for final in r1_by_pre[first.post]:
            paths.add((first, final))
        for middle in r2_by_pre[first.post]:
            for final in r1_by_pre[middle.post]:
                paths.add((first, middle, final))
        for second in f2_by_pre[first.post]:
            for middle in r2_by_pre[second.post]:
                for final in r1_by_pre[middle.post]:
                    paths.add((first, second, middle, final))
    return sorted(
        paths,
        key=lambda path: (
            path[0].pre,
            path[-1].post,
            len(path),
            tuple(edge.post for edge in path),
        ),
    )
