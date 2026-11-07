# Team roster

| Agent | Role | Profile |
| --- | --- | --- |
| Milu | Head of operations; planning, coordination and delivery | [milu.md](milu.md) |
| Stark | Independent graphics quality reviewer | [stark.md](stark.md) |
| Vision | Graphics implementation and photorealism | [vision.md](vision.md) |

Profiles persist in this repository; actual agent sessions are started when needed.
For a new specialist (for example physics), copy `TEMPLATE.md`, agree its remit
with the user, and add it here. Do not assign graphics agents physics ownership.

Task records live in `../tasks/`. The initial visual reference and its interpretation
live in `references/`.

## Unreal launch and evidence

The current Unreal prototype lives in `../unreal-prototype`, separate from Godot
and Three.js. Read [its README](../unreal-prototype/README.md) for launch,
rebuild and capture commands. From the repository root:

```powershell
.\unreal-prototype\Scripts\Run-Prototype.ps1 -Mode Play -NativeResolution -Fullscreen
```

This opens the cockpit directly through the installed UE 5.8 executable in game
mode; it does not require the user to open the editor UI. The user has a
3440x1440 ultrawide monitor. `-Ultrawide` selects that preset, and `-Width` /
`-Height` allow custom dimensions. Preserve vertical FOV when adjusting aspect.

Normal-game warning checks use `-Mode GameCapture`; cinematic MRQ captures do
not prove that normal gameplay has no screen warnings. Verify the target process
and fresh output after launch; sandboxed GUI/GPU starts can fail silently and
may require the execution tool's escalation. Do not stop unrelated UE processes.

The project includes native runtime flight/menu code. A fresh checkout needs
`-Mode Compile` then `-Mode Build` before Play (generated DLLs are ignored).
Use `-Mode Test -Ultrawide` for input/menu regression checks. Controls: arrows
pitch/bank, Q/E yaw, W/S engine/brake, R reset, Esc for the paused Resume/Exit menu.
Flight uses the small model ported from Godot/Plane.gd. The model lives in
`unreal-prototype/Source/PlanesUnreal/FlightModel/`.
The Unreal default aircraft is the SAAB JAS 39 Gripen; Eurofighter assets are
retained as an option. Inspect the current bootstrap aircraft setting and build report when
reporting model identity, camera calibration or source attribution.
Camera controls are C or 1/2/3 for the three views, held RMB to look, I/K J/L U/O
to translate and Home to reset the active view/FOV. Esc includes vertical FOV and
four cloud presets. The native Test report lists comparison images and camera
metadata; inspect those images, not only the boolean checks. See UE-005 for the
canopy-placement correction and Stark's separate image-quality verdict.
