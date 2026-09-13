import type {
  ActiveNeuron,
  ErrorMessage,
  FrameMessage,
  HelloMessage,
  RunningMessage,
  ServerMessage,
} from "./types";

type UnknownRecord = Record<string, unknown>;

export function parseServerMessage(value: unknown): ServerMessage {
  const message = asRecord(value, "message");
  const type = asString(field(message, "type"), "type");
  if (type === "hello") return parseHello(message);
  if (type === "frame") return parseFrame(message);
  if (type === "running") return parseRunning(message);
  if (type === "error") return parseError(message);
  throw new Error("Unknown server message type");
}

export function formatBodyId(bodyId: number): string {
  return Math.trunc(bodyId).toString(10);
}

export function formatReading(value: number): string {
  if (value !== 0 && Math.abs(value) < 0.001) return value.toExponential(2);
  return value.toFixed(3);
}

function parseHello(message: UnknownRecord): HelloMessage {
  exactKeys(message, ["type", "schema", "backend", "dataset", "fps", "world"]);
  const schema = asNumber(field(message, "schema"), "schema");
  if (schema !== 1) throw new Error("Incompatible telemetry schema");
  const backend = asString(field(message, "backend"), "backend");
  if (backend !== "compact" && backend !== "full") throw new Error("Invalid backend");
  const world = asRecord(field(message, "world"), "world");
  exactKeys(world, ["width", "height"]);
  return {
    type: "hello",
    schema: 1,
    backend,
    dataset: asString(field(message, "dataset"), "dataset"),
    fps: asNumber(field(message, "fps"), "fps"),
    world: {
      width: asNumber(field(world, "width"), "world.width"),
      height: asNumber(field(world, "height"), "world.height"),
    },
  };
}

function parseFrame(message: UnknownRecord): FrameMessage {
  exactKeys(message, [
    "type", "schema", "step", "elapsed", "body", "food", "hunger", "ate",
    "sensory", "motor", "neural", "trail", "learning",
  ]);
  const schema = asNumber(field(message, "schema"), "schema");
  if (schema !== 1) throw new Error("Incompatible telemetry schema");
  return {
    type: "frame",
    schema: 1,
    step: asInteger(field(message, "step"), "step"),
    elapsed: asNumber(field(message, "elapsed"), "elapsed"),
    body: parseNumbers(field(message, "body"), ["x", "y", "heading"], "body"),
    food: parseFood(field(message, "food")),
    hunger: asNumber(field(message, "hunger"), "hunger"),
    ate: asBoolean(field(message, "ate"), "ate"),
    sensory: parseNumbers(
      field(message, "sensory"),
      ["smell_left", "smell_right", "vision_left", "vision_right"],
      "sensory",
    ),
    motor: parseNumbers(field(message, "motor"), ["forward", "turn"], "motor"),
    neural: parseNeural(field(message, "neural")),
    trail: parseTrail(field(message, "trail")),
    learning: parseLearning(field(message, "learning")),
  };
}

function parseFood(value: unknown): FrameMessage["food"] {
  if (value === null) return null;
  return parseNumbers(value, ["x", "y", "radius"], "food");
}

function parseNeural(value: unknown): FrameMessage["neural"] {
  const neural = asRecord(value, "neural");
  exactKeys(neural, ["roles", "active"]);
  const rolesRecord = asRecord(field(neural, "roles"), "neural.roles");
  const roles: Record<string, number> = {};
  for (const [role, activity] of Object.entries(rolesRecord)) {
    roles[role] = asNumber(activity, `neural.roles.${role}`);
  }
  const activeValue = field(neural, "active");
  if (!Array.isArray(activeValue) || activeValue.length > 128) {
    throw new Error("Invalid active neuron collection");
  }
  return { roles, active: activeValue.map(parseActiveNeuron) };
}

function parseActiveNeuron(value: unknown): ActiveNeuron {
  const neuron = asRecord(value, "active neuron");
  exactKeys(neuron, ["body_id", "label", "activity"]);
  return {
    body_id: asInteger(field(neuron, "body_id"), "body_id"),
    label: asString(field(neuron, "label"), "label"),
    activity: asNumber(field(neuron, "activity"), "activity"),
  };
}

function parseTrail(value: unknown): [number, number][] {
  if (!Array.isArray(value) || value.length > 80) throw new Error("Invalid trail");
  return value.map((point) => {
    if (!Array.isArray(point) || point.length !== 2) throw new Error("Invalid trail point");
    return [asNumber(point[0], "trail.x"), asNumber(point[1], "trail.y")];
  });
}

function parseLearning(value: unknown): FrameMessage["learning"] {
  const learning = asRecord(value, "learning");
  exactKeys(learning, [
    "reward", "association_strength", "mean_eligibility", "active_kcs", "changed",
  ]);
  return {
    reward: asNumber(field(learning, "reward"), "learning.reward"),
    association_strength: asNumber(
      field(learning, "association_strength"),
      "learning.association_strength",
    ),
    mean_eligibility: asNumber(
      field(learning, "mean_eligibility"),
      "learning.mean_eligibility",
    ),
    active_kcs: asInteger(field(learning, "active_kcs"), "learning.active_kcs"),
    changed: asBoolean(field(learning, "changed"), "learning.changed"),
  };
}

function parseRunning(message: UnknownRecord): RunningMessage {
  exactKeys(message, ["type", "running"]);
  return { type: "running", running: asBoolean(field(message, "running"), "running") };
}

function parseError(message: UnknownRecord): ErrorMessage {
  exactKeys(message, ["type", "code", "message"]);
  return {
    type: "error",
    code: asString(field(message, "code"), "code"),
    message: asString(field(message, "message"), "message"),
  };
}

function parseNumbers<K extends string>(
  value: unknown,
  keys: readonly K[],
  label: string,
): Record<K, number> {
  const record = asRecord(value, label);
  exactKeys(record, keys);
  return Object.fromEntries(
    keys.map((key) => [key, asNumber(field(record, key), `${label}.${key}`)]),
  ) as Record<K, number>;
}

function asRecord(value: unknown, label: string): UnknownRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value as UnknownRecord;
}

function field(record: UnknownRecord, key: string): unknown {
  if (!Object.hasOwn(record, key)) throw new Error(`Missing ${key}`);
  return record[key];
}

function exactKeys(record: UnknownRecord, expected: readonly string[]): void {
  const actual = Object.keys(record).sort();
  const required = [...expected].sort();
  if (actual.length !== required.length || actual.some((key, index) => key !== required[index])) {
    throw new Error("Message fields do not match the schema");
  }
}

function asNumber(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`${label} must be finite`);
  }
  return value;
}

function asInteger(value: unknown, label: string): number {
  const number = asNumber(value, label);
  if (!Number.isSafeInteger(number)) throw new Error(`${label} must be an integer`);
  return number;
}

function asString(value: unknown, label: string): string {
  if (typeof value !== "string") throw new Error(`${label} must be text`);
  return value;
}

function asBoolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") throw new Error(`${label} must be boolean`);
  return value;
}
