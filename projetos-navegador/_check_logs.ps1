$logs = @("bot_output.log", "bot_error.log")
foreach ($f in $logs) {
    $path = "C:\projetos-navegador\$f"
    Write-Output "=== $f ==="
    if (Test-Path $path) {
        $item = Get-Item $path
        Write-Output "Size: $($item.Length) bytes"
        Get-Content $path -Tail 30
    } else {
        Write-Output "NOT FOUND"
    }
    Write-Output ""
}
$procs = Get-Process python* -EA SilentlyContinue
Write-Output "=== PYTHON PROCS ==="
Write-Output "Count: $($procs.Count)"
$procs | Select Id | Format-Table -A
