$r = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper_debug.py"
if ($r.ReturnValue -eq 0) {
    Write-Output "PID=$($r.ProcessId)"
} else {
    Write-Output "FAIL=$($r.ReturnValue)"
}
