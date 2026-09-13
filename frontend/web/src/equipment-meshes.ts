import { BoxGeometry, CylinderGeometry, Group, Mesh, MeshStandardMaterial } from "three/webgpu";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import type { EquipmentStation } from "./gym-types";

export function equipmentMaterials() {
  return {
    steel: new MeshStandardMaterial({color:"#b3c4c2",metalness:.75,roughness:.32}),
    iron: new MeshStandardMaterial({color:"#293b42",metalness:.6,roughness:.5}),
    rubber: new MeshStandardMaterial({color:"#112727",roughness:.92}),
    bench: new MeshStandardMaterial({color:"#378d88",roughness:.82}),
    curl: new MeshStandardMaterial({color:"#d39948",roughness:.7}),
  };
}
type Materials = ReturnType<typeof equipmentMaterials>;
type Triple = [number, number, number];

function box(group: Group, size: Triple, at: Triple, material: MeshStandardMaterial): void {
  const mesh = new Mesh(new BoxGeometry(...size), material);
  mesh.position.set(...at); mesh.castShadow = true; mesh.receiveShadow = true;
  group.add(mesh);
}

function cylinder(group: Group, radius: number, length: number, at: Triple, material: MeshStandardMaterial): void {
  const mesh = new Mesh(new CylinderGeometry(radius,radius,length,12),material);
  mesh.rotation.x = Math.PI / 2; mesh.position.set(...at); mesh.castShadow = true;
  group.add(mesh);
}

/** Merge only our static mesh group: one draw per material, not per bolt/plate. */
function consolidate(group: Group): void {
  const batches = new Map<MeshStandardMaterial, Mesh[]>();
  for (const child of [...group.children] as Mesh[]) {
    const material = child.material as MeshStandardMaterial;
    const batch = batches.get(material) ?? []; batch.push(child); batches.set(material,batch);
  }
  for (const [material, meshes] of batches) {
    const geometries = meshes.map((mesh) => { mesh.updateMatrix(); return mesh.geometry.clone().applyMatrix4(mesh.matrix); });
    const combined = mergeGeometries(geometries);
    if (!combined) throw new Error("Equipment geometry could not be merged");
    for (const geometry of geometries) geometry.dispose();
    for (const mesh of meshes) { group.remove(mesh); mesh.geometry.dispose(); }
    const mesh = new Mesh(combined,material); mesh.castShadow = true; mesh.receiveShadow = true;
    group.add(mesh);
  }
}

export function equipmentFrame(station: EquipmentStation, materials: Materials): Group {
  const frame = new Group();
  const accent = station.kind === "bench_press" ? materials.bench : materials.curl;
  box(frame,[2.65,.035,2.65],[0,.005,0],materials.rubber);
  box(frame,[2.45,.008,.035],[0,.027,1.2],accent);
  if (station.kind === "bench_press") {
    box(frame,[1.85,.2,.78],[-.22,.30,0],materials.bench);
    box(frame,[1.4,.10,.12],[-.22,.15,0],materials.iron);
    for (const x of [-.85,.40]) box(frame,[.12,.25,.64],[x,.13,0],materials.steel);
    const top = .90 + station.travel + .15;
    for (const z of [-1.15,1.15]) {
      box(frame,[.10,top,.10],[.32,top/2,z],materials.steel);
      box(frame,[.85,.07,.22],[.28,.045,z],materials.iron);
      box(frame,[.32,.055,.14],[.27,.86,z],materials.iron);
    }
    box(frame,[.10,.10,2.4],[.32,top,0],materials.iron);
  } else {
    // Side stands support the lower stop; no invisible wall or steering collider.
    for (const z of [-.5,.5]) {
      box(frame,[.12,.47,.12],[.45,.255,z],materials.steel);
      box(frame,[.4,.07,.42],[.45,.49,z],materials.iron);
      box(frame,[.5,.05,.4],[.45,.045,z],materials.iron);
    }
  }
  consolidate(frame);
  return frame;
}

export function equipmentWeight(station: EquipmentStation, materials: Materials): Group {
  const weights = new Group();
  if (station.kind === "bench_press") {
    cylinder(weights,.035,2.55,[0,0,0],materials.steel);
    for (const side of [-1,1]) {
      cylinder(weights,.047,.20,[0,0,.55*side],materials.iron);
      cylinder(weights,.27,.09,[0,0,.93*side],materials.iron);
      cylinder(weights,.23,.075,[0,0,1.035*side],materials.bench);
      cylinder(weights,.075,.08,[0,0,1.16*side],materials.steel);
    }
  } else {
    for (const side of [-1,1]) {
      cylinder(weights,.04,.52,[0,0,.50*side],materials.steel);
      for (const offset of [-.20,.20]) {
        cylinder(weights,.17,.09,[0,0,.50*side+offset],materials.iron);
        cylinder(weights,.13,.095,[0,0,.50*side+offset],materials.curl);
      }
    }
  }
  consolidate(weights);
  return weights;
}
