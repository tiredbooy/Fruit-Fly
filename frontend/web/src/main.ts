import "./styles.css";
import "./scene-controls.css";
import "./neuron-inspector.css";
import "./gym-observatory.css";

import { Dashboard } from "./dashboard";
import { GymDashboard } from "./gym-dashboard";
import type { NeuronMap } from "./neuron-map";
import type { GymFrame } from "./gym-types";
import type { FlyScene } from "./fly-scene";
import type { CameraMode } from "./scene-camera";
import { SimulationClient } from "./simulation-client";
import type { FrameMessage, HelloMessage } from "./types";

const sceneContainer = document.getElementById("scene");
if (!sceneContainer) throw new Error("Missing Three.js scene container");

let client: SimulationClient;
const dashboard = new Dashboard(document, (running) => client.setRunning(running));
const gym = new GymDashboard((count) => client.setPopulation(count), () => renderGym());
let scene: FlyScene | null = null;
let neuronMap: NeuronMap | null = null;
let latestHello: HelloMessage | null = null;
let latestFrame: FrameMessage | null = null;
let latestGym: GymFrame | null = null;
let running = true;
let closed = false;

client = new SimulationClient({
  onConnection: (state) => { dashboard.setConnection(state); gym.connection(state); },
  onHello: (message) => {
    latestHello = message;
    dashboard.updateHello(message);
    gym.configure(message);
    if (message.schema === 1) latestGym = null;
    scene?.configure(message);
  },
  onFrame: (message) => {
    latestFrame = message;
    dashboard.updateFrame(message);
    neuronMap?.update(message);
    scene?.update(message);
  },
  onGymFrame: (message) => { latestGym = message; renderGym(); },
  onPopulation: (count) => gym.acknowledge(count),
  onRunning: (value) => {
    running = value;
    dashboard.setRunning(value);
    scene?.setRunning(value);
  },
  onError: () => { dashboard.showCommandError(); gym.commandError(); },
});

document.addEventListener("visibilitychange", () => scene?.setVisible(!document.hidden));
window.addEventListener("beforeunload", () => {
  closed = true;
  client.disconnect();
  void scene?.dispose();
  void neuronMap?.dispose();
});
const cameraButtons: Record<CameraMode, HTMLButtonElement | null> = {
  overview: document.querySelector("#view-overview"),
  follow: document.querySelector("#view-fly"),
  eye: document.querySelector("#view-eye"),
};

for (const [mode, button] of Object.entries(cameraButtons)) {
  button?.addEventListener("click", () => selectCameraMode(mode as CameraMode));
}

client.connect();

// Stream instruments immediately; asset downloads and shader compilation are asynchronous.
async function initializeScene(): Promise<void> {
  let graphicsFailed = false;
  try {
    const { FlyScene } = await import("./fly-scene");
    scene = await FlyScene.create(sceneContainer!, () => {
      graphicsFailed = true;
      dashboard.showWebGlError();
    });
    if (closed) { await scene.dispose(); return; }
    if (latestHello) scene.configure(latestHello);
    if (latestGym) renderGym();
    else if (latestFrame) scene.update(latestFrame);
    scene.setRunning(running);
    scene.setVisible(!document.hidden);
    if (!graphicsFailed) dashboard.setSceneReady(scene.backend);
  } catch (error) {
    console.error("3D initialization failed", error);
    dashboard.showWebGlError();
  }
}

void initializeScene();
void initializeAnatomy();

function renderGym(): void {
  if (!latestGym) return;
  const selected = gym.update(latestGym);
  latestFrame = selected.frame;
  dashboard.updateFrame(selected.frame);
  neuronMap?.update(selected.frame);
  scene?.updateGym(latestGym, gym.selectedId);
}

async function initializeAnatomy(): Promise<void> {
  const container = document.querySelector<HTMLElement>("#neuron-map")!;
  const loading = document.querySelector<HTMLElement>("#anatomy-loading")!;
  let failed = false;
  const failure = () => {
    failed = true;
    container.dataset.anatomy = "failed";
    loading.hidden = false;
    loading.textContent = "نقشه بارگذاری نشد؛ خوانش‌های دقیق را باز کنید.";
  };
  try {
    const { NeuronMap } = await import("./neuron-map");
    neuronMap = await NeuronMap.create(container, failure);
    if (closed) { await neuronMap.dispose(); return; }
    if (latestFrame) neuronMap.update(latestFrame);
    if (!failed) loading.hidden = true;
  } catch (error) { console.error("Anatomical view failed", error); failure(); }
}

function selectCameraMode(mode: CameraMode): void {
  if (!scene) return;
  if (mode === "overview") scene.showOverview();
  if (mode === "follow") scene.focusFly();
  if (mode === "eye") scene.showEyeView();
  sceneContainer!.dataset.cameraMode = mode;
  sceneContainer!.setAttribute("aria-describedby", mode === "eye" ? "camera-approximation" : "camera-instructions");
  for (const [buttonMode, button] of Object.entries(cameraButtons)) {
    button?.setAttribute("aria-pressed", String(buttonMode === mode));
  }
}
