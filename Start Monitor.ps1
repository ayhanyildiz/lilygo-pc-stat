$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run .\Setup.ps1 first to create the local Python environment.'
}
$scriptPath = Join-Path $PSScriptRoot 'monitor.py'
$logPath = Join-Path $PSScriptRoot '.pio\monitor.log'
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot '.pio') | Out-Null
$existing = Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($scriptPath) }
if ($existing) { Write-Output 'PC Monitor is already running.'; exit }
Start-Process -FilePath $pythonPath -ArgumentList @(('"' + $scriptPath + '"'), '--log', ('"' + $logPath + '"')) -WindowStyle Hidden
Write-Output "PC Monitor started. Log: $logPath"
