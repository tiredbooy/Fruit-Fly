# Experiment 1 Learning and Memory

## Scientific scope

Experiment 1 models one bounded form of learning: an appetitive association
between the current DM1 food-odor channel and ingestion reward. It does not model
general intelligence, episodic memory, awareness, or consciousness.

The architecture follows the established Drosophila mushroom-body motif:
olfactory projection neurons activate sparse Kenyon cells (KCs), reward-related
PAM dopaminergic neurons gate plasticity, and KC-to-MBON synapses store learned
odor value.

## Official data provenance

Dataset: `male-cns:v1.0`

Learning model: `pam01-kc-mbon01-v1`

| Asset | SHA-256 |
| --- | --- |
| Body annotations | `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2` |
| Connectome weights | `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1` |
| Neurotransmitters | `95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621` |

Canonical URLs are pinned in `data/malecns/v1.0/source-manifest.json`.

## Selected official populations

| Function | Official annotation | Body IDs | Official transmitter |
| --- | --- | --- | --- |
| Left odor projection | `DM1_lPN_L` | `10208` | acetylcholine |
| Right odor projection | `DM1_lPN_R` | `10176` | acetylcholine |
| Left memory output | `MBON01(y5B'2a)_L` | `520151` | glutamate |
| Right memory output | `MBON01(y5B'2a)_R` | `10013` | glutamate |
| Reward modulation | `PAM01(y5)`, class `DAN` | 44 bodies listed below | dopamine |
| Sparse odor representation | type `KCg-m`, class `Kenyon_Cell` | 24 per side | acetylcholine |

PAM01 body IDs:

```text
53285 62731 63391 74856 80744 83277 88477 90867 93704 99089
100258 113067 114216 114700 129563 138629 141615 144315
145094 145148 146603 150177 153931 155916 156028 156046
159062 159158 164086 165365 167009 169278 181924 185518
197691 198758 205884 212085 252045 325731 506819 523638
533294 543677
```

Representative ORN_DM1-to-DM1_lPN edges use the four strongest official edges
per side:

| Side | ORN_DM1 body | DM1_lPN body | Weight |
| --- | ---: | ---: | ---: |
| L | 176260 | 10208 | 143 |
| L | 222974 | 10208 | 142 |
| L | 180317 | 10208 | 134 |
| L | 821459348 | 10208 | 132 |
| R | 189605 | 10176 | 175 |
| R | 153046 | 10176 | 143 |
| R | 226920 | 10176 | 143 |
| R | 123123 | 10176 | 140 |

## Deterministic Kenyon-cell selection

Eligible paths must satisfy all conditions:

1. The intermediate neuron has official `class == Kenyon_Cell`.
2. The neuron has an official `DM1_lPN -> KC` edge of weight at least 10.
3. The neuron has an official `KC -> MBON01` edge of weight at least 10 in the
   same hemisphere.
4. Paths rank by descending minimum edge weight, descending weight product, then
   ascending KC body ID.
5. The first 24 paths per hemisphere are retained.

Selected paths:

| Side | KC body | PN-to-KC | KC-to-MBON01 |
| --- | ---: | ---: | ---: |
| L | 133564 | 39 | 33 |
| L | 149820 | 36 | 32 |
| L | 538096 | 35 | 31 |
| L | 43354 | 35 | 29 |
| L | 37916 | 33 | 28 |
| L | 50791 | 30 | 28 |
| L | 72116 | 60 | 27 |
| L | 51865 | 32 | 27 |
| L | 124021 | 32 | 27 |
| L | 42744 | 30 | 27 |
| L | 144730 | 30 | 27 |
| L | 47988 | 48 | 26 |
| L | 81740 | 41 | 25 |
| L | 69417 | 34 | 25 |
| L | 131373 | 32 | 25 |
| L | 122285 | 25 | 28 |
| L | 580641 | 28 | 25 |
| L | 51583 | 27 | 25 |
| L | 137890 | 25 | 27 |
| L | 163735 | 37 | 24 |
| L | 67468 | 24 | 34 |
| L | 102954 | 33 | 24 |
| L | 130324 | 32 | 24 |
| L | 97348 | 24 | 31 |
| R | 45881 | 33 | 37 |
| R | 53144 | 50 | 30 |
| R | 83162 | 37 | 30 |
| R | 66583 | 27 | 32 |
| R | 73750 | 35 | 26 |
| R | 75652 | 34 | 26 |
| R | 125860 | 31 | 26 |
| R | 93485 | 37 | 25 |
| R | 34130 | 32 | 25 |
| R | 109268 | 32 | 25 |
| R | 53050 | 38 | 24 |
| R | 44024 | 37 | 24 |
| R | 44940 | 24 | 31 |
| R | 76493 | 24 | 30 |
| R | 44840 | 26 | 24 |
| R | 86985 | 61 | 23 |
| R | 64471 | 23 | 30 |
| R | 53688 | 23 | 27 |
| R | 50839 | 22 | 30 |
| R | 59286 | 29 | 22 |
| R | 83833 | 22 | 27 |
| R | 103144 | 27 | 22 |
| R | 43876 | 32 | 21 |
| R | 49632 | 26 | 21 |

The machine-readable source of truth is
`data/circuits/foraging-v1-learning.json`. `make data-status` checks every edge
triple against the official weights table.

## Learning equations

These equations are model assumptions, not values supplied by MaleCNS.

For PN-to-KC structural weight `w_i`, side odor input `s`, and the maximum
selected weight `w_max`:

```text
KC_i = s * log(1 + w_i) / log(1 + w_max)
```

Only the strongest 10 percent of KCs on each side remain active. The rest are
set to zero to represent sparse coding.

Eligibility for KC `i` is:

```text
e_i(t) = 0.92 * e_i(t-1) + 0.08 * KC_i(t)
```

When normalized PAM reward `r` arrives, the KC-to-MBON01 multiplier is depressed:

```text
m_i(t+1) = max(0.35, m_i(t) - 0.08 * r * e_i * (m_i(t) - 0.35))
```

Association strength and recall salience are:

```text
association = 1 - mean(m_i)
learned_salience = 1 + association
odor_drive = physical_odor * hunger_gain * learned_salience
```

There is no learned-action threshold. Memory continuously changes the odor drive
entering the existing MaleCNS-derived sensor-to-descending network.

## Evidence versus assumptions

Data-derived facts:

- all IDs, types, classes, sides, transmitter calls, and structural weights;
- DM1_lPN-to-KC and KC-to-MBON01 connectivity;
- PAM01 dopamine identity;
- bilateral organization.

Functional evidence from primary literature:

- mushroom bodies are central to olfactory associative learning;
- KCs sparsely represent odors;
- PAM dopamine conveys appetitive reinforcement;
- KC-to-MBON plasticity stores learned odor value;
- appetitive conditioning depresses odor-specific input to avoidance-associated
  MBON pathways.

Explicit simulation assumptions:

- ACV-like food odor is represented by the DM1 channel;
- contact ingestion creates one unit PAM01 reward and consumes that food source;
- spawn delays, lifetimes, distances, and inaccessible-spawn probability are
  world-model assumptions rather than MaleCNS measurements;
- 24 KCs per side and 10 percent activity are sufficient for Experiment 1;
- the discrete eligibility and depression equations above;
- mean depression continuously increases food-odor salience;
- there is no consolidation, extinction, spontaneous recovery, or interference.

## Primary sources

- Li et al. 2020, "The connectome of the adult Drosophila mushroom body provides
  insights into function," https://elifesciences.org/articles/62576
- Aso et al. 2014, "Mushroom body output neurons encode valence and guide
  memory-based action selection in Drosophila,"
  https://elifesciences.org/articles/4580
- Jacob et al. 2024, "Dopamine-mediated interactions between short- and
  long-term memory dynamics,"
  https://www.nature.com/articles/s41586-024-07819-w
- Eichler et al. 2017, "The complete connectome of a learning and memory centre
  in an insect brain," https://doi.org/10.1038/nature23455

## What is not modeled

- receptor biophysics, spikes, calcium, dopamine diffusion, or receptor kinetics;
- MB compartments beyond the selected gamma-5-related path;
- recurrent MBON-DAN feedback and prediction errors;
- short-versus-long-term consolidation and protein synthesis;
- multiple odors, negative reinforcement, extinction, or reversal learning;
- development, sleep, attention, subjective experience, or consciousness.
