# Wait for FastAPI to accept connections before starting Vite (avoids proxy ECONNREFUSED).
$uri = "http://127.0.0.1:8011/api/health"
$maxAttempts = 60

for ($i = 1; $i -le $maxAttempts; $i++) {
  try {
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
      Write-Host "wait-api: API ready ($uri)"
      exit 0
    }
  } catch {
    # API still starting
  }
  if ($i -eq 1) {
    Write-Host "wait-api: waiting for API on port 8011..."
  }
  Start-Sleep -Seconds 1
}

Write-Error "wait-api: API did not become ready on port 8011 after ${maxAttempts}s"
exit 1
