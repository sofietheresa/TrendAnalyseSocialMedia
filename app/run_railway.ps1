# PowerShell-Startup-Skript für Railway

Write-Host "Starting Railway deployment..."
Write-Host "Current directory: $(Get-Location)"

# Port aus Umgebungsvariable übernehmen oder Standard verwenden
$PORT = if ($env:PORT) { $env:PORT } else { "8000" }
Write-Host "Using port: $PORT"

# Health-App im Hintergrund starten
Write-Host "Starting health app in the background..."
Start-Process -FilePath "uvicorn" -ArgumentList "health_app:app --host=0.0.0.0 --port=$PORT" -NoNewWindow
$healthAppProcess = Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue
Write-Host "Health app started with PID: $($healthAppProcess.Id)"

# Warte einen Moment, damit die Health-App starten kann
Start-Sleep -Seconds 5

# Hauptanwendung starten (blockierend)
Write-Host "Starting main application..."
try {
    python railway.py
} finally {
    # Beim Beenden: Health-App stoppen
    if ($healthAppProcess -ne $null) {
        Write-Host "Stopping health app..."
        Stop-Process -Id $healthAppProcess.Id -Force -ErrorAction SilentlyContinue
    }
} 