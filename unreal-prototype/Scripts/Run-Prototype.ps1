param(
    [ValidateSet('Build', 'Capture', 'GameCapture', 'Play', 'Editor')]
    [string]$Mode = 'Play',
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [switch]$Ultrawide,
    [switch]$NativeResolution,
    [ValidateRange(0, 16384)][int]$Width = 0,
    [ValidateRange(0, 16384)][int]$Height = 0,
    [switch]$Fullscreen
)

$ErrorActionPreference = 'Stop'
$prototypeRoot = Split-Path -Parent $PSScriptRoot
$projectPath = Join-Path $prototypeRoot 'PlanesUnreal.uproject'
$logsPath = Join-Path $prototypeRoot 'Saved\Logs'
$capturePath = Join-Path $prototypeRoot 'artifacts\cockpit.0000.png'
$editorPath = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$commandPath = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (!(Test-Path -LiteralPath $projectPath) -or !(Test-Path -LiteralPath $commandPath)) {
    throw 'Project or Unreal executable missing. Check the project folder and -EngineRoot.'
}
New-Item -ItemType Directory -Force -Path $logsPath | Out-Null

if (($Width -eq 0) -ne ($Height -eq 0)) {
    throw 'Specify both -Width and -Height together.'
}
if ($Fullscreen -and $Mode -ne 'Play') {
    throw '-Fullscreen is for visible Play mode. GameCapture is offscreen.'
}
if ($Mode -notin @('Play', 'GameCapture') -and
    ($Ultrawide -or $NativeResolution -or $Width -or $Height -or $Fullscreen)) {
    throw 'Resolution options apply to Play and GameCapture. Capture uses the saved MRQ preset.'
}
$viewportWidth = 1600
$viewportHeight = 1000
if ($Ultrawide) {
    $viewportWidth = 3440
    $viewportHeight = 1440
}
if ($NativeResolution) {
    Add-Type -AssemblyName System.Windows.Forms
    $primaryBounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $viewportWidth = $primaryBounds.Width
    $viewportHeight = $primaryBounds.Height
}
if ($Width -and $Height) {
    $viewportWidth = $Width
    $viewportHeight = $Height
}

$unrealArguments = @($projectPath)
$unrealExecutable = $commandPath
switch ($Mode) {
    'Build' {
        $buildScript = Join-Path $PSScriptRoot 'build_study.py'
        $unrealArguments += @('-run=pythonscript', "-script=$buildScript", '-NullRHI',
            '-unattended', '-nosplash', '-nosound', '-NoP4', "-abslog=$logsPath\BuildStudy.log")
    }
    'Capture' {
        $captureStarted = Get-Date
        $unrealArguments += @('/Game/Maps/CockpitStudy', '-game', '-RenderOffscreen',
            '-unattended', '-nosplash', '-nosound', '-NoP4', '-ResX=1600', '-ResY=1000',
            '-LevelSequence=/Game/Cinematics/CockpitSequence.CockpitSequence',
            '-MoviePipelineConfig=/Game/Cinematics/CockpitRender.CockpitRender',
            "-abslog=$logsPath\Render.log")
    }
    'Play' {
        $unrealExecutable = $editorPath
        $windowMode = if ($Fullscreen) { '-fullscreen' } else { '-windowed' }
        $unrealArguments += @('/Game/Maps/CockpitStudy', '-game', $windowMode,
            "-ResX=$viewportWidth", "-ResY=$viewportHeight", '-NoP4', '-nosplash',
            "-abslog=$logsPath\Play.log")
        if ($Fullscreen) {
            $unrealArguments += "-ExecCmds=r.SetRes ${viewportWidth}x${viewportHeight}wf"
        }
    }
    'GameCapture' {
        $captureStarted = Get-Date
        # Each DEFER schedules the remaining command for the following frame.
        # Normal Shot includes screen warnings; HighResShot/MRQ can hide them.
        $shotCommand = ('DEFER ' * 180) + 'Shot SHOWUI filename=PlanesGameCapture -nosuffix'
        $quitCommand = ('DEFER ' * 210) + 'Quit'
        $unrealArguments += @('/Game/Maps/CockpitStudy', '-game', '-RenderOffscreen',
            '-windowed', '-ForceRes', '-unattended', '-nosplash', '-nosound', '-NoP4',
            "-ResX=$viewportWidth", "-ResY=$viewportHeight",
            "-ExecCmds=$shotCommand,$quitCommand", "-abslog=$logsPath\GameCapture.log")
    }
    'Editor' {
        $unrealExecutable = $editorPath
        $unrealArguments += @('-NoP4')
    }
}

if ($Mode -in @('Play', 'Editor')) {
    # Start GUI applications explicitly: PowerShell's call operator can return
    # immediately without setting LASTEXITCODE for a Windows GUI executable.
    $quotedArguments = $unrealArguments | ForEach-Object { '"' + $_ + '"' }
    $gameProcess = Start-Process -FilePath $unrealExecutable -ArgumentList $quotedArguments `
        -WorkingDirectory $prototypeRoot -WindowStyle Normal -PassThru
    Write-Output "Launched $Mode (process $($gameProcess.Id))."
    return
}
& $unrealExecutable @unrealArguments
if ($LASTEXITCODE -ne 0) {
    throw "Unreal exited with code $LASTEXITCODE. See $logsPath."
}
if ($Mode -eq 'Capture') {
    if (!(Test-Path -LiteralPath $capturePath) -or
        (Get-Item -LiteralPath $capturePath).LastWriteTime -lt $captureStarted) {
        throw 'Unreal did not produce a fresh cockpit capture. Inspect Render.log.'
    }
    Write-Output "Cockpit render: $capturePath"
}
if ($Mode -eq 'GameCapture') {
    $freshScreenshot = Get-ChildItem -LiteralPath (Join-Path $prototypeRoot 'Saved\Screenshots') `
        -Recurse -Filter 'PlanesGameCapture.png' -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $captureStarted } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$freshScreenshot) {
        throw 'No fresh normal-game screenshot was produced. Inspect GameCapture.log.'
    }
    $artifactsPath = Join-Path $prototypeRoot 'artifacts'
    New-Item -ItemType Directory -Force -Path $artifactsPath | Out-Null
    $gameCapturePath = Join-Path $artifactsPath "game-${viewportWidth}x${viewportHeight}.png"
    Copy-Item -LiteralPath $freshScreenshot.FullName -Destination $gameCapturePath
    $pngBytes = [System.IO.File]::ReadAllBytes($gameCapturePath)
    $actualWidth = ([int]$pngBytes[16] -shl 24) -bor ([int]$pngBytes[17] -shl 16) -bor
        ([int]$pngBytes[18] -shl 8) -bor [int]$pngBytes[19]
    $actualHeight = ([int]$pngBytes[20] -shl 24) -bor ([int]$pngBytes[21] -shl 16) -bor
        ([int]$pngBytes[22] -shl 8) -bor [int]$pngBytes[23]
    if ($actualWidth -ne $viewportWidth -or $actualHeight -ne $viewportHeight) {
        throw "Capture is ${actualWidth}x${actualHeight}, expected ${viewportWidth}x${viewportHeight}."
    }
    Copy-Item -LiteralPath (Join-Path $logsPath 'GameCapture.log') `
        -Destination (Join-Path $artifactsPath "game-${viewportWidth}x${viewportHeight}.log")
    [ordered]@{
        captured_at = $freshScreenshot.LastWriteTime.ToUniversalTime().ToString('o')
        width = $actualWidth
        height = $actualHeight
        mode = 'Normal game, offscreen, Shot SHOWUI'
        warmup_frames = 180
        screen_messages_suppressed = $false
        cinematic_mrq = $false
        performance_benchmark = $false
        sha256 = (Get-FileHash -LiteralPath $gameCapturePath -Algorithm SHA256).Hash
    } | ConvertTo-Json | Set-Content -LiteralPath `
        (Join-Path $artifactsPath "game-${viewportWidth}x${viewportHeight}.json") -Encoding utf8
    Write-Output "Normal game capture (screen messages enabled): $gameCapturePath"
}
