"""Deterministic DM2 extraction and validated Experiment 2 circuit loading."""

from dataclasses import asdict, replace
import json
from pathlib import Path
from types import MappingProxyType

import pandas as pd

from brain.data import LoadedMaleCNS, SourceManifest, load_release, file_sha256
from brain.gym_selection import WeightScanner, choose_path, route_paths, effective_side
from brain.learning import LearningCircuit
from brain.network import RuntimeCircuit

GymCircuits = tuple[RuntimeCircuit, LearningCircuit, LearningCircuit]


def build_gym_documents(root: Path) -> tuple[dict, dict]:
    """Select ACH routes and 24 DM1-disjoint KC paths per side from official assets."""
    source = SourceManifest.from_json(root / 'data/malecns/v1.0/source-manifest.json')
    raw = root / 'data/raw/malecns/v1.0'
    for name, asset in source.sources.items():
        if file_sha256(source.asset_path(name, raw)) != asset.sha256:
            raise ValueError(f'Checksum mismatch: {name}')
    annotations = pd.read_feather(source.asset_path('annotations', raw))
    annotations['effective_side'] = [effective_side(row) for row in annotations.itertuples(index=False)]
    nts = pd.read_feather(source.asset_path('neurotransmitters', raw))
    ach = set(nts.loc[nts['consensus_nt'] == 'acetylcholine', 'body'].astype(int))
    scanner = WeightScanner(source.asset_path('weights', raw))
    runtime = json.loads((root / 'data/circuits/foraging-v1-runtime.json').read_text())
    food = json.loads((root / 'data/circuits/foraging-v1-learning.json').read_text())
    orns = {side: set(annotations.loc[(annotations['type'] == 'ORN_DM2') &
            (annotations['effective_side'] == side), 'bodyId'].astype(int)) for side in ('L', 'R')}
    pns = {side: set(annotations.loc[(annotations['type'] == 'DM2_lPN') &
           (annotations['effective_side'] == side), 'bodyId'].astype(int)) for side in ('L', 'R')}
    paths = route_paths(scanner, set.union(*orns.values()), set(runtime['motor_roles'].values()), ach)
    runtime_edges = {(e['body_pre'], e['body_post'], e['weight']) for e in runtime['edges']}
    selected_routes = []
    for side in ('L', 'R'):
        sensory_ids = set()
        for role, target in runtime['motor_roles'].items():
            path = choose_path([p for p in paths if p[0].pre in orns[side] and p[-1].post == target])
            if path is None:
                raise ValueError(f'Missing DM2 route: {side} {role}')
            sensory_ids.add(path[0].pre)
            runtime_edges.update((e.pre, e.post, e.weight) for e in path)
            selected_routes.append({'side': side, 'role': role, 'bodies': [path[0].pre] + [e.post for e in path]})
        runtime['sensory_inputs'][f'gym_{"left" if side == "L" else "right"}'] = sorted(sensory_ids)
    runtime['edges'] = [_record(e) for e in sorted(runtime_edges)]
    runtime['gym_selection'] = {'minimum_weight': 10, 'maximum_hops': 4,
        'rule': 'ACH only; shortest, strongest bottleneck, largest product, ascending body IDs',
        'routes': selected_routes}
    kc_ids = set(annotations.loc[annotations['class'] == 'Kenyon_Cell', 'bodyId'].astype(int)) & ach
    excluded = {edge['body_post'] for edge in food['pn_kc_edges']}
    pn_edges = scanner.select(pre_ids=set.union(*pns.values()), post_ids=kc_ids - excluded)
    mbon_edges = {(e.pre, e.post): e for e in scanner.select(post_ids=set(food['mbon01_neurons'].values())) if e.pre in kc_ids}
    learning = {key: food[key] for key in ('dataset', 'source_weights_sha256', 'mbon01_neurons', 'pam01_neurons')}
    learning.update(model='gym-dm2-pam01-kc-mbon01-v1', projection_type='DM2_lPN', odor_type='ORN_DM2',
        selection={'kenyon_cells_per_side': 24, 'rule': 'Exclude all food KCs; rank PN-KC-MBON pairs by bottleneck, product, KC ID; choose PN by top-24 minimum bottleneck, total products, PN ID'},
        projection_neurons={}, orn_pn_edges=[], pn_kc_edges=[], plastic_edges=[])
    for side in ('L', 'R'):
        mbon = food['mbon01_neurons'][side]
        ranked = []
        for pn in sorted(pns[side] & ach):
            pairs = [(e, mbon_edges[e.post, mbon]) for e in pn_edges if e.pre == pn and (e.post, mbon) in mbon_edges]
            pairs.sort(key=lambda pair: (-min(pair[0].weight, pair[1].weight), -pair[0].weight * pair[1].weight, pair[0].post))
            if len(pairs) >= 24:
                ranked.append((pn, pairs[:24]))
        pn, pairs = min(ranked, key=lambda item: (-min(min(a.weight, b.weight) for a, b in item[1]), -sum(a.weight * b.weight for a, b in item[1]), item[0]))
        learning['projection_neurons'][side] = pn
        for a, b in pairs:
            learning['pn_kc_edges'].append(_record((a.pre, a.post, a.weight)))
            learning['plastic_edges'].append(_record((b.pre, b.post, b.weight)))
        orn_edges = sorted(scanner.select(pre_ids=orns[side], post_ids={pn}), key=lambda e: (-e.weight, e.pre))[:4]
        learning['orn_pn_edges'].extend(_record((e.pre, e.post, e.weight)) for e in orn_edges)
    evidence = {name: asdict(asset) for name, asset in source.sources.items()}
    for document in (runtime, learning):
        document['evidence'] = evidence
        document['gym_assumptions'] = ['DM2 is a synthetic station cue, not a gym neuron identity.',
            'KC learning modulates only its cue sensory gain; no assumed MBON fast-current sign.',
            'Reward schedule and physiology are dimensionless model assumptions in docs/science/gym.md.',
            'Descending motor drive powers a synthetic foreleg actuator; bench/curl joints, grip, range reflex and recovery are not measured neuron functions (docs/science/equipment.md).']
    return runtime, learning


def _record(edge: tuple[int, int, int]) -> dict[str, int]:
    return dict(zip(('body_pre', 'body_post', 'weight'), edge, strict=True))


def load_gym_circuits(root: Path, *, release: LoadedMaleCNS | None = None) -> GymCircuits:
    """Validate every selected runtime/learning edge on application startup."""
    source = SourceManifest.from_json(root / 'data/malecns/v1.0/source-manifest.json')
    release = release or load_release(source, root / 'data/raw/malecns/v1.0')
    options = dict(annotations=release.annotations, transmitters=release.transmitters,
                   expected_weights_sha256=source.sources['weights'].sha256)
    runtime = RuntimeCircuit.from_json(root / 'data/circuits/gym-v1-runtime.json', **options)
    release.edges.require_edges(tuple((e.body_pre, e.body_post, e.weight) for e in runtime.edges))
    food = LearningCircuit.from_json(root / 'data/circuits/foraging-v1-learning.json', edges=release.edges, **options)
    gym = LearningCircuit.from_json(root / 'data/circuits/gym-v1-learning.json', edges=release.edges, **options)
    if {e.body_pre for e in food.plastic_edges} & {e.body_pre for e in gym.plastic_edges}:
        raise ValueError('Food and gym plastic edges must use disjoint KCs')
    return (replace(runtime, sensory_inputs=MappingProxyType(runtime.sensory_inputs), motor_roles=MappingProxyType(runtime.motor_roles)),
            _freeze_learning(food), _freeze_learning(gym))


def _freeze_learning(circuit: LearningCircuit) -> LearningCircuit:
    return replace(circuit, projection_neurons=MappingProxyType(circuit.projection_neurons),
                   mbon01_neurons=MappingProxyType(circuit.mbon01_neurons))


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    for name, document in zip(('runtime', 'learning'), build_gym_documents(root), strict=True):
        destination = root / f'data/circuits/gym-v1-{name}.json'
        destination.write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')
        print(f'Built {destination.relative_to(root)}')
