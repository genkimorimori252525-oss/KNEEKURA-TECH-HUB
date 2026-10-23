param([Parameter(ValueFromRemainingArguments=$true)][string[]]$TaskArgs)
$ErrorActionPreference = 'Stop'
if (-not $env:KNEEKURA_TANK_WRAPPER) { throw 'TANK_WRAPPER_REQUIRED' }
& $env:KNEEKURA_TANK_WRAPPER @TaskArgs
exit $LASTEXITCODE
