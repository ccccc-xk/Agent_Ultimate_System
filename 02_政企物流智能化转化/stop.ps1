# Smart Logistics - Stop Script
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Stopping Smart Logistics System" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Stopping Backend..." -ForegroundColor Yellow
Get-Process java -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        if ($cmdLine -match "smart-logistics") {
            Stop-Process -Id $_.Id -Force
            Write-Host "  Stopped backend (PID: $($_.Id))" -ForegroundColor Green
        }
    } catch {}
}
Write-Host ""

Write-Host "[2/2] Stopping Frontend..." -ForegroundColor Yellow
$ports = netstat -ano 2>$null | Select-String ":5174.*LISTENING"
if ($ports) {
    $pids = ($ports | ForEach-Object { ($_ -split "\s+")[-1] }) | Select-Object -Unique
    foreach ($p in $pids) {
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped frontend (PID: $p)" -ForegroundColor Green
    }
} else {
    Write-Host "  Frontend not running." -ForegroundColor DarkGray
}
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  All services stopped." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close this window"
