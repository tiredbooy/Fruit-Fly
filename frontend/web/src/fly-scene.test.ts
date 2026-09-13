import { describe, expect, test } from "bun:test";

import {
  cameraFocusX,
  interpolateHeading,
  neuralIntensity,
  odorHaloScale,
  worldToScene,
} from "./fly-scene";

describe("worldToScene", () => {
  test("maps world corners into the specimen chamber", () => {
    expect(worldToScene(-10, -6, 20, 12)).toEqual({ x: -10, z: 6 });
    expect(worldToScene(10, 6, 20, 12)).toEqual({ x: 10, z: -6 });
  });

  test("keeps an edge-positioned fly visible in a narrow viewport", () => {
    expect(cameraFocusX(-9, 10, 20)).toBe(-5);
    expect(cameraFocusX(9, 10, 20)).toBe(5);
    expect(cameraFocusX(4, 22, 20)).toBe(0);
  });
});

describe("scene signals", () => {
  test("interpolates across the shortest heading arc", () => {
    const result = interpolateHeading(Math.PI * 1.9, Math.PI * 0.1, 0.5);
    expect(result).toBeCloseTo(Math.PI * 2, 6);
  });

  test("clamps odor halo scale and handles absent food", () => {
    expect(odorHaloScale(null)).toBe(0);
    expect(odorHaloScale(0.25)).toBeCloseTo(0.75);
    expect(odorHaloScale(5)).toBe(2.4);
  });

  test("uses zero intensity for an inactive network", () => {
    expect(neuralIntensity([])).toBe(0);
    expect(neuralIntensity([0.2, 0.8])).toBeCloseTo(0.5);
    expect(neuralIntensity([4])).toBe(1);
  });
});
