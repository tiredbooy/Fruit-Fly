export interface TrainingSample { time: number; association: number; fatigue: number }

/** A bounded window of actual received measurements, never an authored progress curve. */
export class TrainingHistory {
  private readonly samples = new Map<string, TrainingSample[]>();
  record(id: string, time: number, association: number, fatigue: number): void {
    const samples = this.samples.get(id) ?? [];
    const previous = samples.at(-1);
    if (previous && time < previous.time) samples.length = 0;
    else if (previous && time - previous.time < 0.5) return;
    samples.push({time, association, fatigue});
    if (samples.length > 240) samples.shift();
    this.samples.set(id, samples);
  }
  forFly(id: string): readonly TrainingSample[] { return this.samples.get(id) ?? []; }
}
