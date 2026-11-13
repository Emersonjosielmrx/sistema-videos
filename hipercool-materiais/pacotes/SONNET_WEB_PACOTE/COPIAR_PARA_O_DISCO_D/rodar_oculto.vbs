' rodar_oculto.vbs — roda um programa SEM abrir janela (usado nas tarefas agendadas).
' Uso: wscript.exe D:\rodar_oculto.vbs "C:\caminho\python.exe" "D:\gemini-argo\argon_manter.py"
Set a = WScript.Arguments
cmd = ""
For i = 0 To a.Count - 1
  cmd = cmd & """" & a(i) & """ "
Next
CreateObject("WScript.Shell").Run Trim(cmd), 0, False
