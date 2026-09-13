import { AnimationMixer, Box3, Group, LoopOnce, Mesh, Quaternion, Vector3, type AnimationAction } from "three/webgpu";
import type { GLTF } from "three/addons/loaders/GLTFLoader.js";
import { clone } from "three/addons/utils/SkeletonUtils.js";
import { ForelegPose } from "./foreleg-pose";
import type { ExerciseSnapshot } from "./gym-types";

export interface FlyEyePose { position: Vector3; target: Vector3; up: Vector3 }

/** Visual authoring scale, not a measured biomechanical body size. */
export function prepareFlyAsset(gltf: GLTF): GLTF {
  const bounds = new Box3().setFromObject(gltf.scene);
  const size = bounds.getSize(new Vector3());
  if (!Number.isFinite(size.length()) || size.z <= 0) throw new Error("Invalid rigged fly bounds");
  for (const name of ["Walk", "Feed"]) {
    if (!gltf.animations.some((clip) => clip.name === name)) throw new Error(`Missing ${name} animation`);
  }
  gltf.scene.traverse((node) => {
    if (node instanceof Mesh) { node.castShadow = !node.name.startsWith("Wing"); node.receiveShadow = true; }
  });
  return gltf;
}

/** Independent skeleton and mixer, shared immutable geometry/materials. */
export class AnimatedFly {
  readonly group = new Group();
  private readonly rig: Group;
  private readonly stance = new Group();
  private readonly forelegs: ForelegPose;
  private readonly mixer: AnimationMixer;
  private readonly actions = new Map<string, AnimationAction>();
  private active: AnimationAction | null = null;
  private lastDistance = 0;
  private exercising = false;
  private readonly eye: FlyEyePose = {position:new Vector3(),target:new Vector3(),up:new Vector3()};
  private readonly eyeOrientation = new Quaternion();

  constructor(asset: GLTF) {
    this.rig = clone(asset.scene) as Group;
    const wrapper = new Group();
    // Source is +Z forward and roughly 3 mm long; display head points +X.
    wrapper.rotation.y = Math.PI / 2;
    wrapper.scale.setScalar(2.2 / new Box3().setFromObject(this.rig).getSize(new Vector3()).z);
    wrapper.add(this.rig);
    this.stance.add(wrapper);
    this.group.add(this.stance);
    this.forelegs = new ForelegPose(this.rig);
    this.mixer = new AnimationMixer(this.rig);
    for (const clip of asset.animations) {
      const action = this.mixer.clipAction(clip);
      action.setLoop(LoopOnce, 1);
      action.clampWhenFinished = true;
      action.paused = true;
      this.actions.set(clip.name, action);
    }
    this.sample(0, false, 0);
  }

  /** An observer at the authored head; posture is not compound-eye vision. */
  get eyePose(): FlyEyePose {
    this.group.updateWorldMatrix(true,true);
    this.rig.getObjectByName("Head")!.getWorldPosition(this.eye.position);
    this.stance.getWorldQuaternion(this.eyeOrientation);
    this.eye.target.set(1,0,0).applyQuaternion(this.eyeOrientation).multiplyScalar(4).add(this.eye.position);
    this.eye.up.set(0,1,0).applyQuaternion(this.eyeOrientation);
    return this.eye;
  }

  /** Sample only simulation values; elapsed time cannot make a stationary fly walk. */
  sample(distance: number, eating: boolean, elapsed: number, exercise?: ExerciseSnapshot, grips?: readonly [Vector3, Vector3]): void {
    this.stance.position.y = exercise?.body_elevation ?? 0;
    this.stance.rotation.set(exercise?.body_roll ?? 0, 0, exercise?.body_pitch ?? 0, "ZYX");
    if (exercise?.station_id && grips) {
      this.active?.stop(); this.active = null;
      this.exercising = true;
      this.forelegs.restore();
      this.forelegs.reach(grips);
      this.group.userData.motion = exercise.kind;
      this.lastDistance = distance;
      return;
    }
    if (this.exercising) { this.forelegs.restore(); this.exercising = false; }
    const name = eating ? "Feed" : "Walk";
    const action = this.actions.get(name)!;
    if (this.active !== action) {
      this.active?.stop();
      action.reset().play();
      action.paused = true;
      this.active = action;
    }
    const phase = eating ? elapsed : distance / 0.8;
    action.time = phase % action.getClip().duration;
    this.mixer.update(0);
    this.group.userData.motion = eating ? "feeding" : distance > this.lastDistance ? "walking" : "idle";
    this.group.userData.distance = distance;
    this.lastDistance = distance;
  }

  dispose(): void {
    this.mixer.stopAllAction();
    this.mixer.uncacheRoot(this.rig);
    // Shared geometry and material disposal belongs to the owning scene.
    this.rig.traverse((node) => { if ("skeleton" in node) (node as import("three/webgpu").SkinnedMesh).skeleton.dispose(); });
  }
}
