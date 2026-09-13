"""Export only measured MaleCNS somata for the read-only anatomical observer.

Run from the repository root with the project Python environment. Coordinates
are centered and uniformly scaled, preserving their relative atlas geometry.
No neuron is assigned a substitute position when its measurement is missing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Any

import numpy as np
import pandas as pd


def measured_positions(rows: Iterable[Mapping[str, Any]]) -> tuple[list[list], int]:
    """Return sorted [official body ID, x, y, z] points and eligible body count."""
    measured: list[tuple[int, np.ndarray]] = []
    eligible = 0
    for row in rows:
        superclass = row.get("superclass")
        if not isinstance(superclass, str) or not superclass or "tbc" in superclass.lower():
            continue
        eligible += 1
        coordinates = row.get("somaLocation")
        if not isinstance(coordinates, (list, tuple, np.ndarray)):
            continue
        point = np.asarray(coordinates, dtype=float)
        if point.shape != (3,) or not np.isfinite(point).all():
            continue
        measured.append((int(row["bodyId"]), point))
    if not measured:
        return [], eligible
    measured.sort(key=lambda pair: pair[0])
    positions = np.array([point for _, point in measured])
    center = (positions.min(axis=0) + positions.max(axis=0)) / 2
    extent = float(np.ptp(positions, axis=0).max())
    positions = (positions - center) * (2 / extent if extent else 1)
    return [[body_id, *map(float, point)] for (body_id, _), point in zip(measured, positions)], eligible


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "data/malecns/v1.0/source-manifest.json").read_text())
    source = manifest["sources"]["annotations"]
    path = root / "data/raw/malecns/v1.0" / source["url"].rsplit("/", 1)[-1]
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if digest != source["sha256"]:
        raise ValueError("Official annotations checksum mismatch")
    table = pd.read_feather(path, columns=["bodyId", "superclass", "somaLocation"])
    points, eligible = measured_positions(table.to_dict("records"))
    artifact = {
        "schema": 1, "dataset": manifest["dataset"],
        "source": source, "license": manifest["license"],
        "transform": "Bounding-box center; uniform scale to maximum extent 2; atlas axes preserved",
        "eligible_count": eligible, "measured_count": len(points),
        "points": [[row[0], *[round(value, 7) for value in row[1:]]] for row in points],
    }
    destination = root / "frontend/web/public/assets/neuron-positions.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(artifact, separators=(",", ":")) + "\n")
    print(f"Exported {len(points)} measured somata / {eligible} eligible bodies: {destination}")


if __name__ == "__main__":
    main()
