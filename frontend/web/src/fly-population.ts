import { Group, Vector3 } from "three/webgpu";
import type { GLTF } from "three/addons/loaders/GLTFLoader.js";
import { AnimatedFly } from "./animated-fly";
import { interpolateHeading, worldToScene } from "./scene-math";
import type { FrameMessage } from "./types";
import type { ExerciseSnapshot } from "./gym-types";
import type { EquipmentScene } from "./equipment-scene";

interface VisualFly {
  model: AnimatedFly;
  target: Vector3;
  frame: FrameMessage;
  distance: number;
  shownDistance: number;
  shownElapsed: number;
  active: boolean;
  exercise?: ExerciseSnapshot;
  shownJoint: number;
}

/** At most ten visual rigs; a selected fly never changes another fly's animation. */
export class FlyPopulation {
  readonly group = new Group();
  private readonly actors = new Map<string, VisualFly>();
  selectedId = "fly-1";
  equipment: EquipmentScene | null = null;

  constructor(private readonly asset: GLTF) {}
  get selected(): Group | undefined { return this.actors.get(this.selectedId)?.model.group; }
  get selectedEye() {
    const actor = this.actors.get(this.selectedId);
    return actor?.exercise?.station_id ? actor.model.eyePose : undefined;
  }

  update(entries: { id: string; frame: FrameMessage; distance?: number; exercise?: ExerciseSnapshot }[], world: {width: number; height: number}): void {
    for (const actor of this.actors.values()) actor.active = false;
    for (const { id, frame, distance, exercise } of entries) {
      const point = worldToScene(frame.body.x, frame.body.y, world.width, world.height);
      let actor = this.actors.get(id);
      if (!actor) {
        const model = new AnimatedFly(this.asset);
        model.group.name = id;
        model.group.position.set(point.x, 0.015, point.z);
        model.group.rotation.y = frame.body.heading;
        actor = {model, target: model.group.position.clone(), frame, distance: distance ?? 0, shownDistance: distance ?? 0, shownElapsed: frame.elapsed, active: true, shownJoint:exercise?.joint_position ?? 0};
        this.actors.set(id, actor); this.group.add(model.group);
      } else if (distance === undefined && frame.step > actor.frame.step) {
        // Schema 1 lacks an odometer; accumulated received displacement is visual only.
        actor.distance += Math.hypot(frame.body.x - actor.frame.body.x, frame.body.y - actor.frame.body.y);
      }
      if (frame.step < actor.frame.step) actor.distance = 0;
      actor.distance = distance ?? actor.distance;
      if (actor.exercise?.station_id !== exercise?.station_id) actor.shownJoint = exercise?.joint_position ?? 0;
      actor.exercise = exercise ? {...exercise} : undefined;
      actor.frame = frame; actor.target.set(point.x, 0.015, point.z); actor.active = true;
    }
    if (!entries.some((entry) => entry.id === this.selectedId)) this.selectedId = entries[0]!.id;
  }

  render(amount: number, eye: boolean): void {
    const occupied = new Set<string>();
    for (const [id, actor] of this.actors) {
      actor.model.group.visible = actor.active && !(eye && id === this.selectedId);
      if (!actor.active) continue;
      actor.model.group.position.lerp(actor.target, amount);
      actor.model.group.rotation.y = interpolateHeading(actor.model.group.rotation.y, actor.frame.body.heading, amount);
      actor.shownDistance += (actor.distance - actor.shownDistance) * amount;
      actor.shownElapsed += (actor.frame.elapsed - actor.shownElapsed) * amount;
      const exercise = actor.exercise;
      let grips;
      if (exercise?.station_id) {
        occupied.add(exercise.station_id);
        actor.shownJoint += (exercise.joint_position - actor.shownJoint) * amount;
        grips = this.equipment?.sample(exercise.station_id, actor.shownJoint);
      }
      actor.model.sample(actor.shownDistance, actor.frame.ate, actor.shownElapsed, exercise, grips);
    }
    this.equipment?.resetUnoccupied(occupied);
  }
  dispose(): void { for (const actor of this.actors.values()) actor.model.dispose(); }
}
