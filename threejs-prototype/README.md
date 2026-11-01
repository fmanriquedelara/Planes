# Stratos — Three.js flight graphics prototype

A separate browser experiment for PlanesRace. The focus is an atmospheric pilot's
view over rolling countryside and a coast, using an existing detailed Gripen
cockpit, procedural terrain, an animated river/ocean, shaded volumetric cloud
banks and approximate moving cloud shadows. It does not modify or replace Godot.

## Run

Use Node.js 20.19+ or 22.12+ (validated here with Node 25.9.0) and a browser with
WebGL 2 and hardware acceleration.

```powershell
cd C:\Repositories\Planes\threejs-prototype
npm ci
npm run dev
```

Open http://127.0.0.1:5174. `npm run build` produces `dist/`; `npm run preview`
serves that build at http://127.0.0.1:4174. Serve through HTTP, not `file://`.
Dependencies are pinned in `package-lock.json`; assets are local after install.

## Controls

- Drag the scene to look; double-click to centre the view.
- Arrow keys bank/pitch; W/S adjust throttle. This is an arcade visual flight
  model, not a validated aerodynamic simulation.
- Space or Pause stops flight. R resets flight. C toggles pilot/exterior views.
- H hides the interface. The fullscreen button uses the browser's fullscreen API.
- Scene controls adjust FOV, exposure, cloud cover and quality. Golden coast,
  clear daylight and above-cloud presets change lighting, atmosphere and altitude.
- On touch devices, drag to look and use the toolbar for scene/camera controls;
  manual flying currently needs a keyboard. Autopilot continues without one.

The default is Gripen, eye `(0, 0.65, -5.03)`, FOV 68°, near/far 0.1/100000.
The renderer uses reversed depth when `EXT_clip_control` is available and a
conventional depth buffer otherwise. Reference screenshots are art direction,
not image backdrops. `?model=eurofighter` selects the alternate repository model.

## 120 FPS target mode

The default quality profile is **120 FPS target · Adaptive**. It aims at an
8.33 ms frame budget, rather than forcing a display refresh rate or capping the
browser at exactly 120. Browser animation follows the available display cadence;
a 60 Hz display cannot present 120 distinct frames per second.

- Performance uses 28 cloud ray steps and one optical-shadow sample, with the
  same cloud coverage/layout as High. Terrain draws 131,072 instead of 524,288
  triangles. High restores 80 cloud steps and all terrain detail.
- Render pixel ratio starts at at most 1 and adapts between 0.6 and 1, using
  asynchronous GPU timings where available. The floor protects legibility;
  reaching the floor does not guarantee the frame target. High never adapts.
- Performance uses 1024-pixel cockpit shadow maps refreshed up to 30 times per
  second; High uses 2048 at up to 60. Paused maps are cached. Their projection
  still follows aircraft translation every frame. Banking/preset changes update
  shadows, with bounded latency between scheduled redraws.
- Telemetry updates at 5 Hz; simulation/camera input still runs each animation
  frame. The FPS display reports observed cadence separately from the target.

GPU timing is optional; without its extension, adaptation uses active CPU
update/render work. It never downscales solely because a monitor supplies 60 Hz
callbacks. No native sustained 120 Hz result is claimed from a headless test.

## Validation and capture

With the dev server running and Chrome installed:

```powershell
npm run capture
node tools/verify.mjs
node tools/verify-budget.mjs
npm run benchmark
```

Capture launches a separate headless Chrome process without desktop interaction.
It saves a 1600x1000 PNG and JSON containing the actual camera, browser, renderer
state and errors. URL `?capture=1` freezes flight for review. Example:

```powershell
node tools/capture.mjs "http://127.0.0.1:5174/?capture=1&model=gripen" artifacts/prototype.png
```

For a nonstandard Chrome path, set `CHROME_PATH`. `PLAYWRIGHT_MODULE` optionally
selects an existing Playwright installation for the capture helper. The verification
helper uses the project's pinned Playwright and the installed Chrome channel.
Browser QA checks 22 behaviours including model loading, actual cloud draw-call
changes, settings, camera switching/look, advancing flight, reset and mobile layout.
Build and integration checks passed; captured pilot, exterior and mobile views
were inspected. FPS shown during a short capture is not a benchmark.

`npm run benchmark` saves `artifacts/benchmark-normal.json` using normal headless
scheduling. `npm run benchmark -- --uncapped` uses a separate browser with VSync
and frame-rate limiting disabled as a throughput diagnostic only. It does not
change normal application settings or establish physical screen refresh.
Reports record the actual GPU, viewport, adaptive scale, profile, raw GPU/CPU
sample counts, frame-time percentiles and over-budget rates. CPU active time
and GPU draw time overlap and must not be added together. Timer warm-up/disjoint
periods are excluded from draw timings but included in callback intervals.
Six budget checks cover display-limited callbacks, overload, GPU warm-up,
resolution limits and manual quality behaviour.

Local normal-scheduling results (RTX 4060 Ti, Chrome 156, short flying runs):
1080p GPU draw time averaged 17.14 ms in High versus 6.91 ms in Performance at
pixel ratio 1. Performance's p95 was 8.77 ms, with 5.56% of GPU samples exceeding
8.33 ms. Normal headless cadence stayed near 100 FPS, so native sustained 120 Hz
has not been verified. At a 4K viewport, adaptive ratio reached 0.6 (2304x1296
internally), yet GPU time still averaged 9.88 ms. That case remains over budget.
Full results and the separately labelled uncapped diagnostic are in `artifacts/`.

## Structure

- `src/main.js`: renderer, pilot camera, approximate flight and controls.
- `src/render-budget.js`: asynchronous GPU timing and adaptive render resolution.
- `src/cockpit.js`: repository model loading, materials and display UV correction.
- `src/legacy-materials.js`: approximate legacy specular/glossiness conversion.
- `src/displays.js`: generated navigation and flight/system displays.
- `src/world.js`, `src/world-shaders.js`: terrain, atmosphere, water, clouds and
  approximate projected cloud shadows.
- `public/assets`: copied repository aircraft, not new external downloads.
- `public/credits.html`: aircraft attribution, license links and modification notes.
- `tools`: headless capture and functional browser validation.

## Current limits

This is a visual prototype, not photorealistic scenery or a finished racing game.
Terrain is procedural rather than surveyed imagery; fields and cloud lobes can
still reveal their generated patterns. River geometry/hydrology, reflections and
cloud shadows are approximations. Cloud/terrain intersections and unlimited-world
streaming are not complete. Canopy mirrors use static environment reflections;
the generated MFDs illustrate flight data rather than authentic Gripen avionics.
The legacy material conversion approximates the original BRDF. Large existing
GLBs (about 40 MB Gripen and 14 MB Eurofighter) affect startup and memory.
The build currently reports a nonblocking large Three.js bundle warning.

The Gripen's embedded credits identify ngkoret, CC BY 4.0; attribution travels in
the build's credits page. The alternate Eurofighter has separate noncommercial/
share-alike provenance in the repository's original download. See the credits
before republishing aircraft assets. No online hosting was configured.
