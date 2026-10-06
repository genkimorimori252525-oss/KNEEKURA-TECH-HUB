param(
    [string]$JavaHome = $env:JAVA_HOME,
    [switch]$Test,
    [switch]$Smoke,
    [string]$SmokeOutput = (Join-Path $PSScriptRoot 'build/smoke'),
    [switch]$CompileOnly
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
    (Join-Path $PSScriptRoot 'src/kneekura/danmaku/PatternJson.java')
)
if ($Test) {
    & $taskJavac --release 17 -encoding UTF-8 -d $taskBuild @taskCore (Join-Path $PSScriptRoot 'tests/kneekura/danmaku/PatternTest.java')
    if ($LASTEXITCODE -ne 0) { throw 'Test compile failed' }
    & $taskJava -cp $taskBuild kneekura.danmaku.PatternTest
    if ($LASTEXITCODE -ne 0) { throw 'Pattern tests failed' }
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
& $taskJavac --release 17 -encoding UTF-8 --module-path $taskCache --add-modules javafx.controls -d $taskBuild @taskCore (Join-Path $PSScriptRoot 'src/kneekura/danmaku/PreviewApp.java')
if ($LASTEXITCODE -ne 0) { throw 'JavaFX compile failed' }
if ($CompileOnly) { Write-Output 'PASS: JavaFX compile'; exit 0 }
$taskArgs = @('--module-path', $taskCache, '--add-modules', 'javafx.controls', '-cp', $taskBuild, 'kneekura.danmaku.PreviewApp')
if ($Smoke) { $taskArgs += @('--smoke', $SmokeOutput) }
& $taskJava @taskArgs
if ($LASTEXITCODE -ne 0) { throw 'JavaFX app failed' }