$scriptPath = Join-Path $PSScriptRoot 'monitor.py'
Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($scriptPath) } |
    ForEach-Object { Stop-Process -Id $_.ProcessId }
Write-Output 'PC Monitor stopped.'
