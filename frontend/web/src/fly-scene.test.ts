import { describe, expect, test } from "bun:test";
import { PerspectiveCamera, Vector3 } from "three/webgpu";

import {
  cameraDistanceFor,
  arenaCameraDistance,
  eyeCameraPose,
  interpolateHeading,
  neuralIntensity,
  odorHaloScale,
  worldToScene,
} from "./scene-math";

describe("worldToScene", () => {
  test("maps world corners into the specimen chamber", () => {
    expect(worldToScene(-10, -6, 20, 12)).toEqual({ x: -10, z: 6 });
    expect(worldToScene(10, 6, 20, 12)).toEqual({ x: 10, z: -6 });
  });

  test("projects all arena corners inside the oblique perspective viewport", () => {
    for (const aspect of [1.8, 0.6]) {
      const camera = new PerspectiveCamera(45, aspect, 0.1, 180);
      camera.position.set(0.7, 0.85, 1).normalize().multiplyScalar(arenaCameraDistance(aspect));
      camera.lookAt(0, 0, 0);
      camera.updateMatrixWorld();
      for (const x of [-10.5, 10.5]) for (const y of [-1.35, 1.8]) for (const z of [-6.5, 6.5]) {
        const projected = new Vector3(x, y, z).project(camera);
        expect(Math.abs(projected.x)).toBeLessThan(1);
        expect(Math.abs(projected.y)).toBeLessThan(1);
      }
    }
  });

  test("fits the complete arena at desktop and portrait aspect ratios", () => {
    for (const aspect of [1.8, 0.6]) {
      const distance = cameraDistanceFor(13, aspect);
      const verticalAngle = Math.PI / 8;
      const horizontalAngle = Math.atan(Math.tan(verticalAngle) * aspect);
      expect(Math.asin(13 / distance)).toBeLessThanOrEqual(Math.min(verticalAngle, horizontalAngle));
    }
  });
});

describe("eyeCameraPose", () => {
  test("places a zero-heading eye at head height and looks forward", () => {
    expect(eyeCameraPose(2, 3, 0)).toEqual({
      position: { x: 2.8, y: 0.65, z: 3 },
      target: { x: 8.8, y: 0.65, z: 3 },
    });
  });

  test("uses the scene's negative z axis for a quarter turn", () => {
    const pose = eyeCameraPose(0, 0, Math.PI / 2);
    expect(pose.position.x).toBeCloseTo(0, 12);
    expect(pose.position.z).toBeCloseTo(-0.8, 12);
    expect(pose.target.x).toBeCloseTo(0, 12);
    expect(pose.target.z).toBeCloseTo(-6.8, 12);
  });

  test("preserves negative positions and headings", () => {
    const pose = eyeCameraPose(-4, -2, -Math.PI / 2);
    expect(pose.position.x).toBeCloseTo(-4, 12);
    expect(pose.position.z).toBeCloseTo(-1.2, 12);
    expect(pose.target.x).toBeCloseTo(-4, 12);
    expect(pose.target.z).toBeCloseTo(4.8, 12);
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
