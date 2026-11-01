param(
    [Parameter(Mandatory = $true)][string]$GodotPath,
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\artifacts\cockpit.png'),
    [ValidateSet('1280x720', '1920x1080')][string]$Resolution = '1280x720',
    [ValidateSet('scene', 'inside-lower', 'inside-upper')][string]$CaptureView = 'scene'
)

$ErrorActionPreference = 'Stop'
$enginePath = (Resolve-Path -LiteralPath $GodotPath).Path
$projectPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\Godot')).Path
$capturePath = [System.IO.Path]::GetFullPath($OutputPath)
$captureDirectory = [System.IO.Path]::GetDirectoryName($capturePath)
New-Item -ItemType Directory -Path $captureDirectory -Force | Out-Null
if ($projectPath.Contains('"') -or $capturePath.Contains('"')) {
    throw 'Paths containing quotation marks are unsupported.'
}
$captureArguments = @(
    '--path', ('"' + $projectPath + '"'),
    '--script', 'res://tools/capture_cockpit.gd',
    '--position', '-32000,-32000', '--resolution', $Resolution,
    '--audio-driver', 'Dummy', '--fixed-fps', '60',
    '--log-file', ('"' + $capturePath + '.engine.log"'),
    '--', ('"' + $capturePath + '"'), $Resolution, $CaptureView
)
# The GPU renderer needs the Windows display driver. Headless uses a dummy renderer.
# Use a hidden launch hint, an off-screen position, and an unfocusable root window
# in the capture script; never automate or change the editor's window.
$captureProcess = Start-Process -FilePath $enginePath -ArgumentList $captureArguments `
    -WorkingDirectory $projectPath -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput ($capturePath + '.stdout.log') `
    -RedirectStandardError ($capturePath + '.stderr.log')
if (-not $captureProcess.WaitForExit(60000)) {
    $captureProcess.Kill()
    throw 'Capture timed out after 60 seconds; the separate capture process was stopped.'
}
$captureProcess.Refresh()
if ($captureProcess.ExitCode -ne 0) {
    throw "Godot capture failed with exit code $($captureProcess.ExitCode). See $capturePath.stderr.log"
}
if (-not (Test-Path -LiteralPath $capturePath)) {
    throw "Godot did not create $capturePath. See capture logs."
}
Write-Output $capturePath
