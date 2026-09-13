import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { parseAnatomy, observedSomata } from "./neuron-anatomy";

test("shipped anatomy uses unique official body IDs and finite measured positions", () => {
  const anatomy = parseAnatomy(JSON.parse(readFileSync(new URL("../public/assets/neuron-positions.json", import.meta.url), "utf8")));
  expect(anatomy.points.length).toBe(139659);
  expect(anatomy.eligible_count).toBe(166606);
  expect(anatomy.points.some((point) => point[0] === 10001)).toBe(true);
});

test("anatomical highlights distinguish absent telemetry, received zero and tiny positive rates", () => {
  const positions = new Map([[10001, [0, 1, 2]], [10002, [2, 1, 0]], [10003, [1, 0, 1]]]);
  const result = observedSomata(positions, [
    { body_id: 10001, label: "DNp01", activity: 0 },
    { body_id: 10002, label: "DNp01", activity: 0.0000001 },
    { body_id: 10004, label: "DNp01", activity: 0.8 },
  ]);
  expect(result.map((point) => [point.neuron.body_id, point.active])).toEqual([[10001, false], [10002, true]]);
  expect(result[1]!.neuron.activity).toBe(0.0000001);
});

test("malformed or duplicate anatomy is rejected, never replaced with invented coordinates", () => {
  const original = JSON.parse(readFileSync(new URL("../public/assets/neuron-positions.json", import.meta.url), "utf8"));
  original.points[1] = original.points[0];
  expect(() => parseAnatomy(original)).toThrow();
  original.points[1] = [10002, null, 0, 0];
  expect(() => parseAnatomy(original)).toThrow();
});
