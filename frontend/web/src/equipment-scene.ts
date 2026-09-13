import { Group, Vector3 } from "three/webgpu";
import type { EquipmentStation } from "./gym-types";
import { equipmentFrame, equipmentMaterials, equipmentWeight } from "./equipment-meshes";
import { worldToScene } from "./scene-math";

interface Apparatus {
  station: EquipmentStation;
  root: Group;
  weight: Group;
  grips: [Vector3,Vector3];
}

/** Geometry and grip targets share one stroke; no autonomous animation clock. */
export class EquipmentScene {
  readonly group = new Group();
  private readonly apparatus = new Map<string,Apparatus>();

  constructor(stations: readonly EquipmentStation[], world: {width:number;height:number}) {
    const materials = equipmentMaterials();
    for (const station of stations) {
      const root = new Group(); root.name = station.id;
      const center = worldToScene(station.x,station.y,world.width,world.height);
      root.position.set(center.x,0,center.z); root.rotation.y = station.heading;
      const weight = equipmentWeight(station,materials); weight.name = `${station.id}-weight`;
      root.add(equipmentFrame(station,materials),weight); this.group.add(root);
      this.apparatus.set(station.id,{station,root,weight,grips:[new Vector3(),new Vector3()]});
      this.sample(station.id,0);
    }
  }

  sample(id: string, position: number): readonly [Vector3,Vector3] | undefined {
    const apparatus = this.apparatus.get(id);
    if (!apparatus) return;
    const {station,root,weight,grips} = apparatus;
    const q = Math.min(1,Math.max(0,position));
    const bench = station.kind === "bench_press";
    const x = bench ? .32 : .45 + .15*Math.sin(Math.PI*q) - .10*q;
    const height = (bench ? .90 : .62) + station.travel*q;
    weight.position.set(x,height,0);
    root.updateWorldMatrix(true,true);
    const side = bench ? -.55 : .50;
    grips[0].set(x,height,side); grips[1].set(x,height,-side);
    root.localToWorld(grips[0]); root.localToWorld(grips[1]);
    return grips;
  }

  resetUnoccupied(occupied: ReadonlySet<string>): void {
    for (const id of this.apparatus.keys()) if (!occupied.has(id)) this.sample(id,0);
  }
}
