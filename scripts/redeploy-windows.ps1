param(
    [switch]$SkipBuild,
    [switch]$NoCache,
    [switch]$Pull,
    [switch]$Migrate,
    [switch]$Force,
    [switch]$FrontendOnly,
    [switch]$BackendOnly
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$ComposeFile = Join-Path $ProjectDir "compose\docker-compose.yml"
$ComposeDir = Join-Path $ProjectDir "compose"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Confirm-Action([string]$Message) {
    if ($Force) { return }
    $answer = Read-Host "$Message [y/N]"
    if ($answer -notin @('y', 'Y', 'yes', 'YES')) {
        throw "Cancelled by user."
    }
}

function Invoke-Compose([string[]]$ComposeArgs) {
    & docker compose -f $ComposeFile @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($ComposeArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Wait-ForHttp([string]$Url, [int]$TimeoutSeconds = 90) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 10
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 3
        }
    }
    return $false
}

Write-Step "Trader Windows redeploy"

if ($Pull) {
    Write-Step "Pulling latest Git changes"
    Push-Location $ProjectDir
    try {
        $branch = (& git branch --show-current).Trim()
        if ($branch) {
            & git pull origin $branch
            if ($LASTEXITCODE -ne 0) { throw "git pull failed" }
        }
    } finally {
        Pop-Location
    }
}

$services = @()
if ($FrontendOnly -and -not $BackendOnly) {
    $services = @('frontend', 'proxy')
} elseif ($BackendOnly -and -not $FrontendOnly) {
    $services = @('backend', 'websocket', 'worker-short', 'worker-long', 'worker-default', 'scheduler', 'proxy')
}

if (-not $SkipBuild) {
    $buildArgs = @('build')
    if ($NoCache) { $buildArgs += '--no-cache' }
    if ($services.Count -gt 0) { $buildArgs += $services }

    $serviceLabel = ''
    if ($services.Count -gt 0) {
        $serviceLabel = " for: $($services -join ', ')"
    }

    Write-Step "Building fresh image set$serviceLabel"
    Invoke-Compose $buildArgs
}

Confirm-Action "This will restart the Docker services for Traders"

Write-Step "Restarting compose services"
if ($services.Count -gt 0) {
    Invoke-Compose (@('up', '-d', '--no-deps') + $services)
} else {
    Invoke-Compose @('up', '-d')
}

if ($Migrate) {
    Write-Step "Running backend migrate + clear-cache"
    $siteName = if ($env:SITE_NAME) { $env:SITE_NAME } else { 'trader.localhost' }
    & docker compose -f $ComposeFile exec -T backend bench --site $siteName migrate
    if ($LASTEXITCODE -ne 0) { throw "bench migrate failed" }
    & docker compose -f $ComposeFile exec -T backend bench --site $siteName clear-cache
}

Write-Step "Verifying health"
Invoke-Compose @('ps')

if (-not (Wait-ForHttp 'http://localhost:8080/api/method/ping' 120)) {
    throw "Proxy/API health check did not become ready in time"
}

Write-Host "`nRedeploy complete." -ForegroundColor Green
Write-Host "App UI:   http://localhost:8080"
Write-Host "API:      http://localhost:8080/api/method/ping"