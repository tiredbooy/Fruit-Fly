import { parseServerMessage } from "./snapshot";
import type { ConnectionState, FrameMessage, HelloMessage, ServerMessage } from "./types";
import type { GymFrame } from "./gym-types";

interface SimulationClientEvents {
  onConnection(state: ConnectionState): void;
  onHello(message: HelloMessage): void;
  onFrame(message: FrameMessage): void;
  onRunning(running: boolean): void;
  onError(code: string): void;
  onGymFrame?(message: GymFrame): void;
  onPopulation?(count: number): void;
}

export class SimulationClient {
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private reconnectAttempt = 0;
  private stopped = false;

  constructor(private readonly events: SimulationClientEvents) {}

  connect(): void {
    this.stopped = false;
    this.events.onConnection(this.reconnectAttempt ? "reconnecting" : "connecting");
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    this.socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    this.socket.addEventListener("open", () => this.handleOpen());
    this.socket.addEventListener("message", (event) => this.handleMessage(event.data));
    this.socket.addEventListener("close", () => this.handleClose());
    this.socket.addEventListener("error", () => this.socket?.close());
  }

  setRunning(running: boolean): void {
    if (this.socket?.readyState !== WebSocket.OPEN) return;
    this.socket.send(JSON.stringify({ type: "set_running", running }));
  }

  setPopulation(count: number): void {
    if (this.socket?.readyState !== WebSocket.OPEN) return;
    this.socket.send(JSON.stringify({type: "set_population", count}));
  }

  disconnect(): void {
    this.stopped = true;
    if (this.reconnectTimer !== null) window.clearTimeout(this.reconnectTimer);
    this.socket?.close();
    this.socket = null;
  }

  private handleOpen(): void {
    this.reconnectAttempt = 0;
    this.events.onConnection("open");
  }

  private handleMessage(raw: unknown): void {
    try {
      if (typeof raw !== "string") throw new Error("Non-text WebSocket message");
      this.dispatch(parseServerMessage(JSON.parse(raw)));
    } catch {
      this.stopped = true;
      this.events.onConnection("incompatible");
      this.socket?.close();
    }
  }

  private dispatch(message: ServerMessage): void {
    if (message.type === "hello") this.events.onHello(message);
    if (message.type === "frame") this.events.onFrame(message);
    if (message.type === "gym_frame") this.events.onGymFrame?.(message);
    if (message.type === "population") this.events.onPopulation?.(message.count);
    if (message.type === "running") this.events.onRunning(message.running);
    if (message.type === "error") this.events.onError(message.code);
  }

  private handleClose(): void {
    this.socket = null;
    if (this.stopped) return;
    this.reconnectAttempt += 1;
    this.events.onConnection("reconnecting");
    const delay = Math.min(8_000, 500 * 2 ** (this.reconnectAttempt - 1));
    this.reconnectTimer = window.setTimeout(() => this.connect(), delay);
  }
}
