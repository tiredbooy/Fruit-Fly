import { PerspectiveCamera, Vector3 } from "three/webgpu";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { arenaCameraDistance, cameraDistanceFor, eyeCameraPose } from "./scene-math";
import type { FlyEyePose } from "./animated-fly";

export type CameraMode = "overview" | "follow" | "eye";

/** Camera navigation changes only the observer; it cannot steer the specimen. */
export class SceneCamera {
  readonly camera = new PerspectiveCamera(45, 1, 0.1, 180);
  readonly controls: OrbitControls;
  mode: CameraMode = "overview";
  private automaticOverview = true;
  private readonly offset = new Vector3(0.7, 0.85, 1).normalize();
  private readonly shift = new Vector3();

  constructor(private readonly canvas: HTMLCanvasElement, reducedMotion: boolean) {
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = !reducedMotion;
    this.controls.dampingFactor = 0.12;
    this.controls.minDistance = 2.5;
    this.controls.maxDistance = 85;
    this.controls.maxPolarAngle = Math.PI * 0.48;
    this.controls.addEventListener("start", () => { this.automaticOverview = false; });
    this.updateCanvasInteraction(true);
    this.controls.listenToKeyEvents(canvas);
    canvas.addEventListener("keydown", this.onKeyDown);
  }

  resize(aspect: number): void {
    this.camera.aspect = aspect;
    this.camera.updateProjectionMatrix();
    if (this.automaticOverview) this.overview();
  }

  overview(): void {
    this.mode = "overview";
    this.automaticOverview = true;
    this.restoreNavigation();
    this.controls.target.set(0, 0, 0);
    this.camera.position.copy(this.offset).multiplyScalar(arenaCameraDistance(this.camera.aspect));
    this.controls.update();
  }

  focusFly(position: Vector3): void {
    this.mode = "follow";
    this.automaticOverview = false;
    this.restoreNavigation();
    this.controls.target.copy(position).add(new Vector3(0, 0.6, 0));
    this.camera.position.copy(this.controls.target).addScaledVector(this.offset, cameraDistanceFor(1.65, this.camera.aspect));
    this.controls.update();
  }

  eyeView(position: Vector3, heading: number, eye?: FlyEyePose): void {
    this.mode = "eye";
    this.automaticOverview = false;
    this.controls.enabled = false;
    this.updateCanvasInteraction(false);
    this.camera.fov = 90;
    this.camera.near = 0.03;
    this.camera.updateProjectionMatrix();
    this.applyEyePose(position, heading, eye);
  }

  update(position: Vector3, heading: number, eye?: FlyEyePose): void {
    if (this.mode === "eye") {
      this.applyEyePose(position, heading, eye);
      return;
    }
    if (this.mode === "follow") {
      this.shift.copy(position).add(new Vector3(0, 0.6, 0)).sub(this.controls.target);
      this.camera.position.add(this.shift);
      this.controls.target.add(this.shift);
    }
    this.controls.update();
  }

  dispose(): void {
    this.canvas.removeEventListener("keydown", this.onKeyDown);
    this.controls.dispose();
  }

  private onKeyDown = (event: KeyboardEvent): void => {
    if (this.mode === "eye") return;
    if (!["+", "=", "-"].includes(event.key)) return;
    event.preventDefault();
    this.shift.copy(this.camera.position).sub(this.controls.target);
    const length = Math.min(85, Math.max(2.5, this.shift.length() * (event.key === "-" ? 1.15 : 0.87)));
    this.camera.position.copy(this.controls.target).add(this.shift.setLength(length));
    this.controls.update();
  };

  private restoreNavigation(): void {
    this.camera.up.set(0,1,0);
    this.controls.enabled = true;
    this.updateCanvasInteraction(true);
    this.camera.fov = 45;
    this.camera.near = 0.1;
    this.camera.updateProjectionMatrix();
  }

  private updateCanvasInteraction(enabled: boolean): void {
    this.canvas.tabIndex = enabled ? 0 : -1;
    this.canvas.setAttribute("aria-label", enabled
      ? "نمای سه‌بعدی؛ با کشیدن بچرخانید و با چرخ ماوس بزرگ‌نمایی کنید"
      : "نمای تقریبی چشم مگس؛ این دوربین قابل هدایت نیست.");
  }

  private applyEyePose(position: Vector3, heading: number, eye?: FlyEyePose): void {
    if (eye) {
      this.camera.position.copy(eye.position);
      this.camera.up.copy(eye.up);
      this.camera.lookAt(eye.target);
      return;
    }
    this.camera.up.set(0,1,0);
    const pose = eyeCameraPose(position.x, position.z, heading);
    this.camera.position.set(pose.position.x, pose.position.y, pose.position.z);
    this.camera.lookAt(pose.target.x, pose.target.y, pose.target.z);
  }
}
