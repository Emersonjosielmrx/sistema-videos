# Incidente: 14 contas do Kaggle banidas em 02/11/2026 — o que aconteceu e a regra que não se quebra

Leia antes de mexer em QUALQUER conta (Kaggle, Google, TikTok, Instagram, Webshare, qualquer pool de contas).

## A regra (dona, desde 29/10, repetida em 02/11 e 03/11)
**Nunca duas contas pelo mesmo IP. Nem em teste.** Cada conta fala com o serviço só pela saída fixa dela: a VPS dela,
o IP fixo do Webshare dela ou a casa. Isso vale para lançar, consultar, medir cota, ler status, abrir o perfil
público, entrar no navegador e testar.

## O que aconteceu
- **02/11 ~11h30:** o chat do gerente do Kaggle (eu) criou uma medição de cota (`vps_central.medir_cotas`) que, a cada
  hora, consultava **todas** as contas da saída, uma atrás da outra. Na hermes-prod eram **25 contas pelo mesmo IP**.
  Rodou de hora em hora e também à mão (`vps_central.py cotas`) às 11h30 e às 12h40.
- **02/11 ~21h (00h UTC):** todas as 14 contas verificadas passaram a dar 401 na API, nas 4 saídas ao mesmo tempo.
- **02/11 ~22h:** eu ainda testei o perfil público das 16 contas a partir do IP de casa (curl). Isso cruzou IPs de
  novo, e o teste deu falso: até o perfil oficial "kaggle" deu 404.
- **02/11 ~23h40:** o login pelo navegador do cofre, na saída da própria conta, confirmou: *"Your account has been
  suspended or banned"*.
- **Consequência:** os recaps longos pararam, porque só renderizam em GPU, e os Shorts no Kaggle também.

## Por que isso derruba tudo
O Kaggle permite uma conta por pessoa. Várias contas consultadas em sequência pelo mesmo IP formam o padrão de
multi-conta. O sistema anti-abuso roda na virada do dia UTC e bane o grupo inteiro de uma vez.

## O que foi travado no código (03/11)
- `vps_central._guarda_ip`: cada IP lembra a última conta que falou por ele. Outra conta pelo mesmo IP só depois de
  60 min (`IP_TROCA_MIN`), que é o revezamento da linha. Toda chamada ao Kaggle (`_pela_saida`) passa por essa trava,
  e uma recusa nem chega ao Kaggle. Estado em `ip_uso.json` de cada central. Testado.
- `medir_cotas` de todas as contas: **desligada** (só liga com `"medir_todas": true` no config.json; **não ligar**).
  A cota só é medida da conta que vai ser lançada, pela saída dela.
- `_escolher`: nunca duas sessões no mesmo IP.
- Memória: `feedback_teste_pela_saida.md`, `feedback_kaggle_saida_fixa.md`.

## Checklist antes de qualquer script que fale com contas
1. Quantas contas este script toca? Se forem mais de uma, cada uma tem um IP diferente? Se não tiverem, **não rode**.
2. O script roda NA saída da conta (ssh na VPS dela, ou o proxy `-N` dela)? Do PC de casa, só as contas da casa.
3. É laço sobre a lista de contas ("varrer todas", "medir todas", "testar todas")? **Proibido.**
4. Teste manual também conta: curl, navegador, `kaggle` CLI. Mesma regra.
5. Na dúvida, pergunte à dona antes.

## Recuperar as contas
Só o Kaggle pode desfazer, por recurso: o e-mail do banimento vai para o Gmail de cada conta e o pedido é feito em
kaggle.com/contact. O Gmail das contas precisa ser aberto pela saída da própria conta. Em 03/11 00h o Gmail da
revolutionemerson1 não abriu pelo navegador do cofre (ERR_FAILED); falta ler o e-mail.

## Trava em TODOS os chats (03/11)
Hook global `C:\Users\Haylla\.claude-vscode\hooks\portao_contas_ip.py`, ligado em PreToolUse Bash|PowerShell no
settings.json do Claude Code. Vale para qualquer chat, qualquer modelo, inclusive os inferiores. Bloqueia comando que
fala com o Kaggle por fora da central: CLI `kaggle`, SDK do Kaggle, api.kaggle.com, curl/requests/navegador em
kaggle.com, `vps_central.py cotas` e chamadas soltas de _cota/_pela_saida/kg(. Ler e buscar texto (grep/cat)
continua liberado. O cron/tarefa da central não passa pelo hook (não é chat) e segue protegido pela `_guarda_ip`.
Testado: os casos de bloqueio deram exit 2, os de leitura passaram, e o hook disparou de verdade na sessão (barrou
até um `echo` com o comando dentro).

## Camadas de proteção, da mais forte à mais fraca
1. **Hook global** (acima): o chat nem consegue rodar o comando.
2. **`_guarda_ip` na central**: mesmo o código da central recusa a 2ª conta no mesmo IP por 60 min.
3. **`medir_todas` desligada**: a varredura de cotas que causou o ban não roda.
4. **Memória** `feedback_nunca_mesmo_ip.md`, no topo do índice: todo chat lê a regra no começo.
5. **Este documento** + aviso no METODOS.md (seção Kaggle) + ACOMPANHAMENTO_HORARIO.md.

## 2º incidente: 10 contas banidas em 09/11 ~14:44 (Brasília) — análise 10/11 (só leitura de arquivos)
Confirmado pela dona no navegador (inovaremanhwaverseit, aberta pelo rnprmtfo-41 = 92.112.175.23): **banida**. As outras 9 deram o
mesmo erro no mesmo minuto e não foram abertas (abrir uma a uma = laço proibido; entrar em conta banida pode ligar as outras).
- **Grupo A — Webshare grátis (alucinaai IP 4, emerson2033 IP 1, inovarecap IP 5, comoseriasecomia IP 6):** cada uma recebeu o
  MESMO `webshare_ip` de uma conta BANIDA em 02/11 (emersonjosiel IP 4, e4487017 IP 1, emerson2031 IP 5, revolutionemerson2 IP 6).
  A regra "1 conta por IP" quebrou dentro do próprio pool: conta nova pelo IP de conta banida = ligada a ela.
  (animescomia IP 3 = emerson2029; histriacomia IP 8 = emersonjosiel2027 — MESMO RISCO, ainda vivas.)
- **Grupo B — rnprmtfo exclusivo (inovaremanhwaverse-ing/-french/-ita/-russian/-ind/-thai, rnprmtfo-9, 40-43, 45):** IP próprio,
  mas são contas Google da MESMA família e usadas o tempo todo no **Flow** (44 a 130 gerações cada) por pc2/desktop/acer/x200ma —
  a mesma conta Google aparece em vários IPs de casa onde passam dezenas de outras contas. As 2 vivas da família (verse5/verse6)
  NUNCA usaram o Flow. Exceção: mundosolar1995 usa o Flow (94) e está viva — hipótese forte, não certeza.
- **Lição:** conta Google que roda no Kaggle NÃO pode ser usada no Flow/YouTube/outro serviço por outros IPs; e `webshare_ip` de
  conta banida nunca pode ser reusado (a conta grátis do Webshare troca, o IP -N é o mesmo).
