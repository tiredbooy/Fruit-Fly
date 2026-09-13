import "./styles.css";

import { Dashboard } from "./dashboard";
import { FlyScene } from "./fly-scene";
import { SimulationClient } from "./simulation-client";

const sceneContainer = document.getElementById("scene");
if (!sceneContainer) throw new Error("Missing Three.js scene container");

let client: SimulationClient;
const dashboard = new Dashboard(document, (running) => client.setRunning(running));
let scene: FlyScene | null = null;

try {
  scene = new FlyScene(sceneContainer);
} catch {
  dashboard.showWebGlError();
}

client = new SimulationClient({
  onConnection: (state) => dashboard.setConnection(state),
  onHello: (message) => {
    dashboard.updateHello(message);
    scene?.configure(message);
  },
  onFrame: (message) => {
    dashboard.updateFrame(message);
    scene?.update(message);
  },
  onRunning: (running) => {
    dashboard.setRunning(running);
    scene?.setRunning(running);
  },
  onError: () => dashboard.showCommandError(),
});

window.addEventListener("resize", () => scene?.resize());
document.addEventListener("visibilitychange", () => scene?.setVisible(!document.hidden));
window.addEventListener("beforeunload", () => client.disconnect());

client.connect();
