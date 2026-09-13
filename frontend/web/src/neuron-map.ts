import * as THREE from "three/webgpu";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { createGraphicsRenderer } from "./graphics-renderer";
import { observedSomata, parseAnatomy, type NeuronAnatomy } from "./neuron-anatomy";
import { filterNeuronReadings } from "./neuron-readings";
import { disposeScene } from "./scene-primitives";
import type { ActiveNeuron, FrameMessage } from "./types";

/** Anatomical soma cloud: a position is measured; brightness is received rate, not a spike. */
export class NeuronMap {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(40, 1, 0.01, 30);
  private readonly controls: OrbitControls;
  private readonly positions = new Map<number, readonly number[]>();
  private readonly overlay = new THREE.BufferGeometry();
  private readonly highlights: THREE.Points;
  private readonly resizeObserver: ResizeObserver;
  private readonly intersectionObserver: IntersectionObserver;
  private readonly raycaster = new THREE.Raycaster();
  private visible = true;
  private dirty = true;
  private disposed = false;
  private readings: readonly ActiveNeuron[] = [];
  private mapped: ReturnType<typeof observedSomata> = [];
  private readonly search = document.querySelector<HTMLInputElement>("#neuron-search")!;
  private readonly summary = document.querySelector<HTMLElement>("#anatomy-summary")!;
  private readonly selection = document.querySelector<HTMLElement>("#anatomy-selection")!;

  static async create(container: HTMLElement, onFailure: () => void): Promise<NeuronMap> {
    const response = await fetch("/assets/neuron-positions.json");
    if (!response.ok) throw new Error("Anatomy unavailable");
    const anatomy = parseAnatomy(await response.json());
    const { renderer, assertHealthy } = await createGraphicsRenderer(
      new URLSearchParams(location.search).get("renderer") === "webgl", onFailure,
    );
    let view: NeuronMap | null = null;
    try {
      renderer.shadowMap.enabled = false;
      view = new NeuronMap(container, renderer, anatomy);
      await renderer.compileAsync(view.scene, view.camera);
      assertHealthy();
      await renderer.setAnimationLoop(() => view?.render());
      assertHealthy();
      container.dataset.anatomy = "ready";
      return view;
    } catch (error) {
      if (view) await view.dispose(); else await renderer.dispose();
      throw error;
    }
  }

  private constructor(private readonly container: HTMLElement, private readonly renderer: THREE.WebGPURenderer, anatomy: NeuronAnatomy) {
    this.scene.background = new THREE.Color("#070b0f");
    const coordinates = new Float32Array(anatomy.points.length * 3);
    anatomy.points.forEach(([id, x, y, z], index) => {
      // Atlas Y is flipped for display; this does not assert an anatomical viewing direction.
      const position = [x, -y, z];
      coordinates.set(position, index * 3);
      this.positions.set(id, position);
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(coordinates, 3));
    this.scene.add(new THREE.Points(geometry, new THREE.PointsMaterial({ color: "#507074", size: 0.008, transparent: true, opacity: 0.36, depthWrite: false })));
    this.overlay.setAttribute("position", new THREE.BufferAttribute(new Float32Array(128 * 3), 3));
    this.overlay.setAttribute("color", new THREE.BufferAttribute(new Float32Array(128 * 3), 3));
    this.overlay.setDrawRange(0, 0);
    this.highlights = new THREE.Points(this.overlay, new THREE.PointsMaterial({ size: 0.065, vertexColors: true, transparent: true, depthTest: false, depthWrite: false }));
    // Opaque objects render before transparent ones. This overlay must follow the
    // dense transparent atlas cloud or those points hide the actual readings.
    this.highlights.renderOrder = 1;
    this.scene.add(this.highlights);
    this.camera.position.set(0, 0.25, 3.6);
    const canvas = renderer.domElement;
    canvas.tabIndex = 0;
    canvas.setAttribute("aria-label", "نقشه نورونی؛ چرخش با کشیدن، بزرگ‌نمایی با چرخ ماوس");
    canvas.setAttribute("aria-describedby", "anatomy-summary");
    this.container.prepend(canvas);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enablePan = false;
    this.controls.minDistance = 0.6;
    this.controls.maxDistance = 6;
    this.controls.addEventListener("change", this.markDirty);
    canvas.addEventListener("pointermove", this.pick);
    canvas.addEventListener("keydown", this.keydown);
    this.search.addEventListener("input", this.refresh);
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.intersectionObserver = new IntersectionObserver(([entry]) => { this.visible = entry?.isIntersecting ?? false; this.dirty = true; });
    this.intersectionObserver.observe(container);
    this.raycaster.params.Points = { threshold: 0.025 };
    this.resize();
    this.refresh();
  }

  update(frame: FrameMessage): void { this.readings = frame.neural.active; this.refresh(); }

  private readonly refresh = (): void => {
    this.mapped = observedSomata(this.positions, filterNeuronReadings(this.readings, this.search.value));
    const position = this.overlay.getAttribute("position") as THREE.BufferAttribute;
    const colors = this.overlay.getAttribute("color") as THREE.BufferAttribute;
    this.mapped.forEach(({ position: point, active, neuron }, index) => {
      position.setXYZ(index, point[0]!, point[1]!, point[2]!);
      const color = new THREE.Color(active ? "#e36da6" : "#f2b84b");
      color.multiplyScalar(active ? 0.55 + Math.min(1, Math.max(0, neuron.activity)) * 0.45 : 0.5);
      colors.setXYZ(index, color.r, color.g, color.b);
    });
    position.needsUpdate = true; colors.needsUpdate = true;
    this.overlay.setDrawRange(0, this.mapped.length);
    this.overlay.computeBoundingSphere();
    this.container.dataset.observed = String(this.mapped.length);
    this.container.dataset.positive = String(this.mapped.filter((point) => point.active).length);
    const missing = this.readings.filter((neuron) => !this.positions.has(neuron.body_id)).length;
    this.summary.textContent = `${this.positions.size.toLocaleString("fa-IR")} مکان اندازه‌گیری‌شده · ${missing.toLocaleString("fa-IR")} خوانش بدون مکان`;
    this.selection.textContent = "برای شناسه، روی نقطه روشن بروید.";
    this.dirty = true;
  };

  private readonly markDirty = (): void => { this.dirty = true; };
  private readonly keydown = (event: KeyboardEvent): void => {
    if (!["ArrowLeft", "ArrowRight", "+", "=", "-"].includes(event.key)) return;
    event.preventDefault();
    if (event.key.startsWith("Arrow")) this.camera.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), event.key === "ArrowLeft" ? 0.12 : -0.12);
    else this.camera.position.multiplyScalar(event.key === "-" ? 1.1 : 0.9).clampLength(0.6, 6);
    this.controls.update(); this.dirty = true;
  };
  private readonly pick = (event: PointerEvent): void => {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.raycaster.setFromCamera(new THREE.Vector2((event.clientX - rect.left) / rect.width * 2 - 1, 1 - (event.clientY - rect.top) / rect.height * 2), this.camera);
    const index = this.raycaster.intersectObject(this.highlights)[0]?.index;
    const hit = index === undefined ? undefined : this.mapped[index];
    if (hit) this.selection.textContent = `${hit.neuron.label} · ${hit.neuron.body_id} · ${hit.neuron.activity}`;
  };

  private resize(): void {
    const width = Math.max(1, this.container.clientWidth), height = Math.max(1, this.container.clientHeight);
    this.camera.aspect = width / height; this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false); this.dirty = true;
  }
  private render(): void {
    if (this.disposed || !this.visible || document.hidden) return;
    // Repaint visible canvases even while paused: WebGL's non-preserved drawing
    // buffer can be cleared after composition. Attribute updates remain tick-only.
    this.renderer.render(this.scene, this.camera); this.dirty = false;
  }
  async dispose(): Promise<void> {
    if (this.disposed) return;
    this.disposed = true;
    this.resizeObserver.disconnect(); this.intersectionObserver.disconnect();
    this.controls.dispose();
    this.search.removeEventListener("input", this.refresh);
    this.renderer.domElement.removeEventListener("pointermove", this.pick);
    this.renderer.domElement.removeEventListener("keydown", this.keydown);
    await this.renderer.setAnimationLoop(null);
    disposeScene(this.scene); this.renderer.domElement.remove();
    await this.renderer.dispose();
  }
}
