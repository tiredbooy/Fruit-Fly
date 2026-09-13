import type { ExperimentHello, FrameMessage } from "./types";

export interface GymStation { x: number; y: number; width: number; height: number; resistance: number }
export interface GymHello extends Omit<ExperimentHello, "schema"> {
  schema: 2 | 3;
  experiment: "gym";
  population: number;
  station: GymStation;
  equipment?: EquipmentStation[];
}
export type ExerciseKind = "bench_press" | "bicep_curl";
export interface EquipmentStation {
  id: string;
  kind: ExerciseKind;
  x: number;
  y: number;
  heading: number;
  load: number;
  travel: number;
  grip_radius: number;
}
export interface ExerciseSnapshot {
  station_id: string | null;
  kind: ExerciseKind | null;
  phase: "free" | "lifting" | "lowering" | "recovery";
  joint_position: number;
  joint_velocity: number;
  repetitions: number;
  completed_sets: number;
  rep_in_set: number;
  recovery_remaining: number;
  body_elevation: number;
  body_pitch: number;
  body_roll: number;
}
export interface TrainingSnapshot {
  set_progress: number;
  sets: number;
  effort: number;
  fatigue: number;
  fitness: number;
  reward: number;
  association_strength: number;
  total_work: number;
  distance: number;
}
export interface GymFly { id: string; frame: FrameMessage; training: TrainingSnapshot; exercise?: ExerciseSnapshot }
export interface GymFrame { type: "gym_frame"; schema: 2 | 3; step: number; elapsed: number; flies: GymFly[] }
export interface PopulationMessage { type: "population"; count: number }
