"""Convert the openly licensed Zenodo CT surfaces to a small browser GLB.

Offline tool only: pip install trimesh==5.1.0 fast-simplification==0.2.0
The simulation never imports this tool or the source model's internal organs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_MD5 = "bc42defec0f3754ec1e441d8a9176ba3"
PARTS = {"exoskeleton": 45000, "wing_left": 6000, "wing_right": 6000, "halteres": 2500}


def build(archive: Path, destination: Path) -> None:
    raw = archive.read_bytes()
    if hashlib.md5(raw).hexdigest() != ARCHIVE_MD5:
        raise ValueError("Archive does not match the checksum published by Zenodo")
    meshes = {}
    counts = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as source:
        for part, target in PARTS.items():
            mesh = trimesh.load(
                io.BytesIO(source.read(f"Drosophila/Drosophila_{part}.stl")),
                file_type="stl",
            )
            counts[part] = {"source_triangles": len(mesh.faces)}
            mesh = mesh.simplify_quadric_decimation(face_count=target, aggression=7)
            # CT coordinates: head toward -Y, dorsal toward +Z. Browser: +X, +Y.
            mesh.vertices = mesh.vertices @ np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]])
            meshes[part] = mesh
    bounds = meshes["exoskeleton"].bounds
    center = (bounds[0] + bounds[1]) / 2
    center[1] = bounds[0, 1]
    scale = 2.2 / (bounds[1, 0] - bounds[0, 0])
    scene = trimesh.Scene()
    for part, mesh in meshes.items():
        mesh.vertices = (mesh.vertices - center) * scale
        wing = part.startswith("wing")
        material = trimesh.visual.material.PBRMaterial(
            name=part,
            baseColorFactor=[190, 211, 201, 105] if wing else [150, 96, 40, 255],
            metallicFactor=0.12 if wing else 0.05,
            roughnessFactor=0.4 if wing else 0.62,
            alphaMode="BLEND" if wing else "OPAQUE",
            doubleSided=wing,
        )
        mesh.visual = trimesh.visual.TextureVisuals(material=material)
        scene.add_geometry(mesh, geom_name=part, node_name=part)
        counts[part]["output_triangles"] = len(mesh.faces)
    destination.mkdir(parents=True, exist_ok=True)
    glb = trimesh.exchange.gltf.export_glb(scene, include_normals=True)
    (destination / "drosophila.glb").write_bytes(glb)
    manifest = {
        "source": "https://zenodo.org/records/14838021",
        "download": "https://zenodo.org/api/records/14838021/files/Drosophila.zip/content",
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "authors": ["Orestis Katsamenis", "Pieterjan De Boose", "Herman Wijnen", "Arno Thielens"],
        "specimen": "Adult female Drosophila melanogaster; visual body only, not the MaleCNS specimen",
        "source_md5": ARCHIVE_MD5,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "glb_sha256": hashlib.sha256(glb).hexdigest(),
        "glb_bytes": len(glb),
        "parts": counts,
        "changes": "Quadric mesh reduction; coordinate rotation/centering; 2.2-unit display scale; illustrative materials; external surfaces only",
        "tools": {"trimesh": "5.1.0", "fast-simplification": "0.2.0", "numpy": np.__version__},
    }
    (destination / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"bytes": len(glb), "triangles": sum(len(mesh.faces) for mesh in meshes.values())}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/visuals/drosophila-14838021.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "frontend/web/src/assets/fly")
    args = parser.parse_args()
    build(args.archive, args.output)
