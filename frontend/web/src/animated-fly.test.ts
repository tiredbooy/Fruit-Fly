import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { SkinnedMesh, Vector3, Box3 } from "three/webgpu";
import { AnimatedFly, prepareFlyAsset } from "./animated-fly";
import type { ExerciseSnapshot } from "./gym-types";

async function asset() {
  const bytes = readFileSync(new URL("./assets/fly/walking-fly.glb", import.meta.url));
  return prepareFlyAsset(await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), ""));
}

test("real rig clones share geometry but never animated skeleton state", async () => {
  const source = await asset();
  const first = new AnimatedFly(source);
  const second = new AnimatedFly(source);
  let firstMesh!: SkinnedMesh; let secondMesh!: SkinnedMesh;
  first.group.traverse((node) => { if (node instanceof SkinnedMesh) firstMesh = node; });
  second.group.traverse((node) => { if (node instanceof SkinnedMesh) secondMesh = node; });
  expect(firstMesh.geometry).toBe(secondMesh.geometry);
  expect(firstMesh.skeleton).not.toBe(secondMesh.skeleton);
  const bone = first.group.getObjectByName("Leg1UpperL");
  expect(bone).toBeDefined();
  const before = second.group.getObjectByName("Leg1UpperL")!.quaternion.clone();
  first.sample(0.25, false, 1);
  expect(bone!.quaternion.equals(before)).toBe(false);
  expect(second.group.getObjectByName("Leg1UpperL")!.quaternion.equals(before)).toBe(true);
  first.dispose(); second.dispose();
});

test("walking phase depends on ground distance, not elapsed wall time", async () => {
  const fly = new AnimatedFly(await asset());
  fly.sample(0.25, false, 1);
  const bone = fly.group.getObjectByName("Leg1UpperL")!;
  const walking = bone.quaternion.clone();
  fly.sample(0.25, false, 99);
  expect(bone.quaternion.equals(walking)).toBe(true);
  fly.sample(0.6, false, 100);
  expect(bone.quaternion.equals(walking)).toBe(false);
  expect(fly.group.position.toArray()).toEqual([0, 0, 0]);
  const bounds = new Box3().setFromObject(fly.group);
  expect(bounds.getSize(new Vector3()).length()).toBeLessThan(5);
  fly.dispose();
});

test("bench and curl forelegs reach the measured handles without moving the physical root", async () => {
  const source = await asset();
  const other = new AnimatedFly(source);
  const untouched = other.group.getObjectByName("Leg1UpperL")!.quaternion.clone();
  for (const kind of ["bench_press", "bicep_curl"] as const) {
    const fly = new AnimatedFly(source);
    const bench = kind === "bench_press";
    const exercise: ExerciseSnapshot = {station_id:"station-1",kind,phase:"lifting",
      joint_position:0,joint_velocity:0,repetitions:0,completed_sets:0,rep_in_set:0,
      recovery_remaining:0,body_elevation:bench ? 1.5 : .5,body_pitch:bench ? 0 : .55,body_roll:bench ? Math.PI : 0};
    for (const position of [0, .5, 1]) {
      exercise.joint_position = position;
      const x = bench ? .32 : .45 + .15 * Math.sin(Math.PI * position) - .10 * position;
      const y = bench ? .90 + .70 * position : .62 + .55 * position;
      const z = bench ? -.55 : .50;
      const grips: [Vector3, Vector3] = [new Vector3(x,y,z),new Vector3(x,y,-z)];
      fly.sample(0,false,10,exercise,grips);
      const eye = fly.eyePose;
      const head = fly.group.getObjectByName("Head")!.getWorldPosition(new Vector3());
      expect(eye.position.distanceTo(head)).toBeLessThan(.1);
      expect(eye.position.y).toBeGreaterThan(bench ? .60 : 1.3);
      expect(eye.up.y).toBeCloseTo(bench ? -1 : Math.cos(.55), 6);
      expect(eye.target.y - eye.position.y).toBeCloseTo(bench ? 0 : 4 * Math.sin(.55), 6);
      for (const [index, name] of ["Leg1FootL", "Leg1FootR"].entries()) {
        expect(fly.group.getObjectByName(name)!.getWorldPosition(new Vector3()).distanceTo(grips[index]!)).toBeLessThan(.001);
      }
      const bone = fly.group.getObjectByName("Leg1UpperL")!.quaternion.clone();
      fly.sample(0,false,99,exercise,grips);
      expect(fly.group.getObjectByName("Leg1UpperL")!.quaternion.angleTo(bone)).toBeLessThan(.0001);
    }
    expect(fly.group.position.toArray()).toEqual([0,0,0]);
    expect(other.group.getObjectByName("Leg1UpperL")!.quaternion.equals(untouched)).toBe(true);
    fly.dispose();
  }
  other.dispose();
});
