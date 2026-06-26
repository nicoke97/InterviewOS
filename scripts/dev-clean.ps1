# Free API port before starting dev (orphaned uvicorn reloaders on Windows).
$port = 8001
$killed = @()

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    if ($_ -gt 0) {
      Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
      $killed += $_
    }
  }

if ($killed.Count -gt 0) {
  Write-Host "dev:clean stopped process(es) on port $port : $($killed -join ', ')"
} else {
  Write-Host "dev:clean: port $port is free"
}
