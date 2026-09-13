import { NeuronInspector } from "./neuron-inspector";
import { formatReading } from "./snapshot";
import type { ConnectionState, FrameMessage, HelloMessage } from "./types";

const ROLE_LABELS: Record<string, string> = {
  forward_left: "DNp09 · L",
  forward_right: "DNp09 · R",
  steering_low_left: "DNa01 · L",
  steering_low_right: "DNa01 · R",
  steering_high_left: "DNa02 · L",
  steering_high_right: "DNa02 · R",
};

interface DashboardElements {
  connectionDot: HTMLElement;
  connectionLabel: HTMLElement;
  runningToggle: HTMLButtonElement;
  backend: HTMLElement;
  step: HTMLElement;
  elapsed: HTMLElement;
  foodState: HTMLElement;
  hungerValue: HTMLOutputElement;
  hungerMeter: HTMLMeterElement;
  smell: HTMLOutputElement;
  vision: HTMLOutputElement;
  forward: HTMLOutputElement;
  turn: HTMLOutputElement;
  reward: HTMLOutputElement;
  association: HTMLOutputElement;
  memoryState: HTMLElement;
  roles: HTMLElement;
  announcer: HTMLElement;
  sceneLoading: HTMLElement;
}

export class Dashboard {
  private readonly elements: DashboardElements;
  private readonly neuronInspector: NeuronInspector;
  private running = true;
  private readonly roleValues = new Map<string, HTMLElement>();

  constructor(documentRoot: Document, onRunningChange: (running: boolean) => void) {
    this.elements = elements(documentRoot);
    this.neuronInspector = new NeuronInspector(documentRoot);
    this.elements.runningToggle.addEventListener("click", () => {
      onRunningChange(!this.running);
    });
  }

  updateHello(message: HelloMessage): void {
    this.elements.backend.textContent =
      message.schema !== 1 ? "GYM · COMPACT" : message.backend === "full" ? "FULL · 166,606" : "COMPACT · 66 EDGES";
  }

  setSceneReady(backend: string): void {
    this.elements.sceneLoading.hidden = true;
    required(document, "graphics-backend").textContent = backend;
    document.querySelectorAll<HTMLButtonElement>(".scene-controls button").forEach((button) => { button.disabled = false; });
  }

  updateFrame(frame: FrameMessage): void {
    this.elements.step.textContent = frame.step.toString(10);
    this.elements.elapsed.textContent = frame.elapsed.toFixed(1);
    this.elements.foodState.textContent = frame.food ? "غذا در محیط" : "در انتظار غذا";
    this.elements.hungerValue.textContent = formatReading(frame.hunger);
    this.elements.hungerMeter.value = frame.hunger;
    this.elements.smell.textContent = pair(
      frame.sensory.smell_left,
      frame.sensory.smell_right,
    );
    this.elements.vision.textContent = pair(
      frame.sensory.vision_left,
      frame.sensory.vision_right,
    );
    this.elements.forward.textContent = formatReading(frame.motor.forward);
    this.elements.turn.textContent = signed(frame.motor.turn);
    this.elements.reward.textContent = formatReading(frame.learning.reward);
    this.elements.association.textContent = formatReading(
      frame.learning.association_strength,
    );
    this.elements.memoryState.textContent = frame.learning.changed ? "UPDATED" : "STABLE";
    this.updateRoles(frame.neural.roles);
    this.neuronInspector.update(frame);
  }

  setConnection(state: ConnectionState): void {
    const labels: Record<ConnectionState, string> = {
      connecting: "در حال اتصال",
      open: "زنده",
      reconnecting: "اتصال دوباره…",
      incompatible: "نسخه داده ناسازگار است",
    };
    this.elements.connectionLabel.textContent = labels[state];
    this.elements.connectionDot.dataset.state = state;
    this.elements.runningToggle.disabled = state !== "open";
    if (state === "incompatible") this.elements.announcer.textContent = labels[state];
  }

  setRunning(running: boolean): void {
    this.running = running;
    this.elements.runningToggle.textContent = running ? "توقف" : "ادامه";
    this.elements.runningToggle.setAttribute("aria-pressed", String(!running));
    document.body.dataset.running = String(running);
    this.elements.announcer.textContent = running ? "شبیه‌سازی ادامه یافت" : "شبیه‌سازی متوقف شد";
  }

  showWebGlError(): void {
    this.elements.sceneLoading.hidden = false;
    this.elements.sceneLoading.textContent = "نمای سه‌بعدی بارگذاری نشد؛ صفحه را تازه کنید.";
    required(document, "graphics-backend").textContent = "نمای سه‌بعدی قطع است";
    document.querySelectorAll<HTMLButtonElement>(".scene-controls button").forEach((button) => { button.disabled = true; });
  }

  showCommandError(): void {
    this.elements.announcer.textContent = "فرمان پذیرفته نشد؛ اتصال را دوباره برقرار کنید.";
  }

  private updateRoles(roles: Record<string, number>): void {
    for (const [role, label] of Object.entries(ROLE_LABELS)) {
      let value = this.roleValues.get(role);
      if (!value) {
        const term = this.elements.roles.ownerDocument.createElement("dt");
        term.textContent = label;
        value = this.elements.roles.ownerDocument.createElement("dd");
        value.dir = "ltr";
        this.elements.roles.append(term,value);
        this.roleValues.set(role,value);
      }
      const reading = formatReading(roles[role] ?? 0);
      if (value.textContent !== reading) value.textContent = reading;
    }
  }

}

function elements(root: Document): DashboardElements {
  return {
    connectionDot: required(root, "connection-dot"),
    connectionLabel: required(root, "connection-label"),
    runningToggle: required(root, "running-toggle") as HTMLButtonElement,
    backend: required(root, "backend-label"),
    step: required(root, "step-value"),
    elapsed: required(root, "elapsed-value"),
    foodState: required(root, "food-state"),
    hungerValue: required(root, "hunger-value") as HTMLOutputElement,
    hungerMeter: required(root, "hunger-meter") as HTMLMeterElement,
    smell: required(root, "smell-value") as HTMLOutputElement,
    vision: required(root, "vision-value") as HTMLOutputElement,
    forward: required(root, "forward-value") as HTMLOutputElement,
    turn: required(root, "turn-value") as HTMLOutputElement,
    reward: required(root, "reward-value") as HTMLOutputElement,
    association: required(root, "association-value") as HTMLOutputElement,
    memoryState: required(root, "memory-state"),
    roles: required(root, "role-list"),
    announcer: required(root, "announcer"),
    sceneLoading: required(root, "scene-loading"),
  };
}

function required(root: Document, id: string): HTMLElement {
  const element = root.getElementById(id);
  if (!element) throw new Error(`Missing interface element: ${id}`);
  return element;
}

function pair(left: number, right: number): string {
  return `${formatReading(left)} / ${formatReading(right)}`;
}

function signed(value: number): string {
  return `${value >= 0 ? "+" : ""}${formatReading(value)}`;
}
