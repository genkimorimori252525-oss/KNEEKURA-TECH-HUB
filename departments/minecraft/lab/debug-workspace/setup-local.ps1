param(
    [Parameter(Mandatory = $false)]
    [string]$ReimuWorkspace,

    [Parameter(Mandatory = $false)]
    [string]$WorldName = 'KNEEKURA_DEBUG_WORLD',

    [Parameter(Mandatory = $false)]
    [switch]$Smoke,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $Here
$ProfilePath = Join-Path $Here 'profiles\reimu-mod.example.json'
$ConfigPath = Join-Path $Here 'config.local.json'

function Write-Step([string]$Text) {
    Write-Host "[KNEEKURA] $Text"
}

function Resolve-ReimuWorkspace([string]$Explicit) {
    $candidates = New-Object System.Collections.Generic.List[string]

    if ($Explicit) {
        $candidates.Add($Explicit)
    }

    if ($env:REIMU_MOD_WORKSPACE) {
        $candidates.Add($env:REIMU_MOD_WORKSPACE)
    }

    $parent = Split-Path -Parent $RepoRoot
    $candidates.Add((Join-Path $parent 'reimu-mod'))
    $candidates.Add((Join-Path $HOME 'source\repos\reimu-mod'))
    $candidates.Add((Join-Path $HOME 'Documents\GitHub\reimu-mod'))
    $candidates.Add((Join-Path $HOME 'Desktop\reimu-mod'))
    $candidates.Add((Join-Path $HOME 'Downloads\reimu-mod'))

    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }
        try {
            $resolved = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path
        } catch {
            continue
        }

        if ((Test-Path -LiteralPath (Join-Path $resolved 'build.gradle')) -and
            (Test-Path -LiteralPath (Join-Path $resolved 'gradlew.bat'))) {
            return $resolved
        }
    }

    throw @"
Could not find a local reimu-mod Forge workspace.

Run again with:
  powershell -NoProfile -ExecutionPolicy Bypass -File "$Here\setup-local.ps1" -ReimuWorkspace "C:\path\to\reimu-mod"

Or set:
  REIMU_MOD_WORKSPACE=C:\path\to\reimu-mod
"@
}

function Assert-G1Integration([string]$Workspace) {
    $buildFile = Join-Path $Workspace 'build.gradle'
    $text = Get-Content -LiteralPath $buildFile -Raw

    $required = @(
        'KNEEKURA_DEBUG_FORGE_BRIDGE_SRC',
        'kneekuraDebugSourceSet',
        '--quickPlaySingleplayer',
        'KNEEKURA_DEBUG_BUILD_MARKER'
    )

    $missing = @()
    foreach ($marker in $required) {
        if (-not $text.Contains($marker)) {
            $missing += $marker
        }
    }

    if ($missing.Count -gt 0) {
        throw @"
The selected reimu-mod checkout is too old for G1.
Missing build.gradle markers:
  $($missing -join ', ')

Update the local checkout from:
  genkimorimori252525-oss/reimu-mod

Then run this setup again.
"@
    }
}

if (-not (Test-Path -LiteralPath $ProfilePath)) {
    throw "Profile not found: $ProfilePath"
}

$workspace = Resolve-ReimuWorkspace $ReimuWorkspace
Write-Step "Using reimu-mod workspace: $workspace"

Assert-G1Integration $workspace
Write-Step 'G1 integration markers found.'

if ((Test-Path -LiteralPath $ConfigPath) -and -not $Force) {
    Write-Step "Existing config found: $ConfigPath"
    Write-Step 'Keeping it. Use -Force to regenerate.'
} else {
    $profile = Get-Content -LiteralPath $ProfilePath -Raw | ConvertFrom-Json
    $profile.workspaceDir = $workspace
    $profile.worldName = $WorldName

    $json = $profile | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText(
        $ConfigPath,
        $json + [Environment]::NewLine,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Step "Wrote config: $ConfigPath"
}

$gameDir = Join-Path $workspace 'run\client_a'
$worldDir = Join-Path $gameDir ("saves\" + $WorldName)

if (-not (Test-Path -LiteralPath $gameDir)) {
    Write-Warning "Forge game directory does not exist yet: $gameDir"
    Write-Host 'Run the normal reimu-mod runClient once if this checkout has never created run/client_a.'
}

if (-not (Test-Path -LiteralPath $worldDir)) {
    Write-Warning "Debug World is missing: $worldDir"
    Write-Host ''
    Write-Host "Create a singleplayer world named exactly:"
    Write-Host "  $WorldName"
    Write-Host ''
    Write-Host 'in the reimu-mod run/client_a development client.'
    Write-Host 'After that, run this setup again or run:'
    Write-Host '  npm run debug:doctor'
    Write-Host ''
    exit 2
}

Write-Step "Debug World found: $worldDir"

Push-Location $RepoRoot
try {
    Write-Step 'Running debug doctor...'
    & node 'debug-workspace/cli.mjs' doctor --config 'debug-workspace/config.local.json'
    if ($LASTEXITCODE -ne 0) {
        throw "debug:doctor failed with exit code $LASTEXITCODE"
    }

    if ($Smoke) {
        Write-Step 'Running full G1 smoke acceptance...'
        & node 'debug-workspace/cli.mjs' smoke --config 'debug-workspace/config.local.json'
        if ($LASTEXITCODE -ne 0) {
            throw "debug:smoke failed with exit code $LASTEXITCODE"
        }
        Write-Step 'G1 smoke acceptance passed.'
    } else {
        Write-Host ''
        Write-Step 'Setup complete.'
        Write-Host 'Run the full G1 acceptance with:'
        Write-Host '  npm run debug:smoke'
        Write-Host ''
        Write-Host 'Or run setup + smoke in one command:'
        Write-Host '  powershell -NoProfile -ExecutionPolicy Bypass -File debug-workspace\setup-local.ps1 -Smoke'
    }
} finally {
    Pop-Location
}
