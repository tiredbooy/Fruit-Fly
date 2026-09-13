import * as THREE from "three/webgpu";
import { createFood, createOdorHalo, createTrail, disposeScene } from "./scene-primitives";
import { createWorldScene, lightWorld } from "./world-scene";
import { loadFlyModel } from "./fly-model";
import { FlyPopulation } from "./fly-population";
import { createGymStation } from "./gym-scene";
import { EquipmentScene } from "./equipment-scene";
import { createGraphicsRenderer, graphicsBackend } from "./graphics-renderer";
import { SceneCamera } from "./scene-camera";
import { odorHaloScale, worldToScene } from "./scene-math";
import type { FrameMessage, HelloMessage } from "./types";
import type { GymFrame } from "./gym-types";
import type { GLTF } from "three/addons/loaders/GLTFLoader.js";

export class FlyScene {
  private readonly scene = new THREE.Scene();
  private readonly cameraRig: SceneCamera;
  private readonly population: FlyPopulation;
  private readonly food = createFood();
  private readonly odor = createOdorHalo();
  private readonly trail = createTrail();
  private readonly resizeObserver: ResizeObserver;
  private readonly motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  private world = { width: 20, height: 12 };
  private station: THREE.Group | null = null;
  private visible = !document.hidden;
  private running = true;
  private disposed = false;
  private lastTime = 0;

  static async create(container: HTMLElement, onFailure: () => void): Promise<FlyScene> {
    const { renderer, assertHealthy } = await createGraphicsRenderer(new URLSearchParams(location.search).get("renderer") === "webgl", onFailure);
    let scene: FlyScene | null = null;
    try {
      const asset = await loadFlyModel(); assertHealthy();
      scene = new FlyScene(container, renderer, asset);
      await renderer.compileAsync(scene.scene, scene.cameraRig.camera); assertHealthy();
      await renderer.setAnimationLoop((time) => scene?.render(time)); assertHealthy();
      container.dataset.renderer = graphicsBackend(renderer);
      container.dataset.model = "authored-rig";
      return scene;
    } catch (error) {
      if (scene) await scene.dispose(); else await renderer.dispose();
      throw error;
    }
  }

  private constructor(private readonly container: HTMLElement, private readonly renderer: THREE.WebGPURenderer, asset: GLTF) {
    this.cameraRig = new SceneCamera(renderer.domElement, this.motionPreference.matches);
    this.population = new FlyPopulation(asset);
    this.container.prepend(renderer.domElement);
    lightWorld(this.scene);
    this.scene.add(createWorldScene(), this.population.group, this.food, this.odor, this.trail);
    this.food.visible = false; this.odor.visible = false;
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container); this.resize();
  }

  get backend(): string { return graphicsBackend(this.renderer); }

  configure(message: HelloMessage): void {
    this.world = message.world;
    if (this.station) { this.scene.remove(this.station); disposeScene(this.station); this.station = null; }
    this.population.equipment = null;
    if (message.schema === 3) {
      const equipment = new EquipmentScene(message.equipment!,this.world);
      this.population.equipment = equipment; this.station = equipment.group;
      this.scene.add(this.station);
    } else if (message.schema === 2) {
      this.station = createGymStation(message.station, this.world); this.scene.add(this.station);
    }
  }

  update(frame: FrameMessage): void {
    this.population.update([{id: "fly-1", frame}], this.world);
    this.updateSelected(frame);
  }
  updateGym(message: GymFrame, selectedId: string): void {
    this.population.selectedId = selectedId;
    this.population.update(message.flies.map((fly) => ({...fly, distance: fly.training.distance})), this.world);
    this.updateSelected(message.flies.find((fly) => fly.id === this.population.selectedId)!.frame);
    this.container.dataset.population = String(message.flies.length);
    this.container.dataset.selectedFly = this.population.selectedId;
  }

  setRunning(running: boolean): void { this.running = running; }
  setVisible(visible: boolean): void { this.visible = visible; this.lastTime = 0; }
  showOverview(): void { this.cameraRig.overview(); this.population.render(1, false); }
  focusFly(): void { if (this.population.selected) this.cameraRig.focusFly(this.population.selected.position); this.population.render(1, false); }
  showEyeView(): void {
    const fly = this.population.selected;
    if (fly) this.cameraRig.eyeView(fly.position, fly.rotation.y, this.population.selectedEye);
    this.population.render(1, true);
  }
  resize(): void {
    const width = Math.max(1, this.container.clientWidth), height = Math.max(1, this.container.clientHeight);
    this.cameraRig.resize(width / height); this.renderer.setSize(width, height, false);
  }
  async dispose(): Promise<void> {
    if (this.disposed) return;
    this.disposed = true; this.resizeObserver.disconnect(); this.cameraRig.dispose();
    await this.renderer.setAnimationLoop(null);
    this.population.dispose(); disposeScene(this.scene);
    this.renderer.domElement.remove(); await this.renderer.dispose();
  }

  private updateSelected(frame: FrameMessage): void {
    this.food.visible = frame.food !== null; this.odor.visible = frame.food !== null;
    if (frame.food) {
      const point = worldToScene(frame.food.x, frame.food.y, this.world.width, this.world.height);
      const ground = Math.abs(point.x) <= 10 && Math.abs(point.z) <= 6 ? 0 : -1.3;
      this.food.position.set(point.x, ground, point.z); this.food.scale.setScalar(frame.food.radius);
      this.odor.position.set(point.x, ground + 0.02, point.z);
      this.odor.scale.setScalar(odorHaloScale(Math.max(frame.sensory.smell_left, frame.sensory.smell_right)));
    }
    const positions = this.trail.geometry.getAttribute("position") as THREE.BufferAttribute;
    frame.trail.forEach(([x, y], index) => { const point = worldToScene(x, y, this.world.width, this.world.height); positions.setXYZ(index, point.x, 0.032, point.z); });
    positions.needsUpdate = true; this.trail.geometry.setDrawRange(0, frame.trail.length);
  }

  private render(time: number): void {
    if (this.disposed || !this.visible) return;
    const dt = this.lastTime ? Math.min((time - this.lastTime) / 1000, 0.1) : 0;
    this.lastTime = time;
    this.population.render(this.motionPreference.matches || !this.running ? 1 : 1 - Math.exp(-14 * dt), this.cameraRig.mode === "eye");
    const fly = this.population.selected;
    if (fly) this.cameraRig.update(fly.position, fly.rotation.y, this.cameraRig.mode === "eye" ? this.population.selectedEye : undefined);
    this.renderer.render(this.scene, this.cameraRig.camera);
  }
}
