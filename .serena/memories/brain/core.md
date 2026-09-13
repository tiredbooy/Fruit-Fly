# Brain module
- brain/data.py streams/checks pinned MaleCNS annotations, neurotransmitters, and the 151,856,684-row edge table.
- brain/circuit.py validates the runtime circuit manifest; brain/network.py propagates activity.
- brain/learning.py models sparse bilateral DM1_lPN -> KC -> MBON01 recall and reward-gated plasticity using official annotated bodies/edges.
- brain/memory.py owns schema-versioned KC-to-MBON multiplier state and atomic persistence.
- brain/sensory.py is the adapter: hunger and learned salience continuously modulate physical odor; no learned action threshold.
- Machine-readable manifests: data/circuits/foraging-v1.json and data/circuits/foraging-v1-learning.json.
- Dopamine validates PAM identity but is not assigned a fast excitatory/inhibitory sign.
- Scientific source/assumption ledger: docs/science/learning-memory.md.