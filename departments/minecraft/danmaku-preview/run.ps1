param(
    [string]$JavaHome = $env:JAVA_HOME,
    [switch]$Test,
    [switch]$Smoke,
    [string]$SmokeOutput = (Join-Path $PSScriptRoot 'build/smoke'),
    [switch]$CompileOnly,
    [switch]$Score,
    [string]$ScoreFile = (Join-Path $PSScriptRoot 'presets/grand-danmaku-score.json')
)
$ErrorActionPreference = 'Stop'
if (-not $JavaHome -and (Test-Path -LiteralPath 'C:/Program Files/Java/jdk-17/bin/javac.exe')) {
    $JavaHome = 'C:/Program Files/Java/jdk-17'
}
if (-not $JavaHome) { throw 'Set JAVA_HOME to a JDK17+ installation, or use -JavaHome.' }
$taskJava = Join-Path $JavaHome 'bin/java.exe'
$taskJavac = Join-Path $JavaHome 'bin/javac.exe'
if (-not (Test-Path -LiteralPath $taskJavac)) { throw "JDK javac not found: $taskJavac" }
$taskBuild = Join-Path $PSScriptRoot 'build/classes'
New-Item -ItemType Directory -Force -Path $taskBuild | Out-Null
$taskCore = @(
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/Pattern.java'),
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/PatternJson.java'),
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/Score.java'),
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/ScoreJson.java')
)
if ($Test) {
    $taskTests = @(
        (Join-Path $PSScriptRoot 'tests/kneekura/danmaku/PatternTest.java'),
        (Join-Path $PSScriptRoot 'tests/kneekura/danmaku/ScoreTest.java')
    )
    & $taskJavac --release 17 -encoding UTF-8 -d $taskBuild @taskCore @taskTests
    if ($LASTEXITCODE -ne 0) { throw 'Test compile failed' }
    & $taskJava -cp $taskBuild kneekura.danmaku.PatternTest (Join-Path $PSScriptRoot 'presets/fan.json')
    if ($LASTEXITCODE -ne 0) { throw 'Pattern tests failed' }
    & $taskJava -cp $taskBuild kneekura.danmaku.ScoreTest (Join-Path $PSScriptRoot 'presets/grand-danmaku-score.json')
    if ($LASTEXITCODE -ne 0) { throw 'Score tests failed' }
    exit 0
}
if (-not [Environment]::Is64BitOperatingSystem -or $env:OS -ne 'Windows_NT') { throw 'This launcher supports Windows x64.' }
$taskCache = Join-Path $PSScriptRoot '.cache/javafx-21.0.9'
New-Item -ItemType Directory -Force -Path $taskCache | Out-Null
$taskHashes = @{
    base = '95D680B5D0B1ED9358376B12FC2F30F10E813F04F929E51698EB5507867CD408'
    graphics = '97D85E83CF16964AB015FF735DF6F7F11FE115F78144CA8F1949E89A8BFDDD78'
    controls = '991A8FBDCB289E717B3F5ADA39D2C948D9A7CD8C798A9E2311A4B574274DD1E2'
}
foreach ($taskModule in @('base', 'graphics', 'controls')) {
    $taskJarName = "javafx-$taskModule-21.0.9-win.jar"
    $taskJar = Join-Path $taskCache $taskJarName
    if (-not (Test-Path -LiteralPath $taskJar)) {
        $taskDownload = "$taskJar.download"
        Invoke-WebRequest -Uri "https://repo.maven.apache.org/maven2/org/openjfx/javafx-$taskModule/21.0.9/$taskJarName" -OutFile $taskDownload
        if ((Get-FileHash -LiteralPath $taskDownload -Algorithm SHA256).Hash -ne $taskHashes[$taskModule]) { throw "Download hash mismatch: $taskJarName" }
        Move-Item -LiteralPath $taskDownload -Destination $taskJar
    }
    if ((Get-FileHash -LiteralPath $taskJar -Algorithm SHA256).Hash -ne $taskHashes[$taskModule]) { throw "Cached jar hash mismatch: $taskJarName" }
}
$taskApps = @(
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/PreviewApp.java'),
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/ScorePreviewApp.java')
)
& $taskJavac --release 17 -encoding UTF-8 --module-path $taskCache --add-modules javafx.controls -d $taskBuild @taskCore @taskApps
if ($LASTEXITCODE -ne 0) { throw 'JavaFX compile failed' }
if ($CompileOnly) { Write-Output 'PASS: Pattern + Score JavaFX compile'; exit 0 }
if ($Score -and $Smoke) { throw 'Score Mode smoke is not implemented yet; launch it normally or use -CompileOnly.' }
if ($Score) {
    $taskArgs = @('--module-path', $taskCache, '--add-modules', 'javafx.controls', '-cp', $taskBuild,
        'kneekura.danmaku.ScorePreviewApp', '--score', $ScoreFile)
} else {
    $taskArgs = @('--module-path', $taskCache, '--add-modules', 'javafx.controls', '-cp', $taskBuild,
        'kneekura.danmaku.PreviewApp')
    if ($Smoke) { $taskArgs += @('--smoke', $SmokeOutput) }
}
& $taskJava @taskArgs
if ($LASTEXITCODE -ne 0) { throw 'JavaFX app failed' }
