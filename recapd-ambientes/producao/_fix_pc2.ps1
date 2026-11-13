# Fix the anime_discover.py on PC2
$content = Get-Content -Path "C:\recapd-e-animes\bin\anime_discover.py" -Raw
$content = $content -replace "probe_limit=200", "probe_limit=50"
$content = $content -replace "def _aspect_ratio_remote(url, timeout=45)", "def _aspect_ratio_remote(url, timeout=15)"
Set-Content -Path "C:\recapd-e-animes\bin\anime_discover.py" -Value $content -NoNewline
Write-Host "OK"
