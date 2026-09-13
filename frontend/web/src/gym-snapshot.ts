import type { GymFrame, GymHello, TrainingSnapshot, PopulationMessage } from "./gym-types";
import type { FrameMessage, ExperimentHello } from "./types";
import { asRecord, asNumber, asInteger, asString, exactKeys, field, parseNumbers, type UnknownRecord } from "./snapshot-values";
import { parseEquipment, parseExercise } from "./equipment-snapshot";

export function populationCount(value: unknown): number {
  const count = asInteger(value, "population");
  if (count < 1 || count > 10) throw new Error("Population must be 1..10");
  return count;
}

export function parsePopulation(message: UnknownRecord): PopulationMessage {
  exactKeys(message, ["type", "count"]);
  return { type: "population", count: populationCount(field(message, "count")) };
}

export function parseGymHello(message: UnknownRecord, base: (value: UnknownRecord) => ExperimentHello): GymHello {
  const schema = message.schema;
  if (message.experiment !== "gym" || (schema !== 2 && schema !== 3)) throw new Error("Invalid gym schema");
  exactKeys(message, ["type", "schema", "backend", "dataset", "fps", "world", "experiment", "population", "station", ...(schema === 3 ? ["equipment"] : [])]);
  const { experiment: _experiment, population, station, equipment, ...common } = message;
  const hello = base({ ...common, schema: 1 });
  const location = parseNumbers(station, ["x", "y", "width", "height", "resistance"], "station");
  if (location.width <= 0 || location.height <= 0 || location.resistance < 0) throw new Error("Invalid station");
  return { ...hello, schema, experiment: "gym", population: populationCount(population), station: location,
    ...(schema === 3 ? {equipment: parseEquipment(equipment)} : {}) };
}

export function parseGymFrame(message: UnknownRecord, parseFrame: (value: UnknownRecord) => FrameMessage): GymFrame {
  exactKeys(message, ["type", "schema", "step", "elapsed", "flies"]);
  const schema = message.schema;
  if ((schema !== 2 && schema !== 3) || !Array.isArray(message.flies)) throw new Error("Invalid gym schema");
  populationCount(message.flies.length);
  const seen = new Set<string>();
  const occupied = new Set<string>();
  const step = asInteger(message.step, "step"), elapsed = asNumber(message.elapsed, "elapsed");
  const flies = message.flies.map((value) => {
    const fly = asRecord(value, "fly");
    exactKeys(fly, ["id", "frame", "training", ...(schema === 3 ? ["exercise"] : [])]);
    const id = asString(fly.id, "fly.id");
    if (!/^fly-([1-9]|10)$/.test(id) || seen.has(id)) throw new Error("Invalid fly identity");
    seen.add(id);
    const frame = parseFrame(asRecord(fly.frame, "fly.frame"));
    if (frame.step !== step || frame.elapsed !== elapsed) throw new Error("Unsynchronized fly frame");
    const training = parseNumbers(fly.training, ["set_progress", "sets", "effort", "fatigue", "fitness", "reward", "association_strength", "total_work", "distance"], "training");
    validateTraining(training);
    if (schema === 2) return { id, frame, training };
    const exercise = parseExercise(fly.exercise);
    if (exercise.station_id !== null) {
      if (occupied.has(exercise.station_id)) throw new Error("Duplicate equipment occupant");
      occupied.add(exercise.station_id);
    }
    return { id, frame, training, exercise };
  });
  return { type: "gym_frame", schema, step, elapsed, flies };
}

function validateTraining(training: TrainingSnapshot): void {
  for (const key of ["set_progress", "effort", "fatigue", "reward", "association_strength"] as const) {
    if (training[key] < 0 || training[key] > 1) throw new Error(`Invalid ${key}`);
  }
  if (!Number.isSafeInteger(training.sets) || training.sets < 0 || training.fitness < 1 || training.total_work < 0 || training.distance < 0) throw new Error("Invalid training totals");
}
