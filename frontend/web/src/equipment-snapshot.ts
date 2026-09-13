import type { EquipmentStation, ExerciseKind, ExerciseSnapshot } from "./gym-types";
import { asRecord, asNumber, asInteger, asString, exactKeys } from "./snapshot-values";

function kind(value: unknown): ExerciseKind {
  if (value !== "bench_press" && value !== "bicep_curl") throw new Error("Invalid exercise kind");
  return value;
}

function stationId(value: unknown): string {
  const id = asString(value, "station id");
  if (!/^station-([1-9]|10)$/.test(id)) throw new Error("Invalid equipment identity");
  return id;
}

function nonnegative(value: unknown, name: string): number {
  const result = asNumber(value, name);
  if (result < 0) throw new Error(`Invalid ${name}`);
  return result;
}

export function parseEquipment(value: unknown): EquipmentStation[] {
  if (!Array.isArray(value) || value.length < 1 || value.length > 10) throw new Error("Invalid equipment collection");
  const seen = new Set<string>();
  return value.map((entry) => {
    const station = asRecord(entry, "equipment");
    exactKeys(station, ["id", "kind", "x", "y", "heading", "load", "travel", "grip_radius"]);
    const id = stationId(station.id);
    if (seen.has(id)) throw new Error("Duplicate equipment identity");
    seen.add(id);
    const load = nonnegative(station.load, "load"), travel = nonnegative(station.travel, "travel");
    const radius = nonnegative(station.grip_radius, "grip radius");
    if (!load || !travel || !radius) throw new Error("Invalid equipment dimensions");
    return {id, kind: kind(station.kind), x: asNumber(station.x, "x"), y: asNumber(station.y, "y"),
      heading: asNumber(station.heading, "heading"), load, travel, grip_radius: radius};
  });
}

export function parseExercise(value: unknown): ExerciseSnapshot {
  const state = asRecord(value, "exercise");
  exactKeys(state, ["station_id", "kind", "phase", "joint_position", "joint_velocity", "repetitions",
    "completed_sets", "rep_in_set", "recovery_remaining", "body_elevation", "body_pitch", "body_roll"]);
  const id = state.station_id === null ? null : stationId(state.station_id);
  const exerciseKind = state.kind === null ? null : kind(state.kind);
  const phase = state.phase;
  if (phase !== "free" && phase !== "lifting" && phase !== "lowering" && phase !== "recovery") throw new Error("Invalid exercise phase");
  if ((id === null) !== (exerciseKind === null)) throw new Error("Inconsistent exercise attachment");
  if ((phase === "lifting" || phase === "lowering") && id === null) throw new Error("Inconsistent exercise attachment");
  if (phase === "free" && id !== null) throw new Error("Inconsistent exercise attachment");
  const position = nonnegative(state.joint_position, "joint position");
  if (position > 1) throw new Error("Joint is outside its range");
  const repetitions = asInteger(state.repetitions, "repetitions"), sets = asInteger(state.completed_sets, "sets");
  const inSet = asInteger(state.rep_in_set, "rep in set");
  if (repetitions < 0 || sets < 0 || inSet < 0 || inSet > 2) throw new Error("Invalid repetition count");
  return {station_id: id, kind: exerciseKind, phase, joint_position: position,
    joint_velocity: asNumber(state.joint_velocity, "joint velocity"), repetitions, completed_sets: sets,
    rep_in_set: inSet, recovery_remaining: nonnegative(state.recovery_remaining, "recovery"),
    body_elevation: nonnegative(state.body_elevation, "elevation"),
    body_pitch: asNumber(state.body_pitch, "pitch"), body_roll: asNumber(state.body_roll, "roll")};
}
