# Free API port before starting dev (orphaned uvicorn reloaders on Windows).
$port = 8011
$killed = [System.Collections.Generic.HashSet[int]]::new()

function Stop-ProcessTree {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return }
    if (-not $killed.Add($ProcessId)) { return }
    & taskkill /PID $ProcessId /F /T 2>$null | Out-Null
}

for ($round = 0; $round -lt 6; $round++) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-ProcessTree $_ }

    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'uvicorn' -and $_.CommandLine -match "--port\s+$port(\s|$)" } |
        ForEach-Object { Stop-ProcessTree $_.ProcessId }

    Start-Sleep -Milliseconds 600

    $listening = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    if ($listening.Count -eq 0) { break }
}

$remaining = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
if ($killed.Count -gt 0) {
    Write-Host "dev:clean stopped process(es) on port $port : $(@($killed) -join ', ')"
}
if ($remaining.Count -gt 0) {
    $pids = ($remaining | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique) -join ', '
    Write-Host "dev:clean WARNING: port $port still in use (PID $pids). Close other dev terminals or reboot."
} else {
    Write-Host "dev:clean: port $port is free"
}
