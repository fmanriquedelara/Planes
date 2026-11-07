# PlanesRace — Unreal cockpit prototype

## Separate Eurofighter cockpit study (UE-008)

Revision 6 corrects the geometry against the user's frontal and oblique photos.
Stark cleared its major structural corrections and native testing; exact photo
fidelity is not signed off. Reference camera poses and fine equipment remain
approximate. See UE-008 for the current review and evidence.

The new cockpit has its own map `/Game/Maps/EurofighterCockpitStudy` and assets
under `/Game/EurofighterCockpitStudy`. The original Gripen remains the default.
The cockpit's editable Blender source, GLB export, builders, textures and metrics
are in `../assets/eurofighter-cockpit/`. It has 161,292 triangles and 12 merged
material sections, with original illustrative display art and painted labels.
This is a reference-informed visual cockpit, not functional avionics or a
manufacturer-accurate engineering model.

From the repository root:

```powershell
.\unreal-prototype\Scripts\Run-CockpitStudy.ps1 -Mode Play
.\unreal-prototype\Scripts\Run-CockpitStudy.ps1 -Mode Build
.\unreal-prototype\Scripts\Run-CockpitStudy.ps1 -Mode Test
.\unreal-prototype\Scripts\Run-CockpitStudy.ps1 -Mode Profile
```

The helper defaults to 3440x1440, 100% internal screen percentage and dynamic
resolution off. `-Width`, `-Height`, and `-ScreenPercentage` are explicit options.
Use `-Variant baseline` to build, run or measure the original Eurofighter in
`/Game/Maps/EurofighterCockpitBaseline`. Both maps inherit the existing environment,
camera exposure and native flight/menu controls. On a fresh checkout compile
the runtime and build the default environment first using the main helper below.
Play is an uncooked game through UnrealEditor, not a packaged executable.

Build snapshots its GLB inputs with hashes, uses a content-addressed cockpit asset
namespace to avoid stale imported materials, asserts the active destination map,
and checks the default map's hash before and after. A separate airframe fitting
derivative removes only the obsolete canopy bow; original model files are retained.
The cockpit uses a simple transparent optical material without refraction and a
masked label material with no mipmaps for small legend clarity. Fine labels may
still shimmer in motion; those settings are a deliberate current tradeoff.

Test captures cockpit/chase/canopy views with screen messages enabled and checks
the existing controls. Profile uses Unreal's CSV profiler after 360 warmup frames,
captures 3,000 straight-flight frames with VSync/frame cap off, and exits. Run
baseline and detail sequentially with Blender renders and other GPU work idle.
Results are under `artifacts/ue008/{baseline,detail}`. Summarize them with:

```powershell
python .\unreal-prototype\Scripts\summarize_cockpit_profile.py
```

These are normal-game offscreen Development measurements, not MRQ stills or
long-run packaged-game performance guarantees. See `../tasks/UE-008.md` for
review results, exact conditions and measured results.

The revision-6 3,000-frame native samples averaged 56.51 FPS for the original
cockpit and 56.92 FPS for the rebuild: effectively similar within run variation
(mean difference -0.128 ms). The rebuild averaged 67.09 FPS with 85% internal
rendering and TSR at the same 3440x1440 output. For that
smoother tested option:

```powershell
.\unreal-prototype\Scripts\Run-CockpitStudy.ps1 -Mode Play -ScreenPercentage 85
```

Reduced-resolution evidence is stored separately under `artifacts/ue008/detail-85pct`.
These figures describe short straight-flight tests on the RTX4060Ti8GB at Epic
settings; they are not a locked frame-rate guarantee.

A separate Unreal Engine **5.8.4** graphics study using the repository's detailed
SAAB JAS 39 Gripen as the default aircraft. Vision builds the scene, Stark reviews rendered evidence,
and Milu coordinates the work in [UE-001](../tasks/UE-001.md).

This prototype has a small flight model ported from Godot and a pause/exit menu.
Godot and Three.js remain separate projects.

## Open and run

Open `PlanesUnreal.uproject` in Unreal Engine 5.8.4. The startup map is
`/Game/Maps/CockpitStudy`; `PilotEye` is configured as player 0's camera.
Alternatively, from this repository:

```powershell
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Editor
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Play
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Play -NativeResolution -Fullscreen
```

`Play` runs the uncooked map through the installed editor executable in game
mode. It is not a packaged Windows build.

## Flight controls

The plane moves forward automatically at an initial 100 m/s. Click the game
window if it does not have keyboard focus.

| Input | Action |
| --- | --- |
| Up / Down | Pitch nose up / down |
| Left / Right, or A / D | Bank left / right |
| Q / E | Turn left / right |
| W / S | Engine / brake |
| R | Reset starting pose and speed |
| Esc | Pause and open the menu; press again to resume |
| Resume Flight | Close the menu and resume movement |
| Exit Prototype | Quit the game window |

The gamepad bindings follow `Godot/project.godot`.

| Gamepad | Action |
| --- | --- |
| Left stick | Pitch and roll |
| Right bumper | Yaw right |
| Right / left triggers | Engine / brake |
| Right stick left/right and up | Look sideways and up |
| Y / triangle | Cycle the available views |
| Hold A / cross | Play the Godot gun sound |

Stick and trigger dead zones are 0.2 and 0.5 respectively. Godot defines no
left-yaw gamepad action. Keyboard Q provides left yaw.

### Flight model source

The equations are in `Source/PlanesUnreal/FlightModel/FlightModel.cpp` and the
plain C++ state and inputs are in `FlightModel.h`. The model ports thrust and
drag, gravity projected into the aircraft axes, speed-dependent angular-rate
commands, quaternion attitude and wing deflection state from `Godot/Plane.gd`.
The wing deflection state is available to callers. Unreal does not animate its
mesh from those outputs. The gun control plays audio from the original Godot
asset.

`PlanesFlight::Step(state, inputs, seconds)` uses metres, seconds, m/s and
radians/s in the source model's axes. It has no Unreal or Godot dependency.
The Unreal pawn supplies controller commands and gust samples, steps at 120 Hz,
and converts the pose to Unreal centimetres and axes. A future FMU wrapper can
own the same state and call the same function. FMI packaging is separate work.

## Camera and weather controls

In the detailed Eurofighter study, press **B** or click **Cockpit Bow** in the
pause menu to toggle the canopy bow between opaque and nearly transparent in
the cockpit camera. The chase and canopy mount retain the opaque bow.

| Input | Action |
| --- | --- |
| C | Cycle cockpit, chase, canopy-mounted views |
| 1 / 2 / 3 | Select cockpit / chase / canopy mount directly |
| Hold right mouse + move mouse | Look around |
| I / K | Move camera forward / backward |
| J / L | Move camera left / right |
| U / O | Move camera up / down |
| Home | Reset the active camera's position, look and FOV |

The cockpit view keeps the calibrated pilot eye. Chase sits behind and above the
actual aircraft. The Gripen canopy view sits higher and forward near the glass,
looking down with a wider lens while retaining instrument context. The optional
Eurofighter uses a farther-forward windscreen/nose view to clear its opaque arch.
Mounts are aircraft-specific; neither is an exact reproduction of the reference.
Movement is bounded near each mount and does not move the plane. Home recovers
the default view if a manual offset encounters model geometry.

Esc opens camera-selection buttons, vertical FOV adjustments in 5-degree steps
(40–100 degrees), and Clear / Scattered / Broken / Overcast cloud presets. FOV is
converted to CineCamera focal length and preserves vertical framing on ultrawide.
FOV and offsets are remembered per camera for the session; Home restores that
view's defaults (pilot approximately64, chase60, canopy84 degrees vertical).
Cloud cover is shared across cameras and changes native volumetric material
coverage, density and cloud-type mix. Default is Scattered. These settings reset
on a new run. Camera motion is suspended while the menu is open.

## Screen sizing

For this machine's **3440x1440** monitor, `-Ultrawide` selects that resolution.
`-NativeResolution` reads the primary monitor instead. `-Fullscreen` selects a
borderless game view; Alt+F4 closes it. Custom dimensions override the preset:

```powershell
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Play -Ultrawide -Fullscreen
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Play -Width 2560 -Height 1080
```

The camera preserves vertical FOV and allows the viewport aspect to change.
Ultrawide adds horizontal visibility rather than stretching the image or cropping
the instrument panel vertically. It does not make the prototype a packaged game.

Menu text uses the engine's runtime Roboto UFont at integer sizes, with text draw
scale 1 and pixel-rounded positions. It is rasterized for the viewport rather than
enlarging the earlier small-font glyphs. The panel and click targets retain their
existing dimensions. For sharpness comparisons, inspect full-resolution images:
chat previews may downscale 3440x1440 captures. See [UE-007](../tasks/UE-007.md).

## Rebuild and capture

```powershell
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Compile
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Build
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Capture
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode GameCapture -Ultrawide
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Test -Ultrawide
```

On a fresh checkout, **Compile first**, then Build, then Play. The native runtime
DLL is generated under ignored `Binaries`; Python Build prepares scene assets
and cannot replace compiling runtime code. Compile also follows C++ changes;
Build is needed when changing the scene/bootstrap. Close this prototype's game
window before recompiling a loaded DLL.

Required tools: UE 5.8.4, supported VS 2022 C++ Build Tools (validated MSVC
14.44.35229) and Windows SDK 10.0.22621.0. Build Tools 17.14 is installed alongside
the older IDE at `D:\UnrealBuildTools2022`. It is discovered by UnrealBuildTool.
The runtime disables shared PCH generation and Compile uses `-NoUBA` to keep
build caches modest. On this machine, the ignored project `Intermediate` folder
is a junction to `D:\PlanesBuildCache\unreal-prototype\Intermediate`, after C:
ran out of space during the first compile. This contains only generated build
data; it is not source and is not required on other machines.

Override `-EngineRoot` if Unreal is installed somewhere other than
`C:\Program Files\Epic Games\UE_5.8`.

The build script imports `../Shark 600/saab_jas_39a_gripen_detailed_cockpit.glb`,
creates native Unreal materials, atmosphere, cloud and environment actors, and
saves the map, native moving rig, camera sequence and Movie Render Queue preset.
Python is used for editor asset preparation, not runtime gameplay. The native
module in `Source/PlanesUnreal` owns flight, input, pausing and the Canvas menu.
The builders import the Godot gun sound into `Content/StudyAudio`. Generated
comparison maps, imports, renders and comparison scenes are ignored by Git.
Build the separate cockpit study after a fresh checkout before selecting Play.

Capture runs Movie Render Queue on the real GPU with `-RenderOffscreen` and
does not open an interactive editor window. Output is
`artifacts/cockpit.0000.png`, with logs in `Saved/Logs`. The build step uses
`-NullRHI` only for asset preparation; that step cannot produce rendered evidence.
Initial shader compilation and derived data generation can take time and disk
space. Generated caches, logs and captures are ignored by Git.

`GameCapture` runs the normal game renderer offscreen, waits 180 frames, then
uses `Shot SHOWUI` with screen warnings enabled. It exits after 210 frames and
saves `artifacts/game-WIDTHxHEIGHT.png`, a matching log and JSON metadata;
its working log is `Saved/Logs/GameCapture.log`. The helper checks PNG dimensions.
This is the appropriate startup-warning and viewport-aspect check. MRQ and
HighResShot can suppress screen warnings and cannot substitute for that check.
Resolution options apply to Play, GameCapture and Test. MRQ Capture retains its saved
1600x1000 output preset. Neither capture mode measures sustained performance.

`Test` exercises PlayerController key input and HUD button hitbox dispatch in a
separate offscreen game process. It captures the paused menu and reset flight
view, checks the report, and exits through the menu's Exit handler. Results are
under `artifacts/runtime-WIDTHxHEIGHT`. The extended suite checks camera input,
FOV projection, cloud material settings and the original flight/menu behaviors.
Milu/Stark also inspect the actual menu and camera captures. This verifies the
engine input route, not physical OS mouse clicks or Alt+Tab behavior. Only the
explicit test flag bypasses the offscreen focus guard. Normal play uses viewport
focus and clears held inputs on focus loss.
The extended report includes snapshots with camera pose, vertical FOV and cloud
preset metadata; the launcher checks every listed image is fresh. Automated input
checks cannot prove a camera is unobstructed: actual image review is required.
The extended suite passed31 checks at both tested resolutions. The final forward
mount refinement was rendered/rechecked at3440x1440. Stark's feature and separate
image-quality critiques are recorded in [UE-005](../tasks/UE-005.md): functionality
passes, while terrain detail, cockpit texture fidelity and overcast lighting
still need substantial improvement.

## Review conditions and limits

- Engine: 5.8.4, changelist 58902052; Direct3D 12 / Shader Model 6.
- Validated GPU: NVIDIA RTX 4060 Ti 8 GB, driver 610.88.
- Still capture: 1600x1000, four temporal samples, 48 engine warmup frames.
- Movie Render Queue applies Cinematic scalability during capture, confirmed in
  the render log. Normal game startup uses a different scalability context;
  this still is not a real-time game performance measurement.
- Gripen pilot eye: (503, 0, 180065) Unreal centimetres; pitch -4 degrees,
  yaw 0. External model scale 1.0. Camera mounts are selected for the aircraft.
- Lens: 18 mm, 36x22.5 mm sensor, approximately 90-degree horizontal and
  64-degree vertical FOV. This is close to, but not identical to, the browser's
  68-degree vertical FOV.
- Fixed physical exposure: ISO 100, f/8, shutter 1/128 s (EV100 13).
- Lumen lighting/reflections and Unreal volumetric clouds are visual-study
  settings. Aircraft Nanite is disabled for compatibility with imported materials.

Lumen uses software tracing with generated mesh distance fields. Physical camera
EV100 remains 13; cached-lighting pre-exposure is configured for that exposure
range. Rendering-warning checks and ultrawide review are recorded in
[UE-002](../tasks/UE-002.md).
Normal-game 1600x1000 and 3440x1440 captures were inspected by Milu and Stark:
the reported Lumen and cached-lighting exposure warnings are resolved, and the
ultrawide view preserves vertical framing. Unrelated editor initialization
warnings remain in logs; these checks do not establish a frame-rate result.

Actual renders exposed and helped correct initial exposure and material-import
problems. Review history and remaining findings are recorded in UE-001.
Existing cockpit texture fidelity and simplified environment content remain
limits. Illustrative display graphics are not real flight data.

The default Gripen retains authored physical panels and buttons, with prototype
green radar display material overrides. No new physical cockpit buttons or
functional avionics were modeled. Custom additions are the flight/menu code and
control hints, plus scene lighting and material/glass adjustments. Eurofighter
assets remain in Content; the bootstrap's `AIRCRAFT` setting can select it before
rebuilding. Its authored panels are retained without Gripen radar overrides.
Both models' provenance and licenses are in CREDITS.md. Gripen was restored as
default because its instrument textures are visibly sharper.

Movie Render Queue stills are **offline visual evidence**. They do not establish
real-time frame rates, native 120 Hz, or superiority over the other prototypes.
Standalone CPU/GPU timing, long-run motion quality and a packaged build remain pending.
No DLSS plugin is installed or required by this prototype.

See [CREDITS.md](CREDITS.md) for asset attribution and changes.
