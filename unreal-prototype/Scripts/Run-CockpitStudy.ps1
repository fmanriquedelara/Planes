param(
    [ValidateSet('Build','Capture','Test','Profile','Play')][string]$Mode = 'Play',
    [ValidateSet('detail','baseline')][string]$Variant = 'detail',
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [ValidateRange(640,7680)][int]$Width = 3440,
    [ValidateRange(480,4320)][int]$Height = 1440,
    [ValidateRange(120,10000)][int]$ProfileFrames = 3000,
    [ValidateRange(50,100)][int]$ScreenPercentage = 100
)
$ErrorActionPreference = 'Stop'
$prototypeRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $prototypeRoot 'PlanesUnreal.uproject'
$outputName = if ($ScreenPercentage -eq 100 -or $Mode -eq 'Build') { $Variant } else { "$Variant-${ScreenPercentage}pct" }
$output = Join-Path $prototypeRoot "artifacts\ue008\$outputName"
New-Item -ItemType Directory -Force -Path $output | Out-Null
$map = if ($Variant -eq 'detail') { '/Game/Maps/EurofighterCockpitStudy' } else { '/Game/Maps/EurofighterCockpitBaseline' }
$executable = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$log = Join-Path $output "$($Mode.ToLower()).log"
$started = Get-Date
$arguments = @($project)
if ($Mode -eq 'Build') {
    $env:PLANES_COCKPIT_VARIANT = $Variant
    $script = Join-Path $PSScriptRoot 'build_cockpit_comparison.py'
    $arguments += @('-run=pythonscript',"-script=$script",'-NullRHI','-unattended','-nosplash','-nosound','-NoP4',"-abslog=$log")
} else {
    $renderSettings = "r.ScreenPercentage $ScreenPercentage,r.DynamicRes.OperationMode 0"
    $arguments += @($map,'-game','-windowed','-ForceRes',"-ResX=$Width","-ResY=$Height",'-nosplash','-NoP4',"-abslog=$log")
    if ($Mode -ne 'Play') { $arguments += @('-RenderOffscreen','-unattended','-nosound') }
    if ($Mode -eq 'Capture') {
        $shot = ('DEFER ' * 240) + "Shot SHOWUI filename=UE008-$Variant -nosuffix"
        $quit = ('DEFER ' * 270) + 'Quit'
        $arguments += "-ExecCmds=$renderSettings,$shot,$quit"
    } elseif ($Mode -eq 'Test') {
        $arguments += @('-PlanesSelfTest',"-PlanesTestOutput=$output","-ExecCmds=$renderSettings")
    } elseif ($Mode -eq 'Profile') {
        # Native CSV profiler measures real frame times after warmup, without fixed timestep.
        $capture = ('DEFER ' * 360) + "CsvProfile FRAMES=$ProfileFrames"
        $arguments += @('-csvGpuStats','-ExitAfterCsvProfiling',
            "-ExecCmds=$renderSettings,r.VSync 0,t.MaxFPS 0,CsvProfile STARTFILE=ue008-$Variant.csv,$capture")
    } else {
        $arguments += "-ExecCmds=$renderSettings"
    }
}
if ($Mode -eq 'Play') {
    $executable = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
    $quoted = $arguments | ForEach-Object { '"' + $_ + '"' }
    $game = Start-Process -FilePath $executable -ArgumentList $quoted -WorkingDirectory $prototypeRoot -WindowStyle Normal -PassThru
    Write-Output "Launched separate $Variant cockpit study (PID $($game.Id))."
    return
}
try { & $executable @arguments } finally { if ($Mode -eq 'Build') { Remove-Item Env:PLANES_COCKPIT_VARIANT -ErrorAction SilentlyContinue } }
if ($LASTEXITCODE -ne 0) { throw "Unreal exited $LASTEXITCODE; see $log" }
if ($Mode -eq 'Build') {
    $report = Join-Path $output 'build.json'
    if (!(Test-Path $report) -or (Get-Item $report).LastWriteTime -lt $started) { throw 'No fresh build report.' }
} elseif ($Mode -eq 'Capture') {
    $png = Get-ChildItem (Join-Path $prototypeRoot 'Saved\Screenshots') -Recurse -Filter "UE008-$Variant.png" |
        Where-Object { $_.LastWriteTime -ge $started } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$png) { throw 'No fresh normal-game capture.' }
    Copy-Item -LiteralPath $png.FullName -Destination (Join-Path $output 'normal-game.png')
} elseif ($Mode -eq 'Test') {
    $report = Join-Path $output 'runtime-report.json'
    if (!(Test-Path $report) -or (Get-Item $report).LastWriteTime -lt $started) { throw 'No fresh test report.' }
    $result = Get-Content $report -Raw | ConvertFrom-Json
    $failed = @($result.checks.PSObject.Properties | Where-Object { $_.Value -ne $true })
    if ($failed.Count) { throw "Failed checks: $($failed.Name -join ', ')" }
    foreach ($snapshot in $result.snapshots) {
        if ([IO.Path]::GetFileName($snapshot.file) -ne $snapshot.file) { throw 'Unsafe snapshot path.' }
        $path = Join-Path $output $snapshot.file
        if (!(Test-Path $path) -or (Get-Item $path).LastWriteTime -lt $started) { throw "Missing fresh snapshot $path" }
    }
} elseif ($Mode -eq 'Profile') {
    $csv = Get-ChildItem (Join-Path $prototypeRoot 'Saved\Profiling') -Recurse -Filter "ue008-$Variant.csv" |
        Where-Object { $_.LastWriteTime -ge $started } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$csv) { throw 'No fresh CSV frame-time capture.' }
    Copy-Item -LiteralPath $csv.FullName -Destination (Join-Path $output 'profile.csv')
}
$buildEvidencePath = Join-Path $prototypeRoot "artifacts\ue008\$Variant\build.json"
$buildEvidence = if (Test-Path -LiteralPath $buildEvidencePath) { Get-Content -LiteralPath $buildEvidencePath -Raw | ConvertFrom-Json } else { $null }
[ordered]@{ mode=$Mode; variant=$Variant; map=$map; width=$Width; height=$Height;
    engine=$buildEvidence.engine; input_sha256=$buildEvidence.input_sha256;
    native_material_revision=$buildEvidence.native_material_revision;
    start_utc=$started.ToUniversalTime().ToString('o'); end_utc=(Get-Date).ToUniversalTime().ToString('o');
    normal_game=($Mode -ne 'Build'); offscreen=($Mode -ne 'Play'); cinematic_mrq=$false;
    screen_percentage=$ScreenPercentage; dynamic_resolution=$false;
    profile_frames= $(if ($Mode -eq 'Profile') { $ProfileFrames } else { 0 })
} | ConvertTo-Json | Set-Content (Join-Path $output "$($Mode.ToLower())-run.json") -Encoding utf8
Write-Output "$Mode completed: $output"
