$goPath = Get-Command go -ErrorAction SilentlyContinue
if ($goPath) {
    Write-Host "Found go at: $($goPath.Source)"
    cd D:\callagente
    go fmt ./...
    go build -o bin/server.exe ./cmd/server
    Write-Host "Build finished with code $LASTEXITCODE"
} else {
    Write-Host "Could not find go in PATH"
}
