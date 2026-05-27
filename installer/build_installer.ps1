param(
    [string]$Version = "1.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $repoRoot "dist"
$appDir = Join-Path $distDir "Cursor Trail"
$buildDir = Join-Path $repoRoot "build"
$workDir = Join-Path $buildDir "installer-work"
$payloadAppDir = Join-Path $workDir "app"
$payloadZip = Join-Path $workDir "CursorTrailPayload.zip"
$setupPath = Join-Path $distDir "CursorTrail-Setup-$Version-x64.exe"
$uninstallerPath = Join-Path $payloadAppDir "CursorTrailUninstall.exe"
$iconPath = Join-Path $repoRoot "icon.ico"
$setupSource = Join-Path $PSScriptRoot "CursorTrailSetup.cs"
$uninstallSource = Join-Path $PSScriptRoot "CursorTrailUninstall.cs"

if (-not (Test-Path -LiteralPath (Join-Path $appDir "Cursor Trail.exe"))) {
    throw "Build the application first: python -m PyInstaller `"Cursor Trail.spec`""
}

$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path -LiteralPath $csc)) {
    throw "C# compiler was not found: $csc"
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

$resolvedRoot = [System.IO.Path]::GetFullPath($repoRoot)
$resolvedWork = [System.IO.Path]::GetFullPath($workDir)
if (-not $resolvedWork.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Installer work path is outside repository."
}

if (Test-Path -LiteralPath $workDir) {
    Remove-Item -LiteralPath $workDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $payloadAppDir | Out-Null
Copy-Item -Path (Join-Path $appDir "*") -Destination $payloadAppDir -Recurse -Force

$commonRefs = @(
    "/reference:System.Windows.Forms.dll",
    "/reference:System.Drawing.dll",
    "/reference:System.IO.Compression.dll",
    "/reference:System.IO.Compression.FileSystem.dll"
)

& $csc /nologo /target:winexe /optimize+ /codepage:65001 /win32icon:$iconPath /out:$uninstallerPath $commonRefs $uninstallSource
if ($LASTEXITCODE -ne 0) {
    throw "Failed to compile CursorTrailUninstall.exe."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $payloadAppDir,
    $payloadZip,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

if (Test-Path -LiteralPath $setupPath) {
    Remove-Item -LiteralPath $setupPath -Force
}

& $csc /nologo /target:winexe /optimize+ /codepage:65001 /win32icon:$iconPath /out:$setupPath "/resource:$payloadZip,CursorTrail.Payload.zip" $commonRefs $setupSource
if ($LASTEXITCODE -ne 0) {
    throw "Failed to compile CursorTrail setup."
}

Get-Item -LiteralPath $setupPath
