# Full MaleCNS Graph Model

## Scope

The full backend loads every MaleCNS v1.0 body passing the release's
valid-superclass rule and advances their rate-proxy activities on the CPU. It is
a structural-connectome simulation, not a biologically complete brain and not
evidence of consciousness.

## Official source selection

The three canonical source URLs and SHA-256 hashes are pinned in
`data/malecns/v1.0/source-manifest.json`. The build rule follows the official
MaleCNS counting notebook:

1. Keep annotations with a nonempty `superclass` that does not contain `tbc`.
2. Keep an edge only when both `body_pre` and `body_post` are retained.
3. Apply no structural-weight threshold.
4. Retain valid bodies even when they have no retained edge.

For the pinned v1.0 files this produces:

| Quantity | Count |
| --- | ---: |
| Valid annotated bodies | 166,606 |
| Connected bodies | 166,400 |
| Isolated valid bodies | 206 |
| Retained directed edges | 25,574,615 |

These exact v1.0 counts differ slightly from earlier publication/v0.9 numbers
because the release includes proofreading and annotation refinements. The
builder fails instead of publishing if observed counts differ from the expected
v1.0 contract.

Official release resources:

- MaleCNS downloads: https://male-cns.janelia.org/download/
- MaleCNS release notes: https://male-cns.janelia.org/release/

## Explicit polarity policy

MaleCNS supplies consensus transmitter calls; the conversion from transmitter
to fast-current sign is a simulation assumption:

| Consensus call | Fast-current sign |
| --- | ---: |
| acetylcholine | +1 |
| GABA, glutamate, histamine | -1 |
| dopamine, serotonin, octopamine, other modulators | 0 |
| unclear or missing | 0 |

Zero means no ordinary fast-current propagation in this engine. It does not
mean that the biological neuron has no effect. Dedicated receptor-specific and
neuromodulatory dynamics are outside this milestone.

## Rate dynamics

For official edge weight `w(pre, post)`, the builder stores:

```text
A(post, pre) = sign(pre) * log(1 + w(pre, post))
               / sum_pre log(1 + w(pre, post))
```

Each synchronous substep computes:

```text
current  = A @ activity
driven   = tanh(max(0, current))
activity = 0.30 * previous + 0.70 * driven
```

External sensory bodies are clamped to values in `[0, 1]` after every substep.
This matches the compact engine's leaky rate equation. The equation, leak,
normalization, synchronous updates, and clamping are engineering assumptions;
MaleCNS provides structure rather than membrane dynamics.

## Artifact and validation

`make brain-build` writes sorted IDs and CSR arrays as fixed numeric NumPy files,
plus metadata containing schema, dataset, source hashes, counts, filter, polarity
policy, dynamics version, and transmitter counts. Publishing uses a temporary
sibling and atomic directory replacement. `make brain-status` memory-maps and
validates the complete contract before reporting readiness.

The generated artifact is reproducible and git-ignored. No biological ID, class,
type, edge, weight, or transmitter call is invented during conversion.
