# Asset credits

## Separate Eurofighter cockpit study (UE-008)

The cockpit under `../assets/eurofighter-cockpit/` is newly authored in Blender
from visually inspected public cockpit photographs and the existing model's fit
envelope. Its geometry, painted legends and illustrative screen artwork do not
copy the old cockpit triangles or photographic pixels. Reference sources and
limitations are recorded in that folder's README and
`../references/eurofighter-cockpit/reference-review.md`.

The separate `EF_AirframeFit.glb` does retain bohmerang's original exterior mesh
and texture. It removes the old disconnected 116-triangle front canopy bow to
avoid overlapping the new frame and retains the **CC BY-NC-SA 4.0** attribution
and conditions below. Neither original aircraft source is overwritten.
The new optics and masked legend paint are Unreal study material adjustments.

## Eurofighter Typhoon — optional retained aircraft

- Author: **bohmerang**.
- Original: [Eurofighter Typhoon — Fighter Jet — Free on Sketchfab](https://sketchfab.com/3d-models/eurofighter-typhoon-fighter-jet-free-992bcc8987964ca09d55410330aa8579).
- License: [Creative Commons Attribution–NonCommercial–ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
- Original repository source: `../Shark 600/eurofighter_typhoon_-_fighter_jet_-_free.glb`.
- Imported derivative: `../Godot/Planes/HighResEurofighter.glb`.

The original GLB embeds this author, source and license. The existing Godot
derivative omits that metadata, so attribution is retained here. It contains
modified/re-exported geometry and textures. Unreal changes include scene scale,
material/glass compatibility and pilot-camera placement. Eurofighter-derived
asset modifications retain CC BY-NC-SA 4.0; this attribution does not imply author
endorsement. NonCommercial and ShareAlike conditions apply to this asset.

Physical cockpit panels, button geometry and instrument textures are supplied by
the model. They are not a custom modeled or clickable avionics system.

## SAAB JAS 39A Gripen — default aircraft

- Author: **ngkoret**.
- Source: [SAAB JAS 39A Gripen — detailed cockpit on Sketchfab](https://sketchfab.com/3d-models/saab-jas-39a-gripen-detailed-cockpit-f4646ccf489341c28c4118de38feface).
- License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Repository source: `../Shark 600/saab_jas_39a_gripen_detailed_cockpit.glb`.

Unreal imports this asset into project packages. Prototype changes include
material compatibility adjustments, transparent canopy/HUD treatment, mirror
and interior material adjustments, illustrative display treatment, and hiding
legacy visual effects. The original GLB is preserved. These changes do not imply
endorsement by the original author.

## Environment and tools

The prototype uses Epic's installed Unreal Engine atmosphere, volumetric cloud
material and basic shapes, plus project-authored scene setup and environment
content. Engine content remains subject to Epic's applicable terms and is not
copied as a separate asset pack.

User-supplied cockpit photographs are visual references, not scene backdrops or
redistributed game assets. No external environment asset pack was downloaded.
