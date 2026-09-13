# Third-party notices

The Apache License 2.0 in [`LICENSE`](LICENSE) applies to FlyBrain Lab's
original source code, documentation, and project-produced media unless a file
states otherwise. It does not replace the licenses or permissions below.

## MaleCNS v1.0 connectome

FlyBrain Lab uses official MaleCNS v1.0 annotations, connection weights,
neurotransmitter predictions, and derived anatomical soma positions under the
source's CC-BY terms. The raw datasets are not committed. Source URLs and exact
SHA-256 checksums are pinned in
[`data/malecns/v1.0/source-manifest.json`](data/malecns/v1.0/source-manifest.json).

## Drosophila CT surface

The visual body in `frontend/web/src/assets/fly/drosophila.glb` is derived from
*Behaviour and Reproduction of Drosophila Melanogaster Exposed to 3.5 GHz
Radio-Frequency Electromagnetic Fields - Underlying data* by Orestis Katsamenis,
Pieterjan De Boose, Herman Wijnen, and Arno Thielens. Source: Zenodo record
[14838021](https://zenodo.org/records/14838021), DOI
[10.5281/zenodo.14838021](https://doi.org/10.5281/zenodo.14838021). It is licensed
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Modifications
and checksums are documented in
[`frontend/web/src/assets/fly/ATTRIBUTION.md`](frontend/web/src/assets/fly/ATTRIBUTION.md)
and the adjacent source manifest.

## Authored walking-fly asset

`frontend/web/src/assets/fly/walking-fly.glb` was imported from the user's local
`fly-escape` project with explicit reuse permission. No standalone public
redistribution license was supplied for that asset, so it is not offered under
Apache-2.0. Its source revision, checksum, transformations, used animation
clips, and limitations are recorded in
[`frontend/web/src/assets/fly/walking-source.json`](frontend/web/src/assets/fly/walking-source.json).
