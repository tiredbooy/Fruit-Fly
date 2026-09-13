import { expect, test } from "bun:test";
import { Group, Vector3 } from "three/webgpu";
import { EquipmentScene } from "./equipment-scene";
import type { EquipmentStation } from "./gym-types";
import { disposeScene } from "./scene-primitives";

test("weights and grips share the actual station stroke and world transform", () => {
  const stations: EquipmentStation[] = [
    {id:"station-1",kind:"bench_press",x:2,y:-1,heading:0,load:.6,travel:.7,grip_radius:.45},
    {id:"station-2",kind:"bicep_curl",x:-2,y:1,heading:Math.PI/2,load:.4,travel:.55,grip_radius:.45},
  ];
  const equipment = new EquipmentScene(stations, {width:20,height:12});
  const world = new Group(); world.add(equipment.group);
  const grips = equipment.sample("station-1", 0)!;
  expect(grips[0].distanceTo(new Vector3(2.32,.9,.45))).toBeLessThan(1e-8);
  const moving = equipment.group.getObjectByName("station-1-weight")!;
  const bottom = moving.getWorldPosition(new Vector3());
  equipment.sample("station-1", 1);
  expect(moving.getWorldPosition(new Vector3()).y - bottom.y).toBeCloseTo(.7, 8);
  const curls = equipment.sample("station-2", 1)!;
  expect(curls[0].y).toBeCloseTo(1.17, 8);
  expect(curls[0].x).toBeCloseTo(-1.5, 8);
  expect(curls[0].z).toBeCloseTo(-1.35, 8);
  expect(equipment.sample("station-9", 0)).toBeUndefined();
  disposeScene(equipment.group);
});
