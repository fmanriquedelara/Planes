param(
    [ValidateSet('Build', 'Capture', 'Play', 'Editor')]
    [string]$Mode = 'Play',
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8'
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
        $unrealArguments += @('/Game/Maps/CockpitStudy', '-game', '-windowed',
            '-ResX=1600', '-ResY=1000', '-NoP4')
    }
    'Editor' {
        $unrealExecutable = $editorPath
        $unrealArguments += @('-NoP4')
    }
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
