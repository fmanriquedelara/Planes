# Hidden cockpit render

`capture_cockpit.gd` renders the real flight scene into a 1280x720 or 1920x1080 SubViewport,
checks that the default cockpit camera is active, runs eight gameplay frames,
freezes scene processing, then allows sixteen render frames to settle lighting.
It writes a PNG and adjacent JSON metadata and exits automatically.

Use Godot 4.1 with a real GPU renderer and already imported project assets.
Do not use `--headless` for capture: that selects a dummy renderer. The launcher
must start Godot hidden/offscreen (on Windows, `Start-Process -WindowStyle Hidden`)
as an initial launch hint because script startup occurs after engine window
creation. Godot 4.1 cannot hide its main window, and minimizing stalls rendering
in this setup. The script makes the window unfocusable and positions it offscreen
without hiding or minimizing it, so the GPU render loop continues.

Example engine arguments (launcher supplies the executable and hidden window):

```text
--path C:/Repositories/Planes/Godot --position -32000,-32000 --resolution 1280x720 --fixed-fps 60 --audio-driver Dummy --script res://tools/capture_cockpit.gd -- C:/Repositories/Planes/artifacts/cockpit.png
```

The output argument is optional; its default is `artifacts/cockpit.png` at the
repository root. A supplied path must be absolute and end in `.png`. Failures
exit nonzero; inspect the engine log for the specific cause. The capture creates
no desktop screenshot and requires no desktop interaction. It is a single still,
not a performance or temporal-stability test. For matching comparisons use the
same engine, hardware, launch arguments and scene settings.
Existing gameplay input-action warnings are recorded as a capture limitation;
the capture tool does not change the game's input bindings.

`tools/Render-Cockpit.ps1` at the repository root also accepts `-Resolution
1920x1080`, `-OutputPath <absolute PNG path>` and `-CaptureView inside-lower`
or `inside-upper`. The default capture view, `scene`, uses the saved starting
position. Cloud test views override only the instantiated aircraft altitude to
the chosen volume's centre; they never modify project files. JSON identifies
these test views so they cannot be mistaken for the normal starting scene.
The script seeds random disturbances for repeatable review, but shader TIME and
driver differences still prevent a bit-identical or performance comparison.

Syntax-only check (this may use headless because it does not render):

```text
--headless --path C:/Repositories/Planes/Godot --script res://tools/capture_cockpit.gd --check-only
```
