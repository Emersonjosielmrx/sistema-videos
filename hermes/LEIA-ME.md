# Hermes Call — tudo o que é do Hermes no PC

Organizado em 12/10/2026. Antes cada coisa ficava numa pasta solta do `D:\` (`D:\hermes-call`,
`D:\hermes-wt\`, `D:\campanha-hermes`, `D:\credenciais-vps-hermes`, ...).

| Pasta | O que é | Pode mexer? |
|---|---|---|
| `pc-base\` | **Onde se trabalha.** Código novo, ramo `pc/v0.8.0`. Comece lendo o `CONTINUAR_DAQUI.md` daqui. Publicar: `bash ops/publicar.sh` a partir desta pasta. | Sim |
| `hermes-call\` | Repositório principal, ramo `main` = o que está **no ar**. O `.git` mora aqui (o `pc-base` é um worktree dele). | Não mude código aqui |
| `campanha\` | Campanha de ligações para vender o Hermes: plano, captação de empresas (CNPJ), conferências. Comece pelo `README.md` e `PLANO.md`. | Sim |
| `credenciais-vps\` | Kit para configurar o SSH das VPS em outro PC (chave + `ssh_config` + instruções). A chave em uso neste PC fica em `C:\Users\Haylla\.ssh\`. **Nunca enviar ao GitHub.** | Só copiar |
| `arquivo\` | Coisas antigas guardadas só como consulta (não estão em uso). | Não precisa |

## O que tem no `arquivo\`

- `experimento-bloqueio-2026-07\` — investigação de julho sobre o WhatsApp recusar chamadas (erro 439/463).
  O `APRENDIZADOS_E_ESTRATEGIAS.md` resume o que se descobriu. Os caminhos citados lá são os antigos.
- `hermes-router-plano\` — ideia (03/10) de um roteador de números para ligações em massa; nunca começou.
- `qa-playwright-2026-07\` — testes automáticos do painel feitos em julho, contra a versão antiga. Para rodar de
  novo: `npm install` dentro da pasta.
- `campanha-julho-2026\` — resultado de uma campanha de ligações de 15/07 (resumos de quem se interessou e a lista
  de números recuperados). Tem telefones: **nunca enviar ao GitHub.**

## O que foi apagado em 12/10 e por quê

- 10 worktrees velhos de `D:\hermes-wt\` (integracao, ligacoes, online, painel, pc-achados, pc-ops, pc-voz,
  seguranca, voz-audio, voz-conversa): todos já estavam juntados no `main` e sem nada pendente. Os ramos continuam
  no git (`git branch` no `hermes-call\`).
- Compilações antigas de julho/agosto (`hermes-call.exe`, `server.exe`, `bin\hermescall`, `hermes-dist.tar.gz`,
  `hermescall-20260730184115.tar.gz`, `_GOLDEN_v0.2.1\`) e os executáveis do experimento de bloqueio: foram para
  a Lixeira do Windows.
- Cópia repetida das credenciais (`D:\credenciais-vps-exportar`), `D:\temp\prod_auth.go` (já está no histórico do
  git) e `D:\tmp\pg-achados` (só sobrava o log do Postgres de teste).
