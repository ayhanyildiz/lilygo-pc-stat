$ErrorActionPreference = 'Stop'
$startupFolder = [Environment]::GetFolderPath('Startup')
if (-not $startupFolder) { throw 'The current user Startup folder could not be located.' }
$shortcutPath = Join-Path $startupFolder 'LILYGO PC Stat.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath
    Write-Output 'Automatic startup disabled for your Windows account.'
} else {
    Write-Output 'Automatic startup is already disabled.'
}
Write-Output 'The running helper is unchanged. Use Stop Monitor.ps1 to stop readings now.'
