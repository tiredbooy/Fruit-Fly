import * as THREE from "three";

import {
  createChamber,
  createFly,
  createFood,
  createNeuralHalo,
  createOdorHalo,
  createTrail,
  MAX_NEURAL_PARTICLES,
} from "./scene-primitives";
import type { FrameMessage, HelloMessage } from "./types";

const CHAMBER_HEIGHT = 14;

export function worldToScene(
  x: number,
  y: number,
  worldWidth: number,
  worldHeight: number,
): { x: number; z: number } {
  return {
    x: (x / worldWidth) * 20,
    z: -(y / worldHeight) * 12,
  };
}

export function interpolateHeading(from: number, to: number, amount: number): number {
  let delta = ((to - from + Math.PI) % (Math.PI * 2)) - Math.PI;
  if (delta < -Math.PI) delta += Math.PI * 2;
  return from + delta * amount;
}

export function odorHaloScale(strength: number | null): number {
  if (strength === null || strength <= 0) return 0;
  return Math.min(2.4, 0.5 + strength);
}

export function neuralIntensity(activity: readonly number[]): number {
  if (!activity.length) return 0;
  const mean = activity.reduce((sum, value) => sum + value, 0) / activity.length;
  return Math.min(1, Math.max(0, mean));
}

export function cameraFocusX(
  targetX: number,
  visibleWidth: number,
  chamberWidth: number,
): number {
  if (visibleWidth >= chamberWidth) return 0;
  const travel = (chamberWidth - visibleWidth) / 2;
  return Math.min(travel, Math.max(-travel, targetX));
}

export class FlyScene {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.OrthographicCamera();
  private readonly renderer: THREE.WebGLRenderer;
  private readonly fly = createFly();
  private readonly food = createFood();
  private readonly odor = createOdorHalo();
  private readonly trail = createTrail();
  private readonly neural = createNeuralHalo();
  private readonly clock = new THREE.Clock();
  private readonly reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  private world = { width: 20, height: 12 };
  private targetPosition = new THREE.Vector3();
  private targetHeading = 0;
  private visible = true;
  private running = true;
  private animationFrame = 0;

  constructor(private readonly container: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.setAttribute("aria-hidden", "true");
    this.container.prepend(this.renderer.domElement);
    this.composeScene();
    this.resize();
    this.render();
  }

  configure(message: HelloMessage): void {
    this.world = message.world;
  }

  update(frame: FrameMessage): void {
    const body = worldToScene(frame.body.x, frame.body.y, this.world.width, this.world.height);
    this.targetPosition.set(body.x, 0.5, body.z);
    this.targetHeading = frame.body.heading;
    this.updateFood(frame);
    this.updateTrail(frame.trail);
    this.updateNeuralHalo(frame);
  }

  setRunning(running: boolean): void {
    this.running = running;
  }

  setVisible(visible: boolean): void {
    this.visible = visible;
    if (visible && !this.animationFrame) this.render();
  }

  resize(): void {
    const width = Math.max(1, this.container.clientWidth);
    const height = Math.max(1, this.container.clientHeight);
    const aspect = width / height;
    this.camera.left = (-CHAMBER_HEIGHT * aspect) / 2;
    this.camera.right = (CHAMBER_HEIGHT * aspect) / 2;
    this.camera.top = CHAMBER_HEIGHT / 2;
    this.camera.bottom = -CHAMBER_HEIGHT / 2;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  private composeScene(): void {
    this.scene.background = new THREE.Color("#070b0f");
    this.scene.fog = new THREE.Fog("#070b0f", 15, 32);
    this.camera.position.set(0, 16, 11);
    this.camera.lookAt(0, 0, 0);
    this.scene.add(new THREE.HemisphereLight("#9ce8e3", "#071016", 1.2));
    const key = new THREE.DirectionalLight("#d9ffff", 2.4);
    key.position.set(-6, 12, 4);
    key.castShadow = true;
    this.scene.add(key);
    this.scene.add(createChamber(), this.fly.group, this.food, this.odor, this.trail, this.neural.group);
  }

  private updateFood(frame: FrameMessage): void {
    this.food.visible = frame.food !== null;
    this.odor.visible = frame.food !== null;
    if (!frame.food) return;
    const point = worldToScene(frame.food.x, frame.food.y, this.world.width, this.world.height);
    this.food.position.set(point.x, 0.35, point.z);
    this.odor.position.set(point.x, 0.025, point.z);
    const sensory = Math.max(frame.sensory.smell_left, frame.sensory.smell_right);
    const scale = odorHaloScale(sensory);
    this.odor.scale.setScalar(scale);
  }

  private updateTrail(points: [number, number][]): void {
    const positions = this.trail.geometry.getAttribute("position") as THREE.BufferAttribute;
    const count = Math.min(points.length, 80);
    for (let index = 0; index < count; index += 1) {
      const point = points[points.length - count + index];
      if (!point) continue;
      const scenePoint = worldToScene(point[0], point[1], this.world.width, this.world.height);
      positions.setXYZ(index, scenePoint.x, 0.045, scenePoint.z);
    }
    positions.needsUpdate = true;
    this.trail.geometry.setDrawRange(0, count);
  }

  private updateNeuralHalo(frame: FrameMessage): void {
    const activity = frame.neural.active.slice(0, MAX_NEURAL_PARTICLES);
    const matrix = new THREE.Matrix4();
    for (let index = 0; index < MAX_NEURAL_PARTICLES; index += 1) {
      const value = activity[index]?.activity ?? 0;
      const base = this.neural.positions[index];
      if (!base) continue;
      matrix.compose(base, new THREE.Quaternion(), new THREE.Vector3().setScalar(value ? 0.35 + value : 0));
      this.neural.mesh.setMatrixAt(index, matrix);
    }
    this.neural.mesh.instanceMatrix.needsUpdate = true;
    this.neural.group.position.copy(this.targetPosition);
    this.neural.material.emissiveIntensity = 0.8 + neuralIntensity(activity.map((item) => item.activity)) * 2.2;
  }

  private render = (): void => {
    if (!this.visible) {
      this.animationFrame = 0;
      return;
    }
    const elapsed = this.clock.getElapsedTime();
    const amount = this.reducedMotion ? 1 : 0.14;
    this.fly.group.position.lerp(this.targetPosition, amount);
    this.fly.group.rotation.y = interpolateHeading(this.fly.group.rotation.y, this.targetHeading, amount);
    const cameraX = cameraFocusX(
      this.targetPosition.x,
      this.camera.right - this.camera.left,
      20,
    );
    this.camera.position.x = THREE.MathUtils.lerp(this.camera.position.x, cameraX, amount);
    this.camera.lookAt(this.camera.position.x, 0, 0);
    if (!this.reducedMotion && this.running) {
      const flutter = Math.sin(elapsed * 32) * 0.22;
      this.fly.leftWing.rotation.x = -0.28 + flutter;
      this.fly.rightWing.rotation.x = -0.28 - flutter;
      this.neural.group.rotation.y = elapsed * 0.22;
      this.odor.rotation.z = elapsed * 0.08;
    }
    this.renderer.render(this.scene, this.camera);
    this.animationFrame = window.requestAnimationFrame(this.render);
  };
}
