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
