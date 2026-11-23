# Aikya Forge: verify the native installer from the latest stable release.
[CmdletBinding()]
param(
    [ValidateSet('global')][string]$Scope='global',
    [ValidateSet('stable')][string]$Channel='stable',
    [ValidatePattern('^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')][string]$Version,
    [string]$OfflineDir,
    [ValidateSet('install','uninstall')][string]$Action='install',
    [switch]$NoPath,
    [switch]$DryRun,
    [switch]$Help
)
$callerPreference=$ErrorActionPreference
try {
    $ErrorActionPreference='Stop'
    if ($Help) { Write-Output 'Aikya Forge: .\install.ps1 [-Version X.Y.Z] [-OfflineDir DIR] [-NoPath] [-DryRun]. Requires a published stable release.'; return }
    if ($DryRun) {
        $selected='latest'; if ($Version) {$selected=$Version}
        @{product='aikya-forge';release=$selected;network=$false;writes=$false} | ConvertTo-Json -Compress
        return
    }
    $stage=Join-Path ([IO.Path]::GetTempPath()) ('aikya-forge-install-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    try {
        foreach ($name in @('install.ps1','SHA256SUMS')) {
            $destination=Join-Path $stage $name
            if ($OfflineDir) {
                $source=Get-Item -LiteralPath (Join-Path $OfflineDir $name)
                if ($source.PSIsContainer -or ($source.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $source.Length -gt 128000) { throw 'Offline installer files must be bounded regular files.' }
                Copy-Item -LiteralPath $source.FullName -Destination $destination
            } else {
                Add-Type -AssemblyName System.Net.Http
                $handler=New-Object Net.Http.HttpClientHandler; $handler.AllowAutoRedirect=$false
                $client=[Net.Http.HttpClient]::new($handler); $client.Timeout=[TimeSpan]::FromSeconds(90)
                try {
                    $release='latest/download'; if ($Version) {$release='download/v'+$Version}
                    $uri=[uri]('https://github.com/jlema0590/aikya-forge/releases/'+$release+'/'+$name)
                    for ($redirect=0; $redirect -le 5; $redirect++) {
                        if ($uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Host -notin @('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com')) { throw 'Untrusted Forge release URL.' }
                        $response=$client.GetAsync($uri,[Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
                        try {
                            if ([int]$response.StatusCode -ge 300 -and [int]$response.StatusCode -lt 400) {
                                if (-not $response.Headers.Location) {throw 'Missing release redirect.'}
                                $uri=[uri]::new($uri,$response.Headers.Location); continue
                            }
                            if (-not $response.IsSuccessStatusCode) { throw 'No verified Forge release could be downloaded. Check published releases and your connection.' }
                            if ($response.Content.Headers.ContentLength -gt 128000) {throw 'Installer file exceeds size limit.'}
                            $inputStream=$response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
                            $outputStream=[IO.File]::Create($destination)
                            try {
                                $buffer=New-Object byte[] 16384; $total=0
                                while (($count=$inputStream.Read($buffer,0,$buffer.Length)) -gt 0) {
                                    $total+=$count; if ($total -gt 128000) {throw 'Installer file exceeds size limit.'}
                                    $outputStream.Write($buffer,0,$count)
                                }
                            } finally {$outputStream.Dispose(); $inputStream.Dispose()}
                        } finally {$response.Dispose()}
                        break
                    }
                    if (-not (Test-Path -LiteralPath $destination)) {throw 'Too many release redirects.'}
                } finally {$client.Dispose(); $handler.Dispose()}
            }
        }
        $matchesFound=@([IO.File]::ReadAllLines((Join-Path $stage 'SHA256SUMS')) | Where-Object {$_ -match '^\S+\s+\*?install\.ps1\s*$'})
        if ($matchesFound.Count -ne 1 -or $matchesFound[0] -cnotmatch '^([a-f0-9]{64})  \*?install\.ps1$') {throw 'Installer checksum is missing, malformed or duplicated.'}
        $checksum=$Matches[1]
        $entry=Join-Path $stage 'install.ps1'
        $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $entry).Hash.ToLowerInvariant()
        if ($actual -ne $checksum) {throw 'Installer checksum mismatch; nothing was installed.'}
        $forward=@{Scope=$Scope;Channel=$Channel;Action=$Action}
        if ($Version) {$forward.Version=$Version}
        if ($OfflineDir) {$forward.OfflineDir=$OfflineDir}
        if ($NoPath) {$forward.NoPath=$true}
        # Only verified bytes become executable; no execution policy is changed.
        & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) @forward
    } finally {Remove-Item -LiteralPath $stage -Recurse -Force}
} finally {$ErrorActionPreference=$callerPreference}
