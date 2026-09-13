import * as THREE from "three";

export const MAX_NEURAL_PARTICLES = 64;

export function createChamber(): THREE.Group {
  const group = new THREE.Group();
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(20, 12),
    new THREE.MeshStandardMaterial({ color: "#101820", roughness: 0.88, metalness: 0.08 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  const grid = new THREE.GridHelper(20, 20, "#355565", "#1b2c36");
  grid.scale.z = 0.6;
  grid.position.y = 0.015;
  const rim = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(20, 0.35, 12)),
    new THREE.LineBasicMaterial({ color: "#58d6d0" }),
  );
  rim.position.y = 0.16;
  group.add(floor, grid, rim);
  return group;
}

export function createFly(): {
  group: THREE.Group;
  leftWing: THREE.Mesh;
  rightWing: THREE.Mesh;
} {
  const group = new THREE.Group();
  const dark = new THREE.MeshStandardMaterial({
    color: "#11171b",
    roughness: 0.55,
    metalness: 0.45,
  });
  const amber = new THREE.MeshStandardMaterial({ color: "#b86f28", roughness: 0.64 });
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.48, 20, 14), dark);
  body.scale.set(1.35, 0.85, 0.8);
  body.castShadow = true;
  const abdomen = new THREE.Mesh(new THREE.SphereGeometry(0.42, 20, 14), amber);
  abdomen.position.x = -0.68;
  abdomen.scale.set(1.5, 0.72, 0.72);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.34, 18, 12), dark);
  head.position.x = 0.62;
  const wingMaterial = new THREE.MeshPhysicalMaterial({
    color: "#bceae8",
    transparent: true,
    opacity: 0.42,
    side: THREE.DoubleSide,
    roughness: 0.18,
  });
  const wingGeometry = new THREE.CircleGeometry(0.6, 20);
  const leftWing = new THREE.Mesh(wingGeometry, wingMaterial);
  leftWing.position.set(-0.12, 0.18, 0.58);
  leftWing.scale.set(1.7, 0.64, 1);
  leftWing.rotation.set(-0.28, 0.18, 0.1);
  const rightWing = leftWing.clone();
  rightWing.position.z = -0.58;
  rightWing.rotation.set(-0.28, -0.18, -0.1);
  group.add(body, abdomen, head, leftWing, rightWing);
  group.position.y = 0.5;
  return { group, leftWing, rightWing };
}

export function createFood(): THREE.Group {
  const group = new THREE.Group();
  const core = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.34, 1),
    new THREE.MeshStandardMaterial({
      color: "#f2b84b",
      emissive: "#a55419",
      emissiveIntensity: 1.4,
      roughness: 0.48,
    }),
  );
  core.castShadow = true;
  const light = new THREE.PointLight("#f2b84b", 1.8, 5);
  light.position.y = 1;
  group.add(core, light);
  group.visible = false;
  return group;
}

export function createOdorHalo(): THREE.Mesh {
  const mesh = new THREE.Mesh(
    new THREE.RingGeometry(0.9, 1.05, 64),
    new THREE.MeshBasicMaterial({
      color: "#f2b84b",
      transparent: true,
      opacity: 0.34,
      side: THREE.DoubleSide,
    }),
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.visible = false;
  return mesh;
}

export function createTrail(): THREE.Line {
  const positions = new THREE.BufferAttribute(new Float32Array(80 * 3), 3);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", positions);
  geometry.setDrawRange(0, 0);
  return new THREE.Line(
    geometry,
    new THREE.LineBasicMaterial({ color: "#58d6d0", transparent: true, opacity: 0.58 }),
  );
}

export function createNeuralHalo(): {
  group: THREE.Group;
  mesh: THREE.InstancedMesh;
  material: THREE.MeshStandardMaterial;
  positions: THREE.Vector3[];
} {
  const group = new THREE.Group();
  const material = new THREE.MeshStandardMaterial({
    color: "#e36da6",
    emissive: "#e36da6",
    emissiveIntensity: 1.2,
  });
  const mesh = new THREE.InstancedMesh(
    new THREE.SphereGeometry(0.07, 8, 6),
    material,
    MAX_NEURAL_PARTICLES,
  );
  const positions = Array.from({ length: MAX_NEURAL_PARTICLES }, (_, index) => {
    const angle = index * 2.399963;
    const radius = 1.1 + (index % 5) * 0.08;
    return new THREE.Vector3(
      Math.cos(angle) * radius,
      0.45 + (index % 7) * 0.12,
      Math.sin(angle) * radius,
    );
  });
  group.add(mesh);
  return { group, mesh, material, positions };
}
