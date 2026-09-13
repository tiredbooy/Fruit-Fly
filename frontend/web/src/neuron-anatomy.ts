import type { ActiveNeuron } from "./types";

export interface NeuronAnatomy {
  schema: 1;
  dataset: "male-cns:v1.0";
  eligible_count: number;
  measured_count: number;
  points: [number, number, number, number][];
}

/** Reject mismatched provenance or malformed atlas data; never fill missing somata. */
export function parseAnatomy(value: unknown): NeuronAnatomy {
  if (!value || typeof value !== "object") throw new Error("Missing anatomy");
  const record = value as Record<string, unknown>;
  const source = record.source as Record<string, unknown> | undefined;
  if (record.schema !== 1 || record.dataset !== "male-cns:v1.0" ||
      source?.sha256 !== "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2" ||
      record.eligible_count !== 166606 || !Array.isArray(record.points) ||
      record.measured_count !== record.points.length || record.points.length > 166606) {
    throw new Error("Incompatible anatomical source");
  }
  const ids = new Set<number>();
  for (const point of record.points) {
    if (!Array.isArray(point) || point.length !== 4 || !Number.isSafeInteger(point[0]) || point[0] <= 0 ||
        ids.has(point[0]) || !point.slice(1).every((v) => typeof v === "number" && Number.isFinite(v) && Math.abs(v) <= 1.001)) {
      throw new Error("Invalid measured soma");
    }
    ids.add(point[0]);
  }
  return record as unknown as NeuronAnatomy;
}

export function observedSomata(positions: ReadonlyMap<number, readonly number[]>, neurons: readonly ActiveNeuron[]) {
  return neurons.flatMap((neuron) => {
    const position = positions.get(neuron.body_id);
    return position ? [{ neuron, position, active: neuron.activity > 0 }] : [];
  });
}
