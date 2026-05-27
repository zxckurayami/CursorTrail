param(
    [string]$Version = "1.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $repoRoot "dist"
$appDir = Join-Path $distDir "Cursor Trail"
$buildDir = Join-Path $repoRoot "build"
$payloadDir = Join-Path $buildDir "installer-payload"
$zipName = "CursorTrail-v$Version-windows-x64.zip"
$zipPath = Join-Path $distDir $zipName
$setupPath = Join-Path $distDir "CursorTrail-Setup-$Version-x64.exe"
$sedPath = Join-Path $buildDir "CursorTrailInstaller.sed"

if (-not (Test-Path -LiteralPath (Join-Path $appDir "Cursor Trail.exe"))) {
    throw "Build the application first: python -m PyInstaller `"Cursor Trail.spec`""
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -LiteralPath $appDir -DestinationPath $zipPath -CompressionLevel Optimal

$resolvedRoot = [System.IO.Path]::GetFullPath($repoRoot)
$resolvedPayload = [System.IO.Path]::GetFullPath($payloadDir)
if (-not $resolvedPayload.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Payload path is outside repository."
}

if (Test-Path -LiteralPath $payloadDir) {
    Remove-Item -LiteralPath $payloadDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $payloadDir | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "install.cmd") -Destination $payloadDir -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "install.ps1") -Destination $payloadDir -Force
Copy-Item -LiteralPath $zipPath -Destination $payloadDir -Force

if (Test-Path -LiteralPath $setupPath) {
    Remove-Item -LiteralPath $setupPath -Force
}

$drive = $null
foreach ($letter in "Z", "Y", "X", "W", "V") {
    if (-not (Get-PSDrive -Name $letter -ErrorAction SilentlyContinue)) {
        $drive = "$letter`:"
        break
    }
}

if (-not $drive) {
    throw "No free temporary drive letter was found for IExpress."
}

cmd /c "subst $drive `"$repoRoot`"" | Out-Null

try {
    $versionedSetup = "CursorTrail-Setup-$Version-x64.exe"
    $sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles
[SourceFiles]
SourceFiles0=$drive\build\installer-payload\
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
[Strings]
InstallPrompt=
DisplayLicense=
FinishMessage=Cursor Trail installed successfully.
TargetName=$drive\dist\$versionedSetup
FriendlyName=CursorTrail Setup
AppLaunched=install.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=install.cmd
UserQuietInstCmd=install.cmd
FILE0="install.cmd"
FILE1="install.ps1"
FILE2="$zipName"
"@

    Set-Content -LiteralPath $sedPath -Value $sed -Encoding ASCII
    $process = Start-Process -FilePath "iexpress.exe" -ArgumentList "/N", "$drive\build\CursorTrailInstaller.sed" -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -ne 0) {
        throw "IExpress failed with exit code $($process.ExitCode)."
    }
}
finally {
    cmd /c "subst $drive /D" | Out-Null
}

Get-Item -LiteralPath $setupPath
