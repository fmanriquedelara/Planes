# Photo comparison workspace

`comparison.blend` is a separate inspection copy of revision 7. It does not alter
the cockpit geometry, original `.blend`, or game export. Switch scenes using
Blender's scene selector: **Compare front**, **Compare oblique**, **Compare hud-day**.
Each scene opens through its reference camera, with the original photograph
packed as a camera background at **50% opacity / Front**. Camera Properties →
Background Images controls its opacity. Numpad 0 enters the active camera view.

Each view has three PNGs: `*-reference.png`, `*-model.png`, and `*-overlay.png`.
The overlay composites the cyan model at 35% over the unretouched photograph.
Reference watermarks and screenshot UI remain intact. The transparent model PNG
can be used for any opacity in `review.html`. The solid diagnostic render omits
transparent glass panes, while retaining their structural outlines; it is not a
beauty render or Unreal material evaluation.

Camera estimates use manually selected shared landmarks on the existing model
and photos. They are comparison aids, not survey calibration. A camera cannot
correct discrepancies in the model itself; visible misalignments are preserved.
See `camera-fit.json` for poses, landmarks and fit residuals and
`comparison-report.json` for the exact source hashes. No geometry is warped or
individually scaled to hide discrepancies.

The first inspected overlays expose substantial remaining disagreement: the
oblique display row/top bar fits reasonably while the bow and combiner project
too high. The initial frontal instrument-only fit was rejected because its low
camera exposed rear-seat structure across the instruments. The HUD close-up fits the lens locally, but the clamp height
and lower casing differ. Its lens landmarks were used to fit that camera, so
the close contour overlap is **not independent validation of the lens shape**.
Oblique and HUD-day fit RMS values are approximately 27.5 and 14.9 pixels on their
original image resolutions. These describe selected landmarks, not fidelity.
The front view now uses an independently reviewed elevated camera: location
(-0.35,0,1.0)m, target(0.65,0,-0.22)m, 42mm horizontal36mm sensor, shiftY -0.09,
horizontal FOV46.4°. It shows the cushion and instruments without hiding the seat.
Its original instrument-anchor RMS is30.3px: worse numerically than the rejected
7.8px fit, but physically more useful. Frame width and panel/seat proportions
remain mismatched. Trials and parameters live in camera-review; the previous
scene and overlays are archived under artifacts/initial-camera-fit.
These overlays are a diagnostic workspace, not a realism pass.

Reproduce from the repository root with Blender 3.6:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 3.6\blender.exe' -b --factory-startup --python assets/eurofighter-cockpit/comparison/build_comparison.py
& 'C:\Users\fmanr\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' assets/eurofighter-cockpit/comparison/compose.py
```

Photos are user-provided reference evidence. They are not cockpit textures and
this workspace does not grant redistribution rights to the reference images.
