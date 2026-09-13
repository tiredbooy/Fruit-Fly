import { expect, test } from "bun:test";
import * as THREE from "three/webgpu";
import { disposeScene } from "./scene-primitives";

test("disposes shared point-cloud geometry and material exactly once", () => {
  const scene = new THREE.Group();
  const geometry = new THREE.BufferGeometry();
  const material = new THREE.PointsMaterial();
  let geometryDisposals = 0;
  let materialDisposals = 0;
  geometry.addEventListener("dispose", () => geometryDisposals++);
  material.addEventListener("dispose", () => materialDisposals++);
  scene.add(new THREE.Points(geometry, material), new THREE.Points(geometry, material));

  disposeScene(scene);

  expect(geometryDisposals).toBe(1);
  expect(materialDisposals).toBe(1);
});

test("deduplicates resources shared by points, meshes, and lines", () => {
  const scene = new THREE.Group();
  const geometry = new THREE.BufferGeometry();
  const material = new THREE.ShaderMaterial();
  let geometryDisposals = 0;
  let materialDisposals = 0;
  geometry.addEventListener("dispose", () => geometryDisposals++);
  material.addEventListener("dispose", () => materialDisposals++);
  scene.add(
    new THREE.Points(geometry, [material, material]),
    new THREE.Mesh(geometry, material),
    new THREE.Line(geometry, material),
  );

  disposeScene(scene);

  expect(geometryDisposals).toBe(1);
  expect(materialDisposals).toBe(1);
});
