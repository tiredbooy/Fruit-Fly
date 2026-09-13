# Decision 0002: Memory-Mapped Full Connectome Engine

Date: 2026-09-13
Status: Accepted

## Context

Experiment 1 used a small auditable MaleCNS subgraph. Later gym and learning
experiments need the complete official graph without coupling world behavior to
neural implementation or loading millions of Python edge objects per step.

## Decision

Build a reproducible offline artifact from pinned MaleCNS v1.0 Feather files and
simulate it as a CPU SciPy CSR matrix. Keep all 166,606 bodies passing the
official valid-superclass filter and all 25,574,615 edges between them.

Expose compact and full engines through one `NeuralNetwork` protocol. Keep
compact as the default and require explicit `--brain full` selection. Missing or
stale full artifacts are errors, never fallback conditions.

## Why

- Sparse matrix-vector multiplication fits the graph and measured CPU hardware.
- Numeric memory-mapped arrays avoid millions of Python objects.
- Offline conversion separates expensive validation from ordinary startup.
- Exact source hashes, counts, filters, policies, and dynamics remain auditable.
- The shared boundary preserves the world/sensor/brain/motor architecture.

## Alternatives rejected

### Runtime API queries

They would make runs network-dependent, slower, and harder to reproduce. The
official dataset is local and checksum-pinned instead.

### Dense matrix

A 166,606-square dense matrix would waste prohibitive memory on absent edges.

### GPU-first engine

The development machine has no working NVIDIA runtime. A CPU reference engine
is simpler and provides a correctness baseline for later acceleration.

## Consequences

The processed artifact is 198.3 MiB on the current release and is generated
locally rather than committed. A measured neural substep takes about 14.6 ms on
the current development CPU. Full topology alone does not supply cell
biophysics, receptor-specific signs, neuromodulation, task learning, or
consciousness; those remain explicit future model layers.
