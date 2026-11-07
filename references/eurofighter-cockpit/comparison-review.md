# Cockpit photo-overlay review

Reviewer: Stark. Date: 2026-11-02. Scope: independently assess the comparison
method and inspect the completed overlays. This task exposes differences; it does
not authorize or require geometry changes or a perfect match.

## Method requirements

- Use the current Blender cockpit unchanged, with one rigid pinhole camera per
  photograph. Camera pose, focal length and framing may be estimated. Do not
  deform the mesh, scale individual parts, mirror the aircraft, or warp separate
  rendered regions to force agreement.
- Preserve original photo proportions, watermark and browser/UI overlays. A
  crop may be displayed only if its crop coordinates are recorded and applied
  consistently. The reference image must not be stretched to fit the render.
- Composite the actual rendered model translucently over the photograph, using
  fixed readable opacity (about35% cyan is appropriate). Show structural edges
  or a companion edge overlay so displaced silhouettes are visible.
- Hiding transparent optical panes in the diagnostic solid layer is acceptable
  if declared; retain the actual lens perimeter/support geometry. Such hiding
  must not be confused with a modification of the source cockpit.
- Record input paths/hashes, camera transform, focal length, sensor/framing,
  output dimensions, opacity, fitting anchors and any hidden diagnostic objects.
- Separate anchor-fit error from withheld check-landmark error. An approximate
  camera fit cannot prove model dimensions or make every residual a geometry error.

## Suggested landmarks

| Reference | Fit anchors | Independent check landmarks | Important ambiguities |
| --- | --- | --- | --- |
|`user/front.png`|Outer bezel corners on all three displays; HUD topbar endpoints/base pivots; lower canopy pivot centers|Combiner apex/side clips/lower edge; upper frame arc; seat U-notch; front console transitions|Elevated viewpoint, unknown lens/crop, top frame cropped; three displays may not be exactly coplanar|
|`user/oblique.png`|Near/far bezel corners; HUD topbar/pivot pair; frame-to-rail joints|Optical tray depth; upper lens contour; near/far shoulder slopes; pedestal/stick relation; seat notch|Unknown camera roll/lens distortion; partial occlusion; perspective makes equal parts appear different sizes|
|`user/detail-pass/hud-day.png`|HUD topbar endpoints/base pivots and visible bezel corners, if reliable|Combiner apex/side clips/lower edge; support kink; tray rim/surface; housing depth|Close, wide-angle, cropped screenshot with UI; strongest for optical assembly, weak for full cockpit pose recovery|

A practical fit need not use every suggested anchor. Record the actual selected
ones and confidence. Avoid selecting only the lens to fit the lens, then treating
its small error as independent proof of fidelity. Likewise, a good display-row
fit does not independently validate that row's dimensions.

## Interpreting differences

- A common shift/rotation/scale across most landmarks suggests camera/framing
  error first.
- Near objects displaced more than far objects may indicate depth/camera-position
  error; focal length and camera distance can trade off.
- A local silhouette difference surviving a plausible shared-camera fit is
  stronger geometry evidence, especially if repeated in multiple photographs.
- Systematic edge bending near image borders may be lens distortion. A pinhole
  approximation should disclose this rather than warp the model to compensate.
- Color/lighting mismatch is expected in a cyan diagnostic overlay and is not
  evidence about final materials. The goal is clear outline/depth comparison.

## Review status

Stark inspected all three completed translucent overlays, `camera-fit.json`, the
comparison builder/compositor, README and HTML review implementation.

Verdict: **pass for diagnostic comparison setup**, not geometry fidelity.
The35% cyan rendering is readable over the photographs; the original watermarks
and browser/UI elements remain visible. The builder loads the current source,
creates camera-only comparison scenes, hides optical panes only for diagnostic
clarity, saves a separate packed `.blend`, and asserts the source file hash is
unchanged. The compositor asserts identical photo/render dimensions and blends
the actual rendered PNG; no per-part image warp or mesh deformation is used.

The HTML review provides view selection and adjustable opacity. Its warnings
correctly identify approximate rigid fitting and the non-independent HUD fit.
Interactive UI execution itself was handled by Milu; Stark inspected its source
and static outputs, not live browser interaction.

## Observed overlays and interpretation

### Frontal comparison

The following describes the **initial, subsequently rejected** front camera.
The instrument row roughly registers, while the overlay makes frame, console
and seat disagreements visible. Selected-anchor weighted RMS is7.80px on499x615.
The fitted lens is effectively110mm at its upper search bound, with a shallow
distant pose. Rear-seat structure projects into the photographed instrument area.
This is a strong sign of camera/geometry ambiguity, not proof that the real
cockpit contains that geometry or that the seat alone has a measured error.
Most selected points lie in the display plane; the HUDbar endpoints retain about
14–16px error. Treat this as an instrument-region comparison, not a recovered
whole-cockpit camera.

### Revised frontal camera review

Stark independently inspected the regenerated front model PNG, translucent
overlay and metadata after the camera agent's rendered trials. Verdict:
**pass for the improved diagnostic camera**. The rear seat no longer projects
across the instruments; the cushion and instrument assembly are visible without
hiding seat geometry.

The revised camera is located(-0.35,0,1.0)m, aimed at(0.65,0,-0.22)m, with42mm
focal length on a36mm horizontal sensor, shiftY-0.09 and horizontal FOV46.4degrees.
It is a whole-cockpit inspection compromise, not a recovered physical photo pose.
Its original selected-anchor RMS is30.31px, worse than the rejected7.80px planar
fit but more useful for seeing the whole cockpit honestly.

Remaining visible offsets include a narrower cyan canopy bow with inset legs,
a somewhat higher/narrower display row, low HUDbar assembly relative to the photo,
and seat/console shape differences. These remain exposed; no extra geometry
transforms are warranted just to reduce the overlay mismatch. Camera uncertainty
and the old anchors' limited scope still prevent dimensional conclusions. No
further camera optimization is required to satisfy this comparison-setup request.

### Oblique comparison

The row and HUDbar roughly overlap, but the model bow/lens rise dramatically
above the photographed ones and the lower assembly/seat also differ. These
offsets are honestly exposed rather than hidden. Selected-anchor weighted RMS
is27.50px on1125x1500, with the right HUDbar anchor about57.67px off. Predominantly
planar screen anchors cannot resolve all depth, lens and pose tradeoffs. The
upper offsets warrant further camera/shape investigation; they are not measured
manufacturer-dimension discrepancies. This view is useful precisely because the
remaining disagreement is obvious.

### Daylight HUD comparison

The lens contour is close locally, but those lens anchors were used in fitting;
this is not independent proof of the lens shape. Selected-anchor weighted RMS
is14.87px on1237x1178. The model clamps sit higher than the photo clamps, and the
lower casing/display assembly extends farther downward in this fit. The browser
overlay obscures part of the image and the original crop/lens are unknown, so
interpret this as a local optical-assembly comparison.

## Delivery boundary

The completed artifacts satisfy the request to see the current model
translucently over reference photographs. They deliberately preserve mismatches.
No new geometry changes or Unreal validation are part of this comparison task.
Do not describe these views as an exact photo match, physically recovered camera,
or a new realism pass. Further model edits should use the differences as leads,
with additional noncoplanar anchors or alternate plausible camera fits first.
