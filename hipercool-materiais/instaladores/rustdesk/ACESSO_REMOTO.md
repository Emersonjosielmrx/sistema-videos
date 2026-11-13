# Acesso remoto ao Revision-PC (06/11/2026)

Tailscale IP: 100.118.234.102

## 1) RustDesk (recomendado: ve a MESMA tela, nao derruba a sessao)
- Versao 1.5.1, roda como servico (liga sozinho com o Windows)
- Conexao direta por IP ativada (porta 21118, firewall so libera a Tailscale 100.64.0.0/10)
- No outro aparelho: instale o RustDesk, no campo de ID digite: 100.118.234.102
- Senha fixa: zMQVUd8astNY
- ID publico (se um dia precisar sem Tailscale): 206119593

### Atalho pronto no desktop-su00b7v (06/11)
- Area de trabalho do Emerson: "Tela do PC1" -> abre e ja entra sozinho, sem digitar senha
- RustDesk portatil em C:\Users\Emerson\RustDesk\rustdesk.exe (ssh nao e admin la, entao nao instalou o MSI)
- Atalho = rustdesk.exe --connect 100.118.234.102 --password zMQVUd8astNY
- Mudou a senha aqui? refazer com atalho_cliente.ps1 desta pasta

## 2) Area de Trabalho Remota do Windows (RDP)
- Ja estava ligada; regra de firewall "RDP via Tailscale" criada
- Conectar em 100.118.234.102, usuario: Haylla + senha do Windows
- CUIDADO: ao entrar por RDP a tela fisica bloqueia e, ao sair, a sessao fica sem tela
  (pode quebrar automacoes que tiram print/usam Chrome). Prefira o RustDesk.
