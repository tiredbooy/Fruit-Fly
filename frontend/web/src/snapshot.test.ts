import { describe, expect, test } from "bun:test";

import { formatBodyId, formatReading, parseServerMessage } from "./snapshot";
import type { FrameMessage } from "./types";
import type { ExerciseSnapshot, GymFrame, GymHello } from "./gym-types";

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
  test("accepts articulated equipment without changing neural readings", () => {
    const hello = {type:"hello", schema:3, backend:"compact", dataset:"male-cns:v1.0", fps:10,
      world:{width:20,height:12}, experiment:"gym", population:1,
      station:{x:0,y:0,width:16,height:8,resistance:2},
      equipment:[{id:"station-1",kind:"bench_press",x:-6.4,y:-2,heading:.22,load:.6,travel:.7,grip_radius:.45}]} satisfies GymHello;
    expect(parseServerMessage(hello)).toEqual(hello);
    const exercise = {station_id:"station-1",kind:"bench_press",phase:"lifting",joint_position:.4,
      joint_velocity:.2,repetitions:1,completed_sets:0,rep_in_set:1,recovery_remaining:0,
      body_elevation:1.5,body_pitch:0,body_roll:Math.PI} satisfies ExerciseSnapshot;
    const population = {type:"gym_frame",schema:3,step:9,elapsed:.9,flies:[{id:"fly-1",frame,exercise,
      training:{set_progress:.4,sets:0,effort:.3,fatigue:.1,fitness:1,reward:0,association_strength:0,total_work:.2,distance:0}}]} satisfies GymFrame;
    expect(parseServerMessage(population)).toEqual(population);
    const dockedRecovery = {...exercise, phase:"recovery" as const, joint_position:0,
      joint_velocity:0,rep_in_set:0,recovery_remaining:1.5};
    const recovering: GymFrame = {...population,
      flies:[{...population.flies[0]!,exercise:dockedRecovery}]};
    expect(parseServerMessage(recovering)).toEqual(recovering);
    const detachedRecovery: GymFrame = {...population,flies:[{...population.flies[0]!,
      exercise:{...dockedRecovery,station_id:null,kind:null}}]};
    expect(parseServerMessage(detachedRecovery)).toEqual(detachedRecovery);
    for (const invalid of [{joint_position:1.01},{joint_position:-.01},{repetitions:1.5},
      {rep_in_set:3},{phase:"thinking"},{station_id:null},{joint_velocity:NaN},{body_elevation:-1}]) {
      expect(() => parseServerMessage({...population,flies:[{...population.flies[0],exercise:{...exercise,...invalid}}]})).toThrow();
    }
    expect(() => parseServerMessage({...hello,equipment:[hello.equipment[0],hello.equipment[0]]})).toThrow();
    expect(() => parseServerMessage({...hello,equipment:[{...hello.equipment[0],load:-1}]})).toThrow();
    expect(() => parseServerMessage({...population,flies:[population.flies[0],{...population.flies[0],id:"fly-2"}]})).toThrow();
  });

  test("accepts gym populations without changing the existing nested frame", () => {
    const training = {set_progress: 0.2, sets: 1, effort: 0.3, fatigue: 0.1, fitness: 1.05, reward: 0, association_strength: 0.04, total_work: 2, distance: 3};
    const population: GymFrame = {type: "gym_frame", schema: 2, step: 9, elapsed: 0.9, flies: [{id: "fly-1", frame, training}]};
    expect(parseServerMessage(population)).toEqual(population);
    expect(() => parseServerMessage({...population, flies: Array(11).fill(population.flies[0])})).toThrow();
    expect(() => parseServerMessage({...population, flies: [population.flies[0], population.flies[0]]})).toThrow();
    expect(() => parseServerMessage({...population, flies: [{...population.flies[0], training: {...training, fatigue: 2}}]})).toThrow();
  });

  test("accepts gym hello and validates actual count acknowledgements", () => {
    expect(parseServerMessage({type:"hello", schema:2, backend:"compact", dataset:"male-cns:v1.0", fps:10, world:{width:20,height:12}, experiment:"gym", population:1, station:{x:-3,y:0,width:6,height:3,resistance:2}}).type).toBe("hello");
    expect(parseServerMessage({type:"population", count:10})).toEqual({type:"population",count:10});
    for (const count of [0,11,true,1.5,"2"]) expect(() => parseServerMessage({type:"population",count})).toThrow();
  });

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
