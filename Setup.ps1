param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) {
    $command = Get-Command py, python, python3 -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notlike '*\Microsoft\WindowsApps\*' } |
        Select-Object -First 1
    if ($command) { $PythonPath = $command.Source }
}
if (-not $PythonPath) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Python\pythoncore-*\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\python.exe')
    )
    $found = Get-ChildItem -Path $candidates -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($found) { $PythonPath = $found.FullName }
}
if (-not $PythonPath) { throw 'Install Python 3.10 or later, or pass -PythonPath C:\path\python.exe.' }
$venvPath = Join-Path $PSScriptRoot '.venv'
& $PythonPath -m venv $venvPath
if ($LASTEXITCODE) { throw 'Creating the Python environment failed.' }
$venvPython = Join-Path $venvPath 'Scripts\python.exe'
& $venvPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE) { throw 'Installing runtime dependencies failed.' }
Write-Output 'Setup complete. Run .\Start Monitor.ps1 to start the display helper.'
