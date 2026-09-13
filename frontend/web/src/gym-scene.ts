import * as THREE from "three/webgpu";
import type { GymStation } from "./gym-types";
import { worldToScene } from "./scene-math";

/** The station footprint is received from Python, not a separate frontend arena. */
export function createGymStation(station: GymStation, world: {width: number; height: number}): THREE.Group {
  const group = new THREE.Group(); group.name = "resistance-lane";
  const center = worldToScene(station.x, station.y, world.width, world.height);
  group.position.set(center.x, 0, center.z);
  const width = station.width / world.width * 20, depth = station.height / world.height * 12;
  const rubber = new THREE.MeshStandardMaterial({ color: "#183333", roughness: 0.97 });
  const metal = new THREE.MeshStandardMaterial({ color: "#8ca4a2", metalness: 0.7, roughness: 0.4 });
  const mark = new THREE.MeshStandardMaterial({ color: "#58d6d0", roughness: 0.65 });
  const lane = new THREE.Mesh(new THREE.BoxGeometry(width, 0.025, depth), rubber);
  lane.position.y = 0.008; lane.receiveShadow = true; group.add(lane);
  for (const z of [-depth / 2, depth / 2]) {
    const edge = new THREE.Mesh(new THREE.BoxGeometry(width, 0.05, 0.055), mark);
    edge.position.set(0, 0.028, z); group.add(edge);
  }
  const strips = new THREE.InstancedMesh(new THREE.BoxGeometry(0.016, 0.006, depth - 0.1), metal, 24);
  const transform = new THREE.Matrix4();
  for (let index = 0; index < 24; index++) strips.setMatrixAt(index, transform.makeTranslation((index / 23 - 0.5) * (width - 0.12), 0.024, 0));
  group.add(strips);
  // End caps are visual apparatus, not unmodeled obstacles.
  for (const x of [-width / 2 - 0.12, width / 2 + 0.12]) {
    const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, depth + 0.14, 16), metal);
    roller.rotation.x = Math.PI / 2; roller.position.set(x, 0.08, 0); group.add(roller);
  }
  return group;
}
