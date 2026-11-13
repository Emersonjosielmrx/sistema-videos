# autorizar_desktop.ps1 — a DONA roda no PC1, num PowerShell "Executar como administrador" (29/10/2026).
# Dá ao desktop acesso por ssh ao PC1, PC2 e notebooks com a chave PRÓPRIA dele (a privada nunca saiu de lá; a pública
# veio pelo desktop_vigia.py para D:\video-fila\estado\desktop_chave.pub). É mudança de segurança: por isso não roda
# sozinho. Pode rodar de novo quantas vezes quiser (não duplica nada).
#     powershell -ExecutionPolicy Bypass -File D:\video-fila\autorizar_desktop.ps1
$ErrorActionPreference = "Continue"
$pubArq = "D:\video-fila\estado\desktop_chave.pub"
if (-not (Test-Path $pubArq)) { "Ainda não tenho a chave do desktop (o desktop_vigia pega na 1ª vez que o ssh entrar)."; exit 1 }
$pub = (Get-Content $pubArq -Raw).Trim()
if (-not $pub.StartsWith("ssh-")) { "Chave estranha em $pubArq"; exit 1 }
$ssh = "C:\Program Files\Git\usr\bin\ssh.exe"

# 1) PC1: liga o servidor ssh do Windows (não existia) e aceita a chave do desktop
if (-not (Get-Service sshd -EA SilentlyContinue)) {
  "PC1: instalando o servidor OpenSSH do Windows (leva 1-3 min)..."
  Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
}
Set-Service sshd -StartupType Automatic
Start-Service sshd
$ak = "C:\ProgramData\ssh\administrators_authorized_keys"   # usuário administrador: o Windows só lê este arquivo
if (-not (Test-Path $ak) -or -not (Select-String -Path $ak -SimpleMatch $pub -Quiet)) { Add-Content -Path $ak -Value $pub }
icacls $ak /inheritance:r /grant "*S-1-5-32-544:F" /grant "*S-1-5-18:F" | Out-Null   # Administradores + SYSTEM
"PC1: sshd " + (Get-Service sshd).Status + ", chave do desktop autorizada"

# 2) PC2 (Windows): mesma coisa no usuário de lá
$scr = "`$p = '$pub'; `$adm = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator); " +
       "`$f = if (`$adm) { 'C:\ProgramData\ssh\administrators_authorized_keys' } else { Join-Path `$env:USERPROFILE '.ssh\authorized_keys' }; " +
       "if (-not (Test-Path `$f) -or -not (Select-String -Path `$f -SimpleMatch `$p -Quiet)) { Add-Content -Path `$f -Value `$p }; " +
       "if (`$adm) { icacls `$f /inheritance:r /grant '*S-1-5-32-544:F' /grant '*S-1-5-18:F' | Out-Null }; 'PC2 ok: ' + `$f"
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($scr))
& $ssh -o BatchMode=yes -o ConnectTimeout=20 pc2 "powershell -NoProfile -EncodedCommand $b64"

# 3) Notebooks (Linux)
$lin = "mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && (grep -qxF '$pub' ~/.ssh/authorized_keys || echo '$pub' >> ~/.ssh/authorized_keys) && chmod 600 ~/.ssh/authorized_keys && echo ok"
"x200ma: " + (& $ssh -o BatchMode=yes -o ConnectTimeout=20 x200ma $lin)
"acer: " + (& $ssh -o BatchMode=yes -o ConnectTimeout=20 -o IdentitiesOnly=yes -i "$env:USERPROFILE\.ssh\id_rsa" emerson-ia@100.98.55.125 $lin)
""
"Pronto. No desktop teste: ssh pc1 hostname ; ssh pc2 hostname ; ssh x200ma hostname ; ssh acer hostname"
