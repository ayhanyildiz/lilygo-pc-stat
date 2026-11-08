$ErrorActionPreference = 'Stop'
$launcherPath = Join-Path $PSScriptRoot 'Start Monitor.ps1'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run .\Setup.ps1 first to create the local Python environment.'
}
if (-not (Test-Path -LiteralPath $launcherPath)) {
    throw 'Start Monitor.ps1 is missing. Keep the project files together.'
}
$startupFolder = [Environment]::GetFolderPath('Startup')
if (-not $startupFolder) { throw 'The current user Startup folder could not be located.' }
$shortcutPath = Join-Path $startupFolder 'LILYGO PC Stat.lnk'
$windowsShell = New-Object -ComObject WScript.Shell
$shortcut = $windowsShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcherPath + '"'
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.WindowStyle = 7
$shortcut.Description = 'Start the LILYGO PC Stat USB telemetry helper at Windows sign-in'
$shortcut.Save()
Write-Output "Automatic startup enabled for your Windows account: $shortcutPath"
Write-Output 'Keep this project folder in place. Run Start Monitor.ps1 to start readings now.'
