$ErrorActionPreference = "Stop"

$appName = "CursorTrail"
$displayName = "Cursor Trail"
$publisher = "zxckurayami"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\$appName"
$zip = Get-ChildItem -LiteralPath $PSScriptRoot -Filter "*.zip" | Select-Object -First 1

if (-not $zip) {
    throw "Installer payload archive was not found."
}

$tempDir = Join-Path $env:TEMP ("CursorTrail-install-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

try {
    Expand-Archive -LiteralPath $zip.FullName -DestinationPath $tempDir -Force

    $payloadDir = Join-Path $tempDir "Cursor Trail"
    if (-not (Test-Path -LiteralPath (Join-Path $payloadDir "Cursor Trail.exe"))) {
        $payloadDir = $tempDir
    }

    if (Test-Path -LiteralPath $installDir) {
        Remove-Item -LiteralPath $installDir -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    Copy-Item -Path (Join-Path $payloadDir "*") -Destination $installDir -Recurse -Force

    $exePath = Join-Path $installDir "Cursor Trail.exe"
    if (-not (Test-Path -LiteralPath $exePath)) {
        throw "Cursor Trail.exe was not installed."
    }

    $shell = New-Object -ComObject WScript.Shell

    $programsDir = [Environment]::GetFolderPath("Programs")
    $startMenuDir = Join-Path $programsDir $displayName
    New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null

    $startShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "$displayName.lnk"))
    $startShortcut.TargetPath = $exePath
    $startShortcut.WorkingDirectory = $installDir
    $startShortcut.IconLocation = $exePath
    $startShortcut.Save()

    $desktopDir = [Environment]::GetFolderPath("Desktop")
    $desktopShortcut = $shell.CreateShortcut((Join-Path $desktopDir "$displayName.lnk"))
    $desktopShortcut.TargetPath = $exePath
    $desktopShortcut.WorkingDirectory = $installDir
    $desktopShortcut.IconLocation = $exePath
    $desktopShortcut.Save()

    $uninstallScript = Join-Path $installDir "uninstall.ps1"
    @"
`$ErrorActionPreference = "SilentlyContinue"
`$appName = "$appName"
`$displayName = "$displayName"
`$installDir = Join-Path `$env:LOCALAPPDATA "Programs\`$appName"
Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath("Desktop")) "`$displayName.lnk") -Force
Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath("Programs")) "`$displayName") -Recurse -Force
Remove-Item -LiteralPath "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\`$appName" -Recurse -Force
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command Start-Sleep -Seconds 1; Remove-Item -LiteralPath '`$installDir' -Recurse -Force"
"@ | Set-Content -LiteralPath $uninstallScript -Encoding UTF8

    $uninstallCmd = Join-Path $installDir "uninstall.cmd"
    "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File ""%~dp0uninstall.ps1""" | Set-Content -LiteralPath $uninstallCmd -Encoding ASCII

    $uninstallShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "Uninstall $displayName.lnk"))
    $uninstallShortcut.TargetPath = $uninstallCmd
    $uninstallShortcut.WorkingDirectory = $installDir
    $uninstallShortcut.Save()

    $uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$appName"
    New-Item -Path $uninstallKey -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name DisplayName -Value $displayName -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name DisplayVersion -Value "1.1" -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name Publisher -Value $publisher -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name InstallLocation -Value $installDir -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name DisplayIcon -Value $exePath -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name UninstallString -Value "`"$uninstallCmd`"" -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name NoModify -Value 1 -PropertyType DWord -Force | Out-Null
    New-ItemProperty -Path $uninstallKey -Name NoRepair -Value 1 -PropertyType DWord -Force | Out-Null

    Start-Process -FilePath $exePath -WorkingDirectory $installDir
}
finally {
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
