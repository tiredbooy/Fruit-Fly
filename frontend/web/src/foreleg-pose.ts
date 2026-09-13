import { Object3D, Quaternion, Vector3 } from "three/webgpu";

interface LegChain { upper: Object3D; lower: Object3D; foot: Object3D }

/** Two-bone IK for the authored forelegs, not a biomechanical muscle model. */
export class ForelegPose {
  private readonly chains: LegChain[];
  private readonly rest: {bone: Object3D; rotation: Quaternion}[] = [];
  private readonly a = new Vector3();
  private readonly b = new Vector3();
  private readonly c = new Vector3();
  private readonly direction = new Vector3();
  private readonly bend = new Vector3();
  private readonly elbow = new Vector3();
  private readonly from = new Vector3();
  private readonly to = new Vector3();
  private readonly delta = new Quaternion();
  private readonly worldRotation = new Quaternion();
  private readonly parentRotation = new Quaternion();

  constructor(private readonly rig: Object3D) {
    this.chains = ["L", "R"].map((side) => {
      const upper = rig.getObjectByName(`Leg1Upper${side}`);
      const lower = rig.getObjectByName(`Leg1Lower${side}`);
      const foot = rig.getObjectByName(`Leg1Foot${side}`);
      if (!upper || !lower || !foot) throw new Error("Missing authored foreleg chain");
      return {upper, lower, foot};
    });
    rig.traverse((bone) => { if (bone.type === "Bone") this.rest.push({bone, rotation: bone.quaternion.clone()}); });
  }

  restore(): void { for (const {bone, rotation} of this.rest) bone.quaternion.copy(rotation); }

  reach(grips: readonly [Vector3, Vector3]): void {
    this.rig.updateWorldMatrix(true, true);
    this.chains.forEach((chain, index) => this.solve(chain, grips[index]!, index === 0 ? 1 : -1));
  }

  private solve({upper, lower, foot}: LegChain, target: Vector3, side: number): void {
    upper.getWorldPosition(this.a); lower.getWorldPosition(this.b); foot.getWorldPosition(this.c);
    const first = this.a.distanceTo(this.b), second = this.b.distanceTo(this.c);
    this.direction.subVectors(target, this.a);
    const distance = Math.max(Math.abs(first - second) + 1e-6, Math.min(first + second - 1e-6, this.direction.length()));
    this.direction.normalize();
    const along = (first * first - second * second + distance * distance) / (2 * distance);
    const outward = Math.sqrt(Math.max(0, first * first - along * along));
    // Keep the elbow bend on its existing side; this is stable through supination.
    this.bend.subVectors(this.b, this.a).addScaledVector(this.direction, -this.from.subVectors(this.b, this.a).dot(this.direction));
    if (this.bend.lengthSq() < 1e-10) this.bend.set(0, 0, side).addScaledVector(this.direction, -side * this.direction.z);
    this.bend.normalize();
    this.elbow.copy(this.a).addScaledVector(this.direction, along).addScaledVector(this.bend, outward);
    this.rotateToward(upper, this.b, this.elbow);
    lower.getWorldPosition(this.b); foot.getWorldPosition(this.c);
    this.rotateToward(lower, this.c, target);
  }

  private rotateToward(bone: Object3D, current: Vector3, target: Vector3): void {
    bone.getWorldPosition(this.a);
    this.from.subVectors(current, this.a).normalize();
    this.to.subVectors(target, this.a).normalize();
    this.delta.setFromUnitVectors(this.from, this.to);
    bone.getWorldQuaternion(this.worldRotation);
    bone.parent!.getWorldQuaternion(this.parentRotation).invert();
    bone.quaternion.copy(this.parentRotation.multiply(this.delta).multiply(this.worldRotation)).normalize();
    bone.updateWorldMatrix(false, true);
  }
}
