# UE-008 reference selection and independent review

Reviewer: Stark. Date: 2026-11-01. References were visually inspected, not merely
selected from search captions. Photos are reference evidence, not instructions or
texture assets. No manufacturer cockpit dimensions have been established.

**Current verdict: revision6 qualified runtime visual pass; user visual review
and photo-fidelity limitations remain explicit.** The user rejected revision5 shapes and supplied
two target photos. The earlier revision5 passes below are historical and do not
satisfy that goal. See the final candidate review at the end for the active state.

## Primary configuration

Use the traditional three-display single-seat cockpit, with the MOD front view
for arrangement and the Eurofighter seated photograph for projection/depth.
Do not combine it with proposed wide-area-display upgrades or generic simulator
screens. Photos differ in viewpoint and operating state; do not copy their pixel
positions into geometry before calibrating a camera.

1. [Cockpit of RAF Typhoon Fighter, Sgt Pete Mobbs/MOD, 8 July 2010](https://www.flickr.com/photos/defenceimages/5553768680).
   MOD image 45152531. Local inspection copy: `mod-pete-mobbs-45152531.jpg`.
   The page identifies a RAF aircraft cockpit; it does not identify its exact
   tranche or tail number. This is a high, rearward view, not the pilot eye.
   Three near-square display openings, with the center lower than the outer pair
   by roughly one quarter of a display height in this projection. Gray bezels
   surround dark screens; square softkeys form clear edge rows. Black glareshield,
   left keypad, circular upper-right standby instrument, substantial projecting
   central HUD/control housing, central stick, left throttle, gray side consoles,
   olive seat cushion and selective yellow/black safety markings are visible.
   Those are visual observations, not exact dimensions or functional avionics
   specifications. Crown Copyright; retain the page attribution and do not embed
   this photo in distributed game assets.

2. [Eurofighter official cockpit features](https://world.eurofighter.com/the-aircraft/features).
   Local inspection copy: `eurofighter-features.jpg`.
   The manufacturer describes three identical MHDDs and a wide-angle HUD.
   Its seated flight photograph shows the rounded HUD upper glass edge is thin,
   with dark clips at its sides, paired curved supports and a separate lower
   optical surface. The central equipment housing projects toward the pilot,
   occluding part of the center screen from this view. The dark glare shield,
   lighter bezels, small raised fasteners and coherent curved canopy frame provide
   material and silhouette priorities. Aircraft variant and camera calibration
   are not supplied here. The reference is useful for depth and framing, not
   absolute dimensions. Eurofighter copyright; reference-only copy.

## Supporting or rejected evidence

- [RAF MOD 45148993, SAC Mark Dixon](https://commons.wikimedia.org/wiki/File:RAF_MOD_45148993.jpg),
  local `raf-mod-45148993.jpg`: real in-flight oblique canopy view, useful for
  frame fasteners, mirror mounts, seals and glass reflection restraint. It is
  not a front panel reference. Commons records OGL v1.0 and the attribution
  Photo: SAC Mark Dixon/MOD.
- [Eurofighter Cockpit, tribp, 2012](https://commons.wikimedia.org/wiki/File:Eurofighter_Cockpit.jpg),
  local `tribp-cockpit-2012.jpg`: inspected, but the presentation looks like a
  public display/mockup and the page does not prove an operational configuration.
  Supporting shape evidence only; do not override the MOD arrangement with it.
  Commons records CC BY 2.0, author tribp.
- Search results included simulated and twin-seat interiors; these were not
  selected as primary single-seat references. No exact screen size is inferred
  from unverified forum claims.

## Baseline reviewed

`unreal-prototype/artifacts/eurofighter-cockpit.png`, existing normal-game
3440x1440 evidence. UE 5.8.4, CockpitStudy, pilot camera (650, 0, 180122.5) cm,
external aircraft scale 0.1, MaintainYFOV, EV100 13 (paired build metadata).
Visible shortcomings: faceted canopy/HUD outlines, blurred/mottled panel atlas,
weak separation of paint/glass/bezels and illegible fine instrument detail.

## Independent acceptance gates

1. Record transformed asset dimensions and eye/attachment coordinates. Treat the
   source aircraft as a fit envelope, not a manufacturer drawing.
2. Inspect a simple shaded Blender render before fine detailing: continuous arch,
   rounded thin-edged HUD, three consistent displays and projecting central unit.
3. Inspect finished native-resolution render: clean bezel depth, legible principal
   labels, restrained wear and plausible paint/rubber/glass differences. No
   expectation that all tiny text is readable from the default eye.
4. Compare matched normal-game before/after pilot views, then inspect cockpit,
   chase and canopy views for duplicates, clipping, hidden faces and fit issues.
5. Retain flight/menu controls; record triangle count, material sections, texture
   memory and matched runtime frame timings at 3440x1440 on RTX 4060 Ti. Geometry
   budgets and offline Blender stills do not prove runtime performance.

## New asset review

### First Blender preview review

Stark inspected `assets/eurofighter-cockpit/preview-pilot.png` (1600x1000) and
`preview-overview.png` (1200x1400), plus the corrected Eurofighter baseline at
`unreal-prototype/artifacts/ue008/baseline/camera-cockpit.png` (3440x1440).
Verdict: **needs changes** before a realism pass. These Blender studio previews
are not matched lighting/camera comparisons or Unreal performance evidence.

- P1: lower HUD glass has a dark blurred blotch in pilot view. Remove the
  refraction/shadow artifact; the glass must preserve a clear exterior view.
- P1: raised triangular coaming corners and pale frame/HUD supports look unlike
  the primary photographs. Vision already identified geometry and material fixes.
- P2: side consoles visibly repeat sparse identical control grids on large
  plates. Vary the front visible consoles into asymmetrical functional-looking
  clusters with guarded controls, knobs, toggles, and deliberate blank gaps.
- P2: the stick has a broad block-like cap and straight boot. Refine its rounded
  grip, narrower neck and offset button head for a less toy-like silhouette.
- P2: arch fasteners resemble bright white beads. Reduce size/brightness and
  use closer small-fastener spacing consistent with the reference appearance.
- P2: central housing face is largely blank; add the inset readout already
  planned by Vision.

The smoother arch and readable display art improve on the baseline limitations.
Precise framing, integrated cockpit realism, and performance remain unverified.

### Revision 4 Blender and Unreal review

Stark inspected the fresh Blender pilot/overview previews and all three normal-
game images in `unreal-prototype/artifacts/ue008/detail/`: `camera-cockpit.png`,
`camera-canopy.png`, and `camera-chase.png`. Native evidence: UE 5.8.4,
`/Game/Maps/EurofighterCockpitStudy`, 3440x1440, Epic, EV13, screen percentage100
(integration settings reported by Milu). Runtime metadata independently read:
pilot relative (650,0,122.5) cm, pitch -4, vertical FOV64.011; chase FOV60;
forward canopy mount (740,0,130.5), pitch -13, FOV84; Scattered clouds.

Verdict: **pass for bounded cockpit-detail improvement**, with limitations below.
The dark coaming has no earlier white intersections; the HUD blotch is absent;
screen art and principal labels are substantially clearer; the arch is smoothly
curved and no duplicate old arch is visible. Blender overview confirms more
varied console groups and a rounded stick grip. All three native views remain
usable: pilot exterior sightline clear, chase aircraft attached and complete,
canopy view looking forward over the nose. The latter is not a cockpit-detail
view and retains the prior forward camera mount. Independently read runtime
report lists all31 input/menu/camera/weather checks true.

Remaining P2: HUD glass is almost invisible in the native pilot frame, making
its supports appear disconnected. A restrained edge/Fresnel cue would better
establish the rounded optical shape without adding an opaque frame. Materials
and equipment remain clean/simplified: sparse controls compared with the real
photo, illustrative displays/standby instrument, simplified seat and hardware.
This is not an exact replica or a photorealism sign-off. No new camera blocker
or duplicate-mesh issue requires stopping the bounded integration.

Matched screen-percentage100 baseline and performance comparison remain pending.
The earlier profiler summary contains only an older baseline sample and is not
used for a frame-rate conclusion.

### Revision 5 final image review

Stark re-inspected the final three detail camera images (captured after19:05 on
2026-11-01) and the refreshed baseline pilot image (after19:03), both reported
native screen percentage100. Verdict: **pass for bounded cockpit improvement**.
The fine0.8mm graphite HUD edge now clearly defines the rounded optical surface
and joins its supports without obstructing the horizon; the previous P2 glass
visibility finding is resolved. No new chase/canopy issue is visible.

Matched pilot views show clearer controls/display art, smooth bow geometry and
coherent dark coaming. The replacement has a taller/narrower bow and a larger,
closer central equipment unit in the same camera: it is a reference-informed
rebuild, not an exact reproduction of the old mesh's framing. The prior caveats
about illustrative avionics, simplified hardware and lack of photorealism remain.
Final matched timing results are still pending at this review entry.

### Final performance review

Stark read `artifacts/ue008/performance-summary.json` and both `profile-run.json`
files after the final sequential runs19:06–19:09 UTC. Both runs:3440x1440,
screen percentage100, dynamic resolution disabled,3000 measured frames after
360 warmup frames, uncapped/VSync off. Normal-game offscreen Development renderer,
not MRQ or a packaged build. Milu reports Blender idle during these samples.

| Metric | Original cockpit | Rebuilt cockpit |
| --- | ---: | ---: |
| Mean frame time |17.696ms|18.302ms|
| Mean-derived frame rate |56.51FPS|54.64FPS|
|95th percentile frame time|18.482ms|19.490ms|
|99th percentile frame time|19.152ms|20.230ms|
|Maximum frame time|24.868ms|35.201ms|
|Mean GPU time|17.123ms|17.713ms|
|Mean draw calls|99.99|156.49|

The measured incremental mean cost is0.606ms (+3.42%). This is an acceptable
bounded prototype tradeoff for the demonstrated cockpit-detail improvement.
It does **not** establish a locked60FPS or120FPS result at native ultrawide Epic
settings. The short straight-flight sample also does not establish worst-weather
or long-run stability, nor attribute the single35.2ms maximum to the asset.
GPU local memory reported about3.12GB in both runs; that is whole-process memory,
not the cockpit's standalone texture budget.

Final Stark verdict: **pass with documented limitations** for the separate,
reference-informed cockpit asset and Unreal study. Smooth silhouette, readable
principal controls, camera usability and modest measured incremental cost are
supported. Exact aircraft fidelity, functional avionics, photorealism and sustained
60/120FPS are not claimed.

### Optional85% internal-resolution review

Stark independently inspected `detail-85pct/normal-game.png` and read its profiler
metadata/summary. Output remains3440x1440, with85% internal resolution and TSR,
dynamic resolution off. Main labels, screen content and HUD outline remain clear
in the still; no new obstruction or screen warning is visible. This supports the
optional setting visually, but a still cannot establish temporal reconstruction
quality during rapid movement.

The3000-frame sample averaged15.243ms (65.60FPS); p95 was15.904ms, p99 was16.355ms,
and the maximum was20.146ms. This offers useful60FPS headroom in the sampled
straight-flight scene. It is **upscaled**, not native-resolution performance, and
the maximum plus short sample preclude a locked60FPS guarantee. Native100% results
above remain the baseline for measuring the cockpit's incremental cost.

## User-reference geometry correction — active gate

Stark inspected both supplied targets, now preserved as `user/front.png` and
`user/oblique.png`. The first is a frontal elevated cockpit photograph; the
second is a left-oblique elevated close-up. These are the primary shape targets.
The oblique reference retains its Shutterstock watermark; no watermark removal
or incorporation of photo pixels into model textures is authorized or needed.

Revision5's smooth geometry and sharper text do not remedy its incorrect gross
shapes. **Needs changes**, not pass-with-limitations, for the intended fidelity.

### Reference landmarks and proportions

Manual image-space estimates from the499x615 frontal photo, not manufacturer
dimensions and not lens-corrected measurements:

| Landmark | Approximate image evidence | Relationship |
| --- | --- | --- |
|Complete three-bezel row|x109–403, span294px|Reference span1.0|
|HUD assembly maximum width|x193–304,111px|About0.38row /1.1outer bezel width|
|Combiner lens width|x178–324,146px|About0.50row|
|Combiner lens height|y40–148,108px|Width:height about1.35|
|Visible outer screen widths|64px left,61px right|Approximately equal|
|Visible center screen width|58px|Same equipment size, perspective/occlusion affects apparent size|
|Screen center spacing|about92px left-to-center,98px center-to-right|About1.5visible screen widths|
|Center screen vertical offset|about22px below outer screen centers|About0.35visible screen height|
|Seat visible width|x132–347,215px|About0.73three-bezel span|

Do not require exact pixel equality across unknown photo lens distortion and
viewpoint. Use the relationships to catch gross errors; fit a corresponding
camera before judging normalized silhouette landmarks.

### Required structural corrections

1. **HUD assembly:** slim shallow top five-window strip, narrower inset readout,
   stepped/tapering lower controls and visible mechanical side pivots. Remove the
   broad rectangular plinth and excessive rearward projection seen in revision5.
   At the elevated front angle all three display faces must remain visible.
2. **Combiner:** broad rounded trapezoid/shield with rounded upper shoulders,
   straighter sides and a narrower clipped/flat lower attachment region. A full
   circular/elliptical wire loop fails this silhouette. Thin supports kink/sweep
   outward from low pivots and become near-vertical at the upper clips.
3. **Panel row:** a compact continuous gray fascia supporting three thin broad
   flat bezels. Center display sits lower; outer pair close to it. Avoid separate
   bulky cabinet-like housings and a wide empty gap around the center screen.
4. **Upper contour:** coherent black glareshield, left keypad zone and right
   standby-instrument zone behind the HUD. No floating slanted bars or oversized
   triangular shelf wings. Follow the oblique photo's layered depth.
5. **Shoulders/consoles:** steep front console shoulders transition into lower
   longitudinal consoles, with distinct angled plates and asymmetric control
   clusters. Uniformly tall side rails and long flat repeated tablets fail.
6. **Leg bays/pedestal:** two deep dark footwells underneath the outer displays;
   center pedestal tapers toward the stick base instead of forming a broad box.
7. **Seat/controls:** broad U-notched cushion wraps the stick pedestal; rounded
   grip and offset button head; left throttle rests on its shaped quadrant.
   Avoid the long narrow rectangular cushion and generic repeated knobs.
8. **Frame joints:** curved frame ends connect through sculpted/triangular pivot
   lugs to the side rails. No exposed squared floating arch feet. Match the
   contour and layer thickness seen in the oblique reference, not just smoothness.

### Required evidence before a new pass

- A frontal elevated render with reference-relative HUD/lens/panel landmarks.
- A matching left-oblique render demonstrating HUD step depth, bezel thickness,
  sloping shoulders, footwells, U-notched seat and frame/rail joints.
- A separate pilot render to ensure structural corrections remain usable.
- Native Unreal cockpit/chase/canopy validation after the geometry gate passes.

The reviewer must request changes if major silhouette/proportion/depth errors
remain. A better render than the old model, more polygons, legible labels, or
acceptable FPS cannot substitute for this shape comparison. Current correction
renders are pending; no revised geometry is approved yet.

### Revision6 first reference-angle review

Stark inspected `preview-reference-front.png` and `preview-reference-oblique.png`
against both user photographs. Verdict: **needs changes; do not import as an
approved correction**. The shield combiner and stepped HUD form move in the
right direction, but these are not sufficient to pass.

- P1: large gray shoulder blocks float across/occlude the outer display faces.
  They belong below/outboard of the displays and must slope continuously into
  the console shoulders. Vision identified a transform-pivot bug.
- P1: the studio background is visible through the lower panel/leg bays. These
  require a closed bulkhead and recessed dark footwell floors/walls, not holes.
- P1: sparse isolated console tablets and tall divider walls do not match the
  continuous densely equipped gray console surfaces in the targets. Join the
  support surfaces and correct plate slopes before adding small controls.
- P1 review-evidence issue: front framing is not calibrated. The bow occupies
  about60% of image width and has a12%-height top margin; the target nearly fills
  the width and crops the bow top. The display row begins around45% image height
  versus about33% in the target. Focal length/distance and camera elevation/pitch
  must be jointly fitted before attributing these screen-space errors to geometry.
- P1 review-evidence issue: the oblique view is from the opposite lateral side.
  Its panel lies upper-left and seat lower-right, whereas the target's panel is
  upper-right and seat lower-left. Change the camera lateral offset, not the
  aircraft handedness; preserve the actual left throttle/right console layout.

Camera calibration should first establish the whole-bow horizontal fill, then
the bow/panel/seat vertical landmarks using pitch/elevation, then check relative
perspective scaling of the seat and display row. A longer lens/farther camera
can reduce excess near-console enlargement, but the final image landmarks—not
the chosen lens number—must establish the match. Do not hide geometry problems
by cropping them from the reference review.

### Revision6 third reference-angle review (19:34)

Both front and oblique images inspected. **Needs changes**, with a bounded next
pass rather than more wholesale rebuilding. Upper structure is materially closer:
three displays form a compact row, HUD is stepped, and its projected width is
about0.41of the three-bezel span versus roughly0.38in the reference. Oblique
camera handedness is corrected; large screen-occluding shoulder blocks are gone.

Three remaining priorities:

1. Shorten the visually stretched lower cockpit. The long empty bridge between
   the pedestal and stick is unlike the target, where the stick sits directly
   below the center pedestal and the broad U-notched seat fills the lower third.
   Bring stick/seat forward and shorten that bridge. Current front camera looks
   down about49degrees and crops the top of the HUD; use a less top-down reference
   angle (roughly30–38degrees as a starting point) and include the full lens.
   The result, not the suggested angle, must match the key landmarks.
2. Close the remaining light-background wedges visible behind the left legbay
   and console shoulder in the oblique view. Dark recesses must be real enclosed
   cavities, without exterior/studio background showing through joints.
3. Break up the glaring blank shoulder/console surfaces with the reference's
   distinct front-left guarded switches/knobs, front-right broad information
   plate, and closely fitted asymmetric console groups. Exact switch duplication
   is not required for this prototype, but sparse floating generic plates fail.

A subsequent prototype geometry pass is possible once these structural findings
are visibly resolved. Fine hardware, exact labels and subtle wear can remain
documented limitations; gross seat/pedestal depth or open shell defects cannot.

### Revision6 final candidate geometry review (19:39)

Stark inspected fresh frontal, oblique and pilot previews for GLB hash
`13a0e9c475ea40dc73886cf2606db2f1446006f2c3fb3eeec5baae4d05d7d0b5`.
Verdict: **pass to native validation as revised prototype geometry**. This is
not an exact-photo or final integrated acceptance verdict.

The long empty bridge is removed: stick meets the compact pedestal and the broad
U-notched seat is visible. The large light-background wedges in the oblique view
are closed. Sloped shoulders now connect to populated continuous consoles; the
compact display row, stepped HUD housing and noncircular shield lens remain.
The separate pilot view preserves all three display faces and a clear optical
sightline. These resolve the major structural findings from the prior rounds.

Remaining limitations/checks:

- Reference cameras remain more top-down than the supplied photos; the front
  render includes a headrest across the lower cushion. Precise pixel-match claims
  are unsupported. This is a closer reference-informed shape, not a near-identical
  photo reproduction.
- Equipment and sculpting remain simplified, including sparse control clusters,
  stepped generic button geometry, cushion contour and optical support detailing.
- Thin light slits are visible at the outer footwell/shoulder joints near the
  pilot image bottom. Inspect them in native integration: the surrounding airframe
  may enclose them; if exterior light leaks persist, close those local seams.

Proceed to native camera, normal-game and performance validation. No further
wholesale Blender iteration is requested before inspecting that evidence.

### Revision6 native runtime image review (19:42)

Stark independently inspected all three fresh native `detail/camera-*.png` images
and read `detail/build.json` plus `detail/runtime-report.json`. Build hash matches
`13a0e9c475ea40dc73886cf2606db2f1446006f2c3fb3eeec5baae4d05d7d0b5`; all31 runtime
checks are true. UE5.8.4, EurofighterCockpitStudy, native3440x1440, original pilot
relative eye(650,0,122.5)cm, pitch-4, vertical FOV64.011, Scattered clouds.

Verdict: **qualified runtime visual pass**, not exact-photo acceptance.
The pilot view has no visible exterior/sky leak in the lower footwells, no
duplicate bow and no near-clip blocker. Three screens and the shield combiner
remain visible; the right attitude display uses the corrected blue/brown art.
Chase shows the complete attached aircraft. The forward canopy mount now includes
a broad dark coaming band along roughly the lower15% of the image; the nose and
horizon remain clear, so this view is usable, though it is not interior evidence.

The upper coaming and HUD housing read tan/bright under this native lighting,
unlike the reference's black finish and the dark studio preview. This is a
remaining material/lighting mismatch, not a controls or camera blocker. It must
not be reframed as photographic-fidelity approval. The task appropriately remains
in user visual review; the previous photo-camera and simplified-equipment limits
still apply. Updated revision6 performance measurements are pending separately;
revision5 timing figures must not be reported as revision6 results.

## Additional user detail references — active refinement

Stark visually inspected the five images supplied in the later user turn:

1. Current Unreal screenshot (`codex-clipboard-d136f028-f8ba-4f4b-909d-e4a20ddd9fca.png`):
   evidence of the current flat-topped combiner and tan native surface response.
2. Daylight seated HUD close-up (`codex-clipboard-6c76074b-d972-4757-9b56-196a80b670d5.png`):
   primary optical-shape/depth reference; appears to be a close-up of the official
   Eurofighter flight photo previously inspected.
3. Night cockpit (`codex-clipboard-98caf3bc-ab0e-46cf-b74a-b74e4fc833a1.png`):
   primary supporting silhouette/illumination reference; source not independently
   identified, so no claim about exact aircraft configuration or screen functions.
4. Simulated-looking cockpit (`codex-clipboard-c960d113-819e-4074-9dcb-b748b2d99511.png`):
   secondary illustration only, not authoritative geometry or material evidence.
5. Watermarked oblique photograph (`codex-clipboard-5cb32910-66c4-481e-a8e8-0a5ce71db135.png`):
   same target composition as `user/oblique.png`; primary support/tray depth cue.

The daylight close-up refines the earlier shield description. Its **top edge is
continuously arched**, with rounded oval shoulders, not the long flat plateau in
revision6. The reviewer accepts responsibility for making that distinction
explicit: a generic rounded rectangle does not meet this new close-up evidence.

### Bounded detail priorities and acceptance

1. **Combiner contour:** continuously curved oval upper apex/shoulders, broad
   width roughly1.3–1.4times height in the supplied day projection, tapering lower
   bowl. Preserve a fine upper edge and selectively thicker lower optical edge;
   avoid a uniformly heavy wire or the flat rounded-rectangle plateau. Inspect
   the whole silhouette in pilot and oblique renders.
2. **Support assemblies:** shaped paired arms with an angular lower kink,
   substantial dark structural section/lighter inner face, broad upper clamps,
   and circular base pivots. They should visibly support the lens rather than
   read as two skinny curved tubes. Do not obstruct the exterior sightline.
3. **Layered optical tray:** shallow polygonal horizontal optical surface behind
   the top five-window strip, raised rim, stepped plates and restrained screw
   row. The oblique render must show this depth instead of a blank coaming shelf.
4. **Housing/readouts:** thin framed top keys, recessed dark center readout,
   side bezel keys and layered side detail; avoid chunky repeated cube buttons.
   Retain the now-compact three-display row and corrected lower cockpit geometry.
5. **Native material distinction:** graphite coaming/HUD hardware must remain
   visibly darker than the gray display bezels under the same light. Investigate
   the tan appearance as import/material behavior rather than claiming it is
   automatically a realistic warm-light effect.

Night lighting is supporting evidence for restrained green legends/keys and any
scoped illustrative HUD glyphs; it does not justify overpowering daytime emission
or functional-avionics claims. The simulator-like fourth image cannot override
the photographed silhouettes. New geometry/material renders are pending, and the
earlier runtime pass does not constitute approval of these refinements.

### Revision7 Blender detail gate (23:24–23:25)

Stark inspected the fresh pilot, frontal and oblique previews against the new
daylight/night/oblique references. Verdict: **clear for native detail validation**.
The upper lens contour is continuously oval rather than flat-topped; upper/lower
edge thickness is differentiated. Clamps, pivots and substantial shaped support
sections establish a structural assembly. The optical tray's layered plates,
rim and screw strip are visible in the elevated/oblique views. Five shallow
framed keys and a dark recessed center readout improve the housing's depth.
No new critical geometry blocker is visible, and lower cockpit geometry is stable.

The supports remain more angular/faceted than the photographed curved brackets;
fine optical/hardware shape and exact camera projection are still approximate.
These are bounded prototype limitations, not reasons for another wholesale pass.
The tray is already legible, so no further coaming lowering was requested.
Native matte graphite/paint separation and all three camera views still require
actual revised renders before integration sign-off.
