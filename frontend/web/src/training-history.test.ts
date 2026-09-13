import { expect, test } from "bun:test";
import { TrainingHistory } from "./training-history";

test("training traces keep actual per-fly samples and bounded memory", () => {
  const history = new TrainingHistory();
  for (let second = 0; second < 300; second++) history.record("fly-1", second, 0.2, 0.4);
  history.record("fly-2", 299, 0.8, 0.1);
  expect(history.forFly("fly-1")).toHaveLength(240);
  expect(history.forFly("fly-1")[0]).toEqual({time:60,association:0.2,fatigue:0.4});
  expect(history.forFly("fly-2")).toEqual([{time:299,association:0.8,fatigue:0.1}]);
});

test("paused duplicate samples do not fabricate a learning curve; restart clears stale history", () => {
  const history = new TrainingHistory();
  history.record("fly-1", 10, 0.2, 0.3);
  history.record("fly-1", 10, 0.2, 0.3);
  expect(history.forFly("fly-1")).toHaveLength(1);
  history.record("fly-1", 1, 0, 0);
  expect(history.forFly("fly-1")).toEqual([{time:1,association:0,fatigue:0}]);
});
