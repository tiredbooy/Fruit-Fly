# Observation is not neural input

The browser exposes two different kinds of observation. They must not be
presented as a reconstruction of a fly's subjective experience.

## Fly-eye camera

The eye view is a conventional perspective camera in the Three.js arena. Its
pose uses the rendered body's position and heading: +X points forward at zero
heading, with scene Z negated relative to the Python world's Y axis. The display
assumptions are a 0.8-unit head offset, 0.65-unit eye height, 6-unit look-ahead,
90-degree field of view, and 0.03-unit near clipping plane. These values are
visual choices, not measurements of Drosophila optics.

Hiding the selected body prevents self-occlusion; other flies remain visible.
Leaving eye view restores it and the original observer controls. The camera does not
read pixels back into the brain, change sensor gain, steer, or affect memory.
The simulation continues to use its existing bilateral scalar vision signals.
Compound-eye facets, spectral sensitivity, retinal dynamics, and photoreceptor
transduction are not implemented.

## Neuron readings

Each displayed ID, label, and activity value comes from the authoritative Python
telemetry. IDs and labels originate in the pinned MaleCNS annotations. Activity
is the current simulator's rate proxy, not measured membrane voltage, a spike,
or a thought. Search and sorting operate only on already received records.

The UI counts values greater than zero within that received subset. It does not
compute a whole-brain active count. Zero values remain inspectable; the numeric
readout preserves small nonzero values with scientific notation. Bar lengths
are bounded for display and do not change the underlying activity. The list's
order and bar placement have no anatomical meaning.

## Measured soma map

The spatial panel uses `somaLocation` from our checksum-verified official
MaleCNS v1.0 annotations, not the reference project's graph. The valid-superclass
filter yields 166,606 bodies; 139,659 have finite measured coordinates. The other
26,947 are omitted spatially, not assigned guessed positions. A global bounding
box center and uniform scale preserve relative geometry without claiming physical
display units. The export records its exact transform, source and CC-BY license.

Only matching official IDs receive live color. Dim atlas points are unobserved,
not known inactive; amber received values are exactly zero; pink values are
positive rate proxies. Brightness has a minimum visible level for positive rates,
while exact readings retain their true value. Missing positions are counted.
Neither point adjacency nor color supplies structural connections, spikes or a
whole-brain measurement. The compact gym updates 91 runtime bodies, not the
139,659 atlas points. Search changes observation only.

## Authored motion

The user-authorized fly-escape asset supplies appearance and skeletal clips only.
Our own engine determines every body position. Walking phase uses cumulative
physical displacement (display stride 0.8 units); feeding uses actual ingestion.
These are visual mappings, not measured biomechanics or evidence of intention.
The shipped Fly/Land clips remain unused: ground locomotion does not imply
airborne flight. Gym effort, fatigue and reward are defined separately in
[gym assumptions](gym.md), not inferred from an animation.

See [the observatory guide](../frontend-observatory.md) for operation and
[decision 0005](../decisions/0005-gym-and-fly-observation.md) for scope.
