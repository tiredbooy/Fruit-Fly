import { describe, expect, test } from "bun:test";

import { formatBodyId, formatReading, parseServerMessage } from "./snapshot";
import type { FrameMessage } from "./types";

const frame: FrameMessage = {
  type: "frame",
  schema: 1,
  step: 9,
  elapsed: 0.9,
  body: { x: 1, y: -2, heading: 0.5 },
  food: null,
  hunger: 0.42,
  ate: false,
  sensory: {
    smell_left: 0.1,
    smell_right: 0.2,
    vision_left: 0.3,
    vision_right: 0.4,
  },
  motor: { forward: 0.5, turn: -0.1 },
  neural: {
    roles: { forward_left: 0.25 },
    active: [{ body_id: 416090, label: "ORN_DM1#416090", activity: 0.8 }],
  },
  trail: [[0, 0], [1, -2]],
  learning: {
    reward: 0,
    association_strength: 0.12,
    mean_eligibility: 0.2,
    active_kcs: 4,
    changed: false,
  },
};

describe("parseServerMessage", () => {
  test("accepts a complete finite frame", () => {
    expect(parseServerMessage(frame)).toEqual(frame);
  });

  test("accepts hello and running state messages", () => {
    expect(
      parseServerMessage({
        type: "hello",
        schema: 1,
        backend: "full",
        dataset: "male-cns:v1.0",
        fps: 10,
        world: { width: 20, height: 12 },
      }).type,
    ).toBe("hello");
    expect(parseServerMessage({ type: "running", running: false })).toEqual({
      type: "running",
      running: false,
    });
  });

  test("rejects incompatible, missing, and non-finite values", () => {
    expect(() => parseServerMessage({ ...frame, schema: 2 })).toThrow("schema");
    expect(() => parseServerMessage({ ...frame, body: { x: 1, y: 2 } })).toThrow();
    expect(() =>
      parseServerMessage({ ...frame, hunger: Number.POSITIVE_INFINITY }),
    ).toThrow("finite");
    expect(() => parseServerMessage({ type: "frame" })).toThrow();
  });
});

describe("display formatting", () => {
  test("formats official IDs without locale digit substitution", () => {
    expect(formatBodyId(416090)).toBe("416090");
  });

  test("formats activity readings consistently", () => {
    expect(formatReading(0.12345)).toBe("0.123");
    expect(formatReading(0.0000042)).toBe("4.20e-6");
  });
});
