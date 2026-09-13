import type { GymFrame, GymFly } from "./gym-types";
import type { HelloMessage, ConnectionState } from "./types";
import { TrainingHistory } from "./training-history";
import { formatReading } from "./snapshot";

/** Explicit population setup is the only gym command; fly selection is observer-only. */
export class GymDashboard {
  selectedId = "fly-1";
  private readonly form = document.querySelector<HTMLFormElement>("#population-form")!;
  private readonly count = document.querySelector<HTMLInputElement>("#fly-count")!;
  private readonly apply = document.querySelector<HTMLButtonElement>("#apply-population")!;
  private readonly status = document.querySelector<HTMLElement>("#population-status")!;
  private readonly picker = document.querySelector<HTMLElement>("#fly-picker")!;
  private readonly panel = document.querySelector<HTMLElement>("#training-instrument")!;
  private readonly history = new TrainingHistory();
  private connected = false;
  private enabled = false;
  private pending = false;
  private ids = "";

  constructor(onCount: (count: number) => void, private readonly onSelect: (id: string) => void) {
    this.count.addEventListener("invalid", () => {
      const message = this.count.validity.valueMissing
        ? "تعداد مگس را وارد کنید."
        : "عدد صحیح بین ۱ تا ۱۰ وارد کنید.";
      this.count.setCustomValidity(message);
      this.status.textContent = message;
    });
    this.count.addEventListener("input", () => {
      this.count.setCustomValidity("");
      this.status.textContent = "";
    });
    this.form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!this.form.reportValidity() || !this.connected || this.pending) return;
      this.pending = true; this.apply.disabled = true;
      this.status.textContent = "در حال اعمال…";
      onCount(this.count.valueAsNumber);
    });
  }
  configure(hello: HelloMessage): void {
    this.enabled = hello.schema !== 1;
    this.form.hidden = !this.enabled; this.picker.hidden = !this.enabled; this.panel.hidden = !this.enabled;
    document.querySelector("#chamber-title")!.textContent = this.enabled ? "باشگاه مگس" : "محفظه زنده";
    if (hello.schema !== 1) this.acknowledge(hello.population);
    this.syncDisabled();
  }
  connection(state: ConnectionState): void {
    this.connected = state === "open";
    if (!this.connected) { this.pending = false; this.status.textContent = "برای تغییر تعداد، منتظر اتصال بمانید."; }
    this.syncDisabled();
  }
  acknowledge(count: number): void {
    this.pending = false; this.count.value = String(count);
    this.count.setCustomValidity("");
    this.status.textContent = `${count.toLocaleString("fa-IR")} مگس در محیط`;
    this.syncDisabled();
  }
  commandError(): void {
    this.pending = false; this.syncDisabled();
    this.status.textContent = "تعداد ۱ تا ۱۰ را دوباره وارد کنید.";
  }
  update(message: GymFrame): GymFly {
    for (const fly of message.flies) this.history.record(fly.id, message.elapsed, fly.training.association_strength, fly.training.fatigue);
    if (!message.flies.some((fly) => fly.id === this.selectedId)) this.selectedId = message.flies[0]!.id;
    const ids = message.flies.map((fly) => fly.id).join(",");
    if (ids !== this.ids) {
      this.ids = ids;
      this.picker.replaceChildren(...message.flies.map((fly) => this.flyButton(fly.id)));
    }
    this.picker.querySelectorAll<HTMLButtonElement>("button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.fly === this.selectedId)));
    const selected = message.flies.find((fly) => fly.id === this.selectedId)!;
    this.renderTraining(selected);
    return selected;
  }
  private flyButton(id: string): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button"; button.dataset.fly = id;
    button.textContent = `مگس ${Number(id.slice(4)).toLocaleString("fa-IR")}`;
    button.addEventListener("click", () => { this.selectedId = id; this.onSelect(id); });
    return button;
  }
  private syncDisabled(): void {
    this.count.disabled = !this.enabled || !this.connected || this.pending;
    this.apply.disabled = !this.enabled || !this.connected || this.pending;
  }
  private renderTraining(fly: GymFly): void {
    const training = fly.training;
    const exercise = fly.exercise;
    const apparatus = document.querySelector<HTMLElement>("#exercise-readings")!;
    apparatus.hidden = !exercise;
    if (exercise) {
      const name = exercise.kind === "bench_press" ? "پرس سینه" : exercise.kind === "bicep_curl" ? "جلو بازو" : "حرکت آزاد";
      const phase = {free:"بدون اتصال",lifting:"بالا بردن",lowering:"پایین آوردن",recovery:"بازیابی"}[exercise.phase];
      document.querySelector("#exercise-name")!.textContent = name;
      document.querySelector("#exercise-phase")!.textContent = phase;
      document.querySelector("#exercise-reps")!.textContent = exercise.repetitions.toLocaleString("fa-IR");
      document.querySelector("#exercise-recovery")!.textContent = exercise.recovery_remaining > 0 ? `${exercise.recovery_remaining.toFixed(1)} s` : "—";
      this.panel.dataset.exercise = exercise.kind ?? exercise.phase;
      this.panel.dataset.repetitions = String(exercise.repetitions);
    }
    for (const key of ["sets", "effort", "fatigue", "fitness", "reward", "association_strength"] as const) {
      document.getElementById(`gym-${key}`)!.textContent = key === "sets" ? String(training[key]) : formatReading(training[key]);
    }
    (document.querySelector("#gym-progress") as HTMLMeterElement).value = training.set_progress;
    document.querySelector("#gym-progress-value")!.textContent = `${Math.round(training.set_progress * 100).toLocaleString("fa-IR")}%`;
    const samples = this.history.forFly(fly.id);
    const first = samples[0]?.time ?? 0, last = samples.at(-1)?.time ?? 0;
    for (const key of ["association", "fatigue"] as const) {
      const coordinates = samples.map((sample) => `${8 + (sample.time - first) / Math.max(1, last - first) * 224},${72 - sample[key] * 64}`).join(" ");
      document.querySelector(`#curve-${key}`)!.setAttribute("points", coordinates);
    }
    document.querySelector("#curve-range")!.textContent = samples.length < 2 ? "در انتظار نمونه بعدی" : `${first.toFixed(0)}–${last.toFixed(0)} s`;
    this.panel.dataset.fly = fly.id;
  }
}
