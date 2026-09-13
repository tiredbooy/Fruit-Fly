import { describe, expect, test } from "bun:test";

import { filterNeuronReadings } from "./neuron-readings";
import type { ActiveNeuron } from "./types";

const readings: readonly ActiveNeuron[] = [
  { body_id: 11177, label: "DNp09#11177", activity: 0.5 },
  { body_id: 63316, label: "L2#63316", activity: 0 },
  { body_id: 10783, label: "DNp09#10783", activity: 0.5 },
  { body_id: 520151, label: "MBON01#520151", activity: 0.8 },
];

describe("filterNeuronReadings", () => {
  test("returns every reading sorted by activity then body ID for an empty query", () => {
    expect(filterNeuronReadings(readings, "")).toEqual([
      readings[3]!, readings[2]!, readings[0]!, readings[1]!,
    ]);
  });

  test("matches labels without case sensitivity", () => {
    expect(filterNeuronReadings(readings, "dNp09")).toEqual([readings[2]!, readings[0]!]);
  });

  test("matches a body ID substring", () => {
    expect(filterNeuronReadings(readings, "633")).toEqual([readings[1]!]);
  });

  test("retains received zero-activity readings", () => {
    expect(filterNeuronReadings(readings, "L2")).toEqual([readings[1]!]);
  });

  test("returns an empty array when nothing matches", () => {
    expect(filterNeuronReadings(readings, "missing")).toEqual([]);
  });

  test("returns a new array without changing input order", () => {
    const original = [...readings];
    const result = filterNeuronReadings(readings, "");
    expect(result).not.toBe(readings);
    expect(readings).toEqual(original);
  });
});
