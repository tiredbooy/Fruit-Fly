import * as THREE from "three/webgpu";

/** A dimensional specimen arena. Only its top rectangle is physically walkable. */
export function createWorldScene(): THREE.Group {
  const world = new THREE.Group();
  const surface = new THREE.MeshStandardMaterial({ color: "#53665b", roughness: 0.96 });
  const edge = new THREE.MeshStandardMaterial({ color: "#233d37", roughness: 0.8 });
  const trim = new THREE.MeshStandardMaterial({ color: "#789085", roughness: 0.45, metalness: 0.45 });
  const floor = new THREE.Mesh(new THREE.BoxGeometry(20, 0.6, 12), surface);
  floor.position.y = -0.3;
  floor.receiveShadow = true;
  floor.castShadow = true;
  world.add(floor);
  const pedestal = new THREE.Mesh(new THREE.BoxGeometry(21, 0.7, 13), edge);
  pedestal.position.y = -0.95;
  pedestal.castShadow = true;
  pedestal.receiveShadow = true;
  world.add(pedestal);
  for (const z of [-6.08, 6.08]) addRail(world, [20.3, 0.16, 0.16], [0, 0.08, z], trim);
  for (const x of [-10.08, 10.08]) addRail(world, [0.16, 0.16, 12], [x, 0.08, 0], trim);
  // Sparse scale markings on the rim communicate the real arena dimensions.
  const ticks = new THREE.InstancedMesh(new THREE.BoxGeometry(0.025, 0.015, 0.25), trim, 38);
  const transform = new THREE.Matrix4();
  let index = 0;
  for (const z of [-5.83, 5.83]) {
    for (let x = -9; x <= 9; x += 1) ticks.setMatrixAt(index++, transform.makeTranslation(x, 0.012, z));
  }
  world.add(ticks);
  const table = new THREE.Mesh(
    new THREE.PlaneGeometry(120, 120),
    new THREE.MeshStandardMaterial({ color: "#172420", roughness: 1 }),
  );
  table.rotation.x = -Math.PI / 2;
  table.position.y = -1.35;
  table.receiveShadow = true;
  world.add(table);
  return world;
}

function addRail(world: THREE.Group, size: [number, number, number], position: [number, number, number], material: THREE.Material): void {
  const rail = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  rail.position.set(...position);
  rail.castShadow = true;
  world.add(rail);
}

export function lightWorld(scene: THREE.Scene): void {
  scene.background = new THREE.Color("#101c19");
  scene.fog = new THREE.Fog("#101c19", 65, 140);
  scene.add(new THREE.HemisphereLight("#e0efdf", "#384031", 1.5));
  const sun = new THREE.DirectionalLight("#ffdfaa", 2.4);
  sun.position.set(8, 17, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 14, bottom: -14, near: 1, far: 55 });
  sun.shadow.normalBias = 0.025;
  scene.add(sun);
  const fill = new THREE.DirectionalLight("#96d4d0", 1.1);
  fill.position.set(-12, 8, -8);
  scene.add(fill);
}
