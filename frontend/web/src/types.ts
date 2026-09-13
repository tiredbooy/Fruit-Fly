export interface HelloMessage {
  type: "hello";
  schema: 1;
  backend: "compact" | "full";
  dataset: string;
  fps: number;
  world: { width: number; height: number };
}

export interface ActiveNeuron {
  body_id: number;
  label: string;
  activity: number;
}

export interface FrameMessage {
  type: "frame";
  schema: 1;
  step: number;
  elapsed: number;
  body: { x: number; y: number; heading: number };
  food: { x: number; y: number; radius: number } | null;
  hunger: number;
  ate: boolean;
  sensory: {
    smell_left: number;
    smell_right: number;
    vision_left: number;
    vision_right: number;
  };
  motor: { forward: number; turn: number };
  neural: {
    roles: Record<string, number>;
    active: ActiveNeuron[];
  };
  trail: [number, number][];
  learning: {
    reward: number;
    association_strength: number;
    mean_eligibility: number;
    active_kcs: number;
    changed: boolean;
  };
}

export interface RunningMessage {
  type: "running";
  running: boolean;
}

export interface ErrorMessage {
  type: "error";
  code: string;
  message: string;
}

export type ServerMessage = HelloMessage | FrameMessage | RunningMessage | ErrorMessage;
export type ConnectionState = "connecting" | "open" | "reconnecting" | "incompatible";
