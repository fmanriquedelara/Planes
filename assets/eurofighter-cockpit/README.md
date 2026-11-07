# Eurofighter cockpit — UE-008

2026-11-07 visibility update: the existing bow, lip, fasteners, lugs and latches
now export as four `EF_CanopyBow_*` assemblies, each with one opaque material at
slot 0. Geometry is unchanged (168,228 triangles); the export now has 18 sections.
The Unreal comparison builder tags these components `PlanesCanopyBow` and creates
`/Game/EurofighterCockpitStudy/Materials/M_CanopyBowClear.M_CanopyBowClear` for the
runtime cockpit-only transparency option. Exterior views restore their original
slot-0 materials. The clear material uses 0.025 opacity with subdued unlit colour.
Existing photo-comparison files retain their earlier source hash and appearance;
the split does not change the opaque silhouette. The rebuilt opaque Blender
pilot view was inspected; runtime switching is validated in Unreal separately.

Separate editable, reference-informed single-seat cockpit with the conventional
three-display arrangement. Original source models are retained, and Gripen remains
the default Unreal scene. The displays are authored illustrative static art, not functional
avionics or a claim of exact operational screen formats.

## Files and reproduction

- `EurofighterCockpit.blend`: packed Blender 3.6.2 source with a calibrated pilot
  camera, neutral studio lights and material-organized editable meshes.
- `EurofighterCockpit.glb`: cockpit-only runtime export; 14 merged material
  assemblies instead of thousands of per-button draw calls.
- `build_cockpit.py` and `geometry_v6.py`: reproducible geometry, materials,
  export and studio previews. The latter replaces the rejected revision 5 shapes.
- `make_textures.py`: original display artwork, legend atlas and woven-fabric maps.
  Requires Pillow and Windows Consolas. No photographic pixels are in game textures.
- `EF_AirframeFit.glb` / `build_airframe_fit.py`: separate optional fit derivative,
  only the original airframe with its obsolete disconnected front bow removed.
- `asset-metrics.json` and `airframe-fit-metrics.json`: measured asset statistics.
- `preview-pilot.png`, `preview-reference-front.png` and
  `preview-reference-oblique.png`: current Blender studio evidence, not Unreal
  performance evidence. Native Unreal captures are maintained by Milu.
- `reference-cameras.json`: explicit camera coordinates, lens and resolution for
  the two estimated photo-comparison views. These are not calibrated photogrammetry.
- `shape-metrics.json`: approximate model proportions corresponding to photo
  landmarks. Perspective and occlusion must still be judged in rendered images.

Run the texture script with a Pillow-equipped Python, then:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 3.6\blender.exe' -b --factory-startup -t 6 --python assets/eurofighter-cockpit/build_cockpit.py
& 'C:\Program Files\Blender Foundation\Blender 3.6\blender.exe' -b --factory-startup -t 4 --python assets/eurofighter-cockpit/build_airframe_fit.py
```

The builder uses CPU Cycles, 24 samples with denoising. Pilot evidence is
1600x1000, 18mm on a 36mm horizontal sensor, eye at origin and pitch -4 degrees.
The front/oblique views are estimated elevated inspection views, not pilot cameras.
Studio exposure
and lighting are independent of Unreal's EV13 environment.

## Coordinate and integration contract

Cockpit GLB is in **metres**, Blender **+X forward, +Y pilot-left, +Z up**,
with origin at the pilot eye. Standard glTF import converts metres to Unreal
centimetres. Import at scale 1 and attach at rig-relative **(650,0,122.5) cm**.
Keep camera at that calibrated eye; do not scale cockpit and camera independently.

Airframe-fit GLB instead uses full aircraft coordinates in metres: attach at
the rig origin with scale 1. It contains only the original `Object_4` remainder.
Hide old `Object_4`, both cockpit copies (`Object_8`, `Object_8.001`, Unreal may
sanitize the dot), and old HUD `Object_10`. Original `Object_6` canopy glazing
can be hidden for the cockpit study; new front windscreen glazing is included.
Other exterior parts, including `Object_12`, must not be hidden by a blanket
glass-material rule.

The old bow is a disconnected 91-vertex island in `Object_4`, verified by a
color-coded source render. The fit script asserts its topology and bounding box
before removal. It never modifies the original GLB or `.blend`.

Fit measurements from the source after its existing 0.1 scale:

| Part | X bounds m | Y bounds m | Z bounds m |
| --- | --- | --- | --- |
| Original cockpit copies | 4.634–8.583 | -0.534–0.534 | 0.174–1.356 |
| Original canopy | 4.634–8.441 | -0.456–0.456 | 0.719–1.442 |
| Original HUD | 7.281–7.408 | -0.143–0.143 | 0.988–1.257 |
| Removed old front bow | 6.976–7.225 | -0.448–0.448 | 0.774–1.331 |

These are model fit constraints, **not manufacturer-verified cockpit dimensions**.
The new bow is somewhat taller/wider to preserve a clear pilot view and smooth
photo-informed curvature. Native chase/canopy views must be checked for fit.

## References and provenance

The current PRIMARY visual targets are the user's supplied images, preserved in
`references/eurofighter-cockpit/user/front.png` and `oblique.png`. Both were
inspected before the structural rewrite. The oblique photograph has a stock-photo
watermark; it is reference-only and no part of it is copied into textures.

Supporting visual reference inspected: Ministry of Defence/Pete Mobbs 2010
cockpit photograph [45152531](https://www.flickr.com/photos/defenceimages/5553768680),
as tracked in `references/eurofighter-cockpit/reference-review.md`.
Supporting close-up inspected: [Bredow ILA 2008 cockpit](https://www.bredow-web.de/ILA_2008/Luftwaffe/Eurofighter_Typhoon/eurofighter_typhoon.html).
The photo-informed features are the three near-square MHDDs (center lower),
projecting HUD controls and rounded thin combiner, paired supports, left keypad,
upper-right standby dial, central stick, left throttle, console and seat layout.
The module does not reproduce engineering drawings, wiring or every control.

The newly authored cockpit geometry, legends and display graphics do not reuse
photographic textures or triangles from the old cockpit. The **airframe-fit
derivative** does retain the source mesh and texture and remains subject to
**CC BY-NC-SA 4.0**, original author **bohmerang**,
[source model](https://sketchfab.com/3d-models/eurofighter-typhoon-fighter-jet-free-992bcc8987964ca09d55410330aa8579).
See `unreal-prototype/CREDITS.md` for the original repository asset history.

## Validation and limits

The user rejected revision 5 geometry despite its earlier bounded rendering pass.
Its packed source/export and previews are archived in ignored `artifacts/revision5`;
the old overview preview is superseded. That acceptance does not establish the
current shape gate. The current rewrite replaces the box-like HUD with a shallow
stepped housing, uses a curved combiner, a curved continuous coaming,
thin compact display plates, closed deep footwells, an inclined narrow pedestal,
compact asymmetric console equipment, and a broad U-notched seat cover. The
instrument cluster is 100mm higher than the rejected blockout; the stick/seat
assembly moved forward 320mm to remove its long empty center bridge. Bow sides
now narrow into lower attachment feet instead of ending at maximum width.

Revision 7 is a bounded HUD detail pass guided by the newer day close-up, night
view and oblique photo in `references/eurofighter-cockpit/user/detail-pass`.
It corrects the earlier flat-topped shield into a continuous oval with the same
348x260mm envelope, a fine upper edge and thicker lower optical edge. Tapered
kinked brackets have lighter inner faces, split clamps and circular pivots. A
layered polygonal optical tray, retaining strip, screws and stepped rear casting
sit behind shallow framed top keys. The central readout is a separately authored
512x256 dark texture with restrained green characters. The accepted display and
lower-cockpit layout is unchanged. Revision 6 packed source/export, textures,
metrics and renders are preserved in ignored `artifacts/revision6`.

The two added material assemblies are `EF_ProjectorOptics` (dark, low-roughness
optical tray/key glazing) and `EF_HUDControlDisplay` (restrained textured readout).
No functional projected HUD symbology or night-flight lighting is claimed.

Vision inspects every generated camera set; Milu/Stark own final native evidence
and independent acceptance. Do not infer acceptance from file existence. This is
a photo-informed game approximation, not a museum/engineering replica.
Micro-wear, exact labels, real avionics, complete canopy rear glazing, LODs and
animated controls remain outside this first asset pass. Emissive screen art is
deliberately restrained; engine-specific glass and masked-label material setup
may need overrides on import. Real-time performance can only be established by
the native Unreal timing run, not these studio images or triangle totals.

Historical revision 6 Unreal validation: all 31 native input/menu checks passed and
Milu/Stark inspected cockpit, chase and canopy views. At 3440x1440 Epic settings
on the RTX 4060 Ti, 3,000-frame samples averaged 54.64 FPS at native resolution
and 65.60 FPS with 85% internal resolution and TSR. The original cockpit averaged
56.51 FPS at native resolution. See `tasks/UE-008.md` and the Unreal prototype
README for full conditions, review limitations and the separate launch helper.
Those performance numbers do not validate the newer revision 7 detail export;
new native validation and independent review are required.
