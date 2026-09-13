# Compact neural update performance — 2026-09-13

Caching static edge normalization and neuron labels reduced median compact
`ConnectomeNetwork.step()` time by 29.0% for Experiment 1 and 24.2% for the gym
in an alternating original/optimized comparison. This is a neural-update
microbenchmark, not an end-to-end simulation or browser performance result.

The original loop recalculated `log1p(weight)` and the same normalization and
looked up the same presynaptic sign for each edge on every substep. It also
formatted every label on each snapshot. The optimized implementation prepares
ordered `(pre, post, normalized_weight, sign)` tuples and labels per network.
It preserves multiplication and accumulation order, the leaky rate equation,
five default substeps, external clamping, and dynamic motor-role lookup.
Snapshot dictionaries remain independent copies. The trade-off is additional
per-instance storage proportional to circuit nodes and edges, plus small
constructor work. No circuit, learning, physiology, API, or full-engine changes
are part of this optimization.

## Measurements

Environment: CPython 3.14.7, Linux x86_64, AMD Ryzen 7 7700X. Both circuits were
loaded from the pinned MaleCNS v1.0 release, with source checksums verified and
every selected edge validated against the official weights asset.

Each network received 200 warm-up calls followed by nine batches of 4,000 calls
at five substeps per call. The original and optimized loops alternated order
between batches. Fixed sensory input for channel index `i` was
`(i + 1) / (channel_count + 1)`, preserving circuit channel order. Data loading,
construction, warm-up, profiling, and equality checks were outside the timer.

| Circuit | Nodes / edges | Original median µs/step | Optimized median µs/step | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| Experiment 1 | 70 / 66 | 151.05 | 107.31 | 29.0% |
| Gym | 91 / 92 | 210.13 | 159.26 | 24.2% |

The original/optimized batch ranges were 134.21–164.37 / 94.61–120.58 µs for
Experiment 1 and 203.61–221.03 / 147.88–179.38 µs for the gym. A separate run
before editing the implementation measured medians of 146.19 and 202.20 µs.
The alternating comparison above controls for some run-to-run drift; CPU
frequency, other work on the host, and Python version can still affect timings.
These are repeated steady sensory workloads, not all possible activity patterns
or a measurement of ten-fly simulation throughput.

Separate `cProfile` runs over 1,000 calls found 330,000 and 460,000 `math.log1p`
calls before the change, and zero during updates afterward. Timing results above
exclude profiler overhead.

## Verification and reproduction

The performance regression test first failed with 30 repeated logarithms across
two small-circuit updates, then passed after caching. All eight focused tests
passed (`Ran 8 tests in 5.367s`, `OK`), covering 180 exact snapshot comparisons
against the original loop on both official circuits, varied leak/substep/input
values, existing clamp behavior, ignored unknown IDs, snapshot mutation,
independent instances, unchanged prior snapshots, and mutable motor-role maps.

Run the focused checks with:

```sh
.venv/bin/python -B -m unittest tests.brain.test_network tests.brain.test_network_equivalence -v
```

The original loop is retained in the regression module. Reproduce the timing
comparison from the repository root with its pinned raw assets available:

```sh
.venv/bin/python -B - <<'PY'
import statistics
import time
from brain.network import ConnectomeNetwork
from tests.brain.test_network_equivalence import OriginalConnectomeNetwork, load_official_circuits

for name, circuit in zip(("Experiment 1", "Gym"), load_official_circuits(), strict=True):
    external = {body: (i + 1) / (len(circuit.sensory_inputs) + 1)
                for i, bodies in enumerate(circuit.sensory_inputs.values()) for body in bodies}
    networks = {"original": OriginalConnectomeNetwork(circuit),
                "optimized": ConnectomeNetwork(circuit)}
    for _ in range(200):
        assert networks["original"].step(external) == networks["optimized"].step(external)
    samples = {label: [] for label in networks}
    for repeat in range(9):
        order = list(networks.items())[::1 if repeat % 2 == 0 else -1]
        for label, network in order:
            start = time.perf_counter_ns()
            for _ in range(4000):
                network.step(external)
            samples[label].append((time.perf_counter_ns() - start) / 4000 / 1000)
        assert networks["original"].step({}, substeps=0) == networks["optimized"].step({}, substeps=0)
    print(name, {label: statistics.median(values) for label, values in samples.items()})
PY
```

The root task will run `make test` and `make data-status` after concurrent
equipment changes finish. These integration checks are not claimed by this
isolated optimization report.
