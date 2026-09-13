import * as THREE from "three/webgpu";

export const MAX_NEURAL_PARTICLES = 64;

export function createFood(): THREE.Group {
  const group = new THREE.Group();
  const fruit = new THREE.Mesh(
    new THREE.SphereGeometry(1, 24, 16),
    new THREE.MeshStandardMaterial({ color: "#e3a53e", roughness: 0.7 }),
  );
  fruit.scale.y = 0.75;
  fruit.position.y = 0.7;
  fruit.castShadow = true;
  const stem = new THREE.Mesh(
    new THREE.CylinderGeometry(0.06, 0.09, 0.6, 6),
    new THREE.MeshStandardMaterial({ color: "#4b5b28", roughness: 1 }),
  );
  stem.position.y = 1.6;
  stem.rotation.z = 0.22;
  group.add(fruit, stem);
  group.visible = false;
  return group;
}

export function createOdorHalo(): THREE.Mesh {
  const mesh = new THREE.Mesh(
    new THREE.RingGeometry(0.9, 0.94, 64),
    new THREE.MeshBasicMaterial({ color: "#f2b84b", transparent: true, opacity: 0.6, side: THREE.DoubleSide, depthWrite: false }),
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.visible = false;
  return mesh;
}

export function createTrail(): THREE.Line {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(80 * 3), 3));
  geometry.setDrawRange(0, 0);
  const trail = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: "#8bf7ed", transparent: true, opacity: 0.8 }));
  // The vertex buffer moves across the arena; its initial bounds are all zero.
  trail.frustumCulled = false;
  return trail;
}

export function createNeuralHalo() {
  const group = new THREE.Group();
  const material = new THREE.MeshBasicMaterial({ color: "#f69ec5", transparent: true, opacity: 0.65, depthWrite: false });
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(0.035, 6, 4), material, MAX_NEURAL_PARTICLES);
  mesh.count = 0;
  mesh.frustumCulled = false;
  const positions = Array.from({ length: MAX_NEURAL_PARTICLES }, (_, index) => {
    const angle = index * 2.399963;
    return new THREE.Vector3(Math.cos(angle) * 1.45, 1.5 + (index % 7) * 0.06, Math.sin(angle) * 1.45);
  });
  group.add(mesh);
  return { group, mesh, material, positions };
}

export function disposeScene(scene: THREE.Object3D): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  scene.traverse((object) => {
    if (!(object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points)) return;
    geometries.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) materials.add(material);
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
}
