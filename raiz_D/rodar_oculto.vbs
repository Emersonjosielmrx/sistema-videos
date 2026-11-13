' Roda um comando sem abrir janela (usado pelas tarefas agendadas).
' Uso: wscript.exe D:\rodar_oculto.vbs "C:\caminho\script.bat" [args...]
Dim sh, i, cmd
Set sh = CreateObject("WScript.Shell")
cmd = ""
For i = 0 To WScript.Arguments.Count - 1
    cmd = cmd & """" & WScript.Arguments(i) & """ "
Next
WScript.Quit sh.Run(cmd, 0, True)
