import type { ActiveNeuron } from "./types";

export function filterNeuronReadings(
  neurons: readonly ActiveNeuron[],
  query: string,
): ActiveNeuron[] {
  const needle = query.trim().toLocaleLowerCase();
  return neurons
    .filter((neuron) => (
      !needle
      || neuron.label.toLocaleLowerCase().includes(needle)
      || neuron.body_id.toString(10).includes(needle)
    ))
    .slice()
    .sort((left, right) => right.activity - left.activity || left.body_id - right.body_id);
}
