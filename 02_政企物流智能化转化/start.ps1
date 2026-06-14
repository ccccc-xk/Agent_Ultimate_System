# Smart Logistics - Startup Script
$ErrorActionPreference = "SilentlyContinue"
$projectRoot = "D:\Codex-project\Agent_Ultimate_System\02_政企物流智能化转化"
$javaHome = "D:\Program Files\Java\jdk-17"
$mvnCmd = "D:\Codex-project\Agent_Ultimate_System\01_企业管理基座系统\backend\maven\apache-maven-3.9.6\bin\mvn.cmd"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Smart Logistics - Quick Start" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check MySQL
Write-Host "[1/4] Checking MySQL..." -ForegroundColor Yellow
$mysql = Get-Service -Name "MySQL80","MySQL" -ErrorAction SilentlyContinue | Where-Object { $_.Status -ne "Running" }
if ($mysql) {
    $mysql | Start-Service
    Write-Host "  MySQL started." -ForegroundColor Green
} else {
    Write-Host "  MySQL ready." -ForegroundColor Green
}
Write-Host ""

# 2. Start Backend
Write-Host "[2/4] Starting Backend (port 8081)..." -ForegroundColor Yellow
$env:JAVA_HOME = $javaHome
Set-Location "$projectRoot\backend"

Get-Process java -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        if ($cmdLine -match "smart-logistics") {
            Stop-Process -Id $_.Id -Force
            Write-Host "  Killed old backend." -ForegroundColor DarkGray
        }
    } catch {}
}

if (-not (Test-Path "$projectRoot\backend\target\smart-logistics-1.0.0.jar")) {
    Write-Host "  Building backend..." -ForegroundColor DarkGray
    & $mvnCmd clean package -DskipTests -f "$projectRoot\backend\pom.xml"
}

Start-Process -FilePath "$javaHome\bin\java.exe" `
    -ArgumentList "-jar", "$projectRoot\backend\target\smart-logistics-1.0.0.jar" `
    -WindowStyle Hidden
Write-Host "  Backend starting..." -ForegroundColor DarkGray

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $listening = netstat -ano 2>$null | Select-String ":8081.*LISTENING"
    if ($listening) { $ready = $true; break }
}
if ($ready) { Write-Host "  Backend ready!" -ForegroundColor Green }
else { Write-Host "  Backend may need more time..." -ForegroundColor DarkYellow }
Write-Host ""

# 3. Start Frontend
Write-Host "[3/4] Starting Frontend (port 5174)..." -ForegroundColor Yellow
Set-Location "$projectRoot\frontend"

$oldVite = netstat -ano 2>$null | Select-String ":5174.*LISTENING"
if ($oldVite) {
    $pids = ($oldVite | ForEach-Object { ($_ -split "\s+")[-1] }) | Select-Object -Unique
    foreach ($p in $pids) {
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npx vite --port 5174 --host" -WindowStyle Hidden
Write-Host "  Frontend starting..." -ForegroundColor DarkGray

$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    $listening = netstat -ano 2>$null | Select-String ":5174.*LISTENING"
    if ($listening) { $ready = $true; break }
}
if ($ready) { Write-Host "  Frontend ready!" -ForegroundColor Green }
else { Write-Host "  Frontend may need more time..." -ForegroundColor DarkYellow }
Write-Host ""

# 4. Done
Write-Host "[4/4] All services started!" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5174" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8081" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:5174"
Read-Host "Press Enter to close this window"
