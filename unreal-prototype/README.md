# PlanesRace — Unreal cockpit prototype

A separate Unreal Engine **5.8.4** graphics study using the repository's detailed
SAAB JAS 39 Gripen. Vision builds the scene, Stark reviews rendered evidence,
and Milu coordinates the work in [UE-001](../tasks/UE-001.md).

This first milestone is a cockpit visual prototype. It does not yet implement
interactive flight controls, aerodynamic physics, racing or working avionics.
Godot and the Three.js prototype remain separate.

## Open and run

Open `PlanesUnreal.uproject` in Unreal Engine 5.8.4. The startup map is
`/Game/Maps/CockpitStudy`; `PilotEye` is configured as player 0's camera.
Alternatively, from this repository:

```powershell
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Editor
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Play
```

`Play` runs the uncooked map through the installed editor executable in game
mode. It is not a packaged Windows build. The local installation currently lacks
the Windows SDK needed for packaging; editor rendering works without it.

## Rebuild and capture

```powershell
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Build
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Capture
```

Override `-EngineRoot` if Unreal is installed somewhere other than
`C:\Program Files\Epic Games\UE_5.8`.

The build script imports `../Shark 600/saab_jas_39a_gripen_detailed_cockpit.glb`,
creates native Unreal materials, atmosphere, cloud and environment actors, and
saves the map, camera sequence and Movie Render Queue preset. Python is used
for editor asset preparation, not runtime gameplay.

Capture runs Movie Render Queue on the real GPU with `-RenderOffscreen` and
does not open an interactive editor window. Output is
`artifacts/cockpit.0000.png`, with logs in `Saved/Logs`. The build step uses
`-NullRHI` only for asset preparation; that step cannot produce rendered evidence.
Initial shader compilation and derived data generation can take time and disk
space. Generated caches, logs and captures are ignored by Git.

## Review conditions and limits

- Engine: 5.8.4, changelist 58902052; Direct3D 12 / Shader Model 6.
- Validated GPU: NVIDIA RTX 4060 Ti 8 GB, driver 610.88.
- Still capture: 1600x1000, four temporal samples, 48 engine warmup frames.
- Movie Render Queue applies Cinematic scalability during capture, confirmed in
  the render log. Normal game startup uses a different scalability context;
  this still is not a real-time game performance measurement.
- Pilot eye: (503, 0, 180065) Unreal centimetres; pitch -4 degrees, yaw 0.
- Lens: 18 mm, 36x22.5 mm sensor, approximately 90-degree horizontal and
  64-degree vertical FOV. This is close to, but not identical to, the browser's
  68-degree vertical FOV.
- Fixed physical exposure: ISO 100, f/8, shutter 1/128 s (EV100 13).
- Lumen lighting/reflections and Unreal volumetric clouds are visual-study
  settings. Aircraft Nanite is disabled for compatibility with imported materials.

Actual renders exposed and helped correct initial exposure and material-import
problems. Review history and remaining findings are recorded in UE-001.
Existing cockpit texture fidelity and simplified environment content remain
limits. Illustrative display graphics are not real flight data.

Movie Render Queue stills are **offline visual evidence**. They do not establish
real-time frame rates, native 120 Hz, or superiority over the other prototypes.
Standalone CPU/GPU timing, motion stability and a packaged build remain pending.
No DLSS plugin is installed or required by this prototype.

See [CREDITS.md](CREDITS.md) for asset attribution and changes.
