# Drosophila CT surface

Source: [Zenodo record 14838021](https://zenodo.org/records/14838021),
DOI [10.5281/zenodo.14838021](https://doi.org/10.5281/zenodo.14838021).

Title: *Behaviour and Reproduction of Drosophila Melanogaster Exposed to 3.5 GHz
Radio-Frequency Electromagnetic Fields - Underlying data* (2025).

Authors: Orestis Katsamenis, Pieterjan De Boose, Herman Wijnen, and Arno Thielens.
License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

The source is an adult **female** Drosophila melanogaster CT scan. It is a visual
body surface and is not the male specimen used to obtain the MaleCNS connectome.
The source metadata also contains an inconsistent "Blue Bottle Fly" common-name
label; its scientific species field and description identify D. melanogaster.
No source neural model, code, dynamics, or internal organ meshes are imported.

Changes: four external surfaces were simplified to 59,500 triangles, rotated
from CT coordinates to +X forward/+Y up, centered, and scaled to 2.2 display
units. Illustrative brown and translucent wing materials were added; color is
not measured by CT. The asset is static and has no skeleton or walking clips.
Its pose follows the authoritative Python body's position and heading.

`source-manifest.json` records checksums, mesh counts, and tool versions.
`scripts/build_fly_asset.py` reproduces the GLB from `Drosophila.zip` downloaded
from the source. Preserve this credit and the on-screen attribution when using
or modifying the asset.
