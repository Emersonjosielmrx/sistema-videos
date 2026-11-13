# Melhorias contínuas: 3 camadas (24/10) — estado e o que falta

## LIGADO AGORA
- **Camadas 1 e 2 (Kiro + Gemini, 24 h):**
  - busca em dupla, com votante C (Kiro adversário) quando o Gemini não vota;
  - críticos do PLANO (Gemini e Kiro) antes de aplicar;
  - 3 revisores: Gemini, Kiro adversário e Kiro do checklist;
  - ANÁLISE/CHECK obrigatório (aprovação sem ANÁLISE não vale);
  - Kiro com marcas de raciocínio e linha AGORA (Brasília e UTC).
- **Guarda de comandos** (`painel_ia.py guarda` + `config\melhoria_guarda.json`): bloqueia pip, mover mídia, tarefas, postagem e cookies, também em Edit/Write.
- **3ª camada, o Opus 4.6 como juiz final** (`auditoria_final.py` + `camada_opus.py`):
  - só roda com o monitor fresco, 3 ou mais contas com crédito e a dona sem usar o Opus no VS Code;
  - o botão na área de trabalho LIGA/DESLIGA. Também dá pelo Telegram: `melhorias opus ligar|desligar`.
- **Monitor:** `D:\monitor_opus.py` agora grava `leitura` (com_credito, hora).

## Testes (todos passam)
`D:\veo\venv\Scripts\python.exe` em `D:\video-fila\testes\`: `teste_motor_camadas.py`, `teste_guarda.py` e `teste_camada_opus.py`.

## Backups (para voltar)
`*.bak_20261024_camada3`, `*.bak_20261024_fase0`, `*.bak_20261024_guarda_escrita` e `*.bak_20261024_voltas`, em `D:\video-fila` e `D:\monitor_opus.py.bak_20261024_camada3`.

## Funcionando de verdade (conferido no log às 10:20 de 24/10)
- O motor novo já roda com as camadas.
- O crítico do plano (Gemini) **reprovou um plano com premissa falsa** (`creditos_contas.ordenar`) antes de aplicar, e o plano foi refeito com a crítica.
- O executor passou a responder STATUS: OK quando o item já estava resolvido. Ele confere antes de mexer.
- O Gemini, com 40 voltas, está entregando no formato.

## Pendente
1. A revisão adversária (workflow `wf_48c91cc4-cbb`) estava rodando. Quando voltar, leia o resultado em
   `C:\Users\Haylla\AppData\Local\Temp\claude\D--hermes-pc-base\f1234ce5-cf67-48e8-bb52-694fa47ea18c\tasks\w563u6evo.output`
   e corrija os achados confirmados.
2. Primeira janela real do Opus: conferir `auditoria_opus\INDICE.md`, o `primeiro_byte_s` e os tokens; calibrar `opus_primeiro_byte_s` e `opus_chamadas_dia_max`.
3. Conferir no log (`logs\melhoria_continua.log`) que o Gemini com 40 voltas e o Kiro com raciocínio estão terminando no formato.
4. Prováveis falsos positivos da guarda: `import mr.publish` / `import postar_hipercool` só para ler dados.
5. Pendente da dona: decidir se tira do ar o cap 5 e os 2 Shorts do cap 1 do hipercool, que subiram 2 h antes do fim do congelamento.

## CORRIGIDOS em 24/10 ~11:10 (os 31) — ver CAMADAS_PROGRESSO_24OUT.md
Backups `*.bak_20261024_achados`. Testes: teste_guarda, teste_motor_camadas, teste_camada_opus e o novo
`testes\teste_achados_24out.py` — todos TUDO OK. O motor e o bots_conversa pegam o código novo na próxima janela
`--rodar 39`; o hook da guarda já vale (processo novo a cada passo).
Ficou de fora: 17 "VIGIA_DIARIO único alvo"; 12 só vale para Write de script NOVO/temp; 2 parte opcional.

## Achados CONFIRMADOS da revisão adversária (24/10: 31 de 40)
1. [alta] O aviso da auditoria pra dona (DONA, DESFAZER sem prova, não consegui desfazer, fora de arquivo) nunca chega no Telegram — D:\video-fila\auditoria_final.py 512 (_para_dona: e["entregar"].append(jid)); D:\video-fila\bots_conversa.py:191 e 195
   - correção: Em _para_dona, gravar e['auditoria_dona'][jid]['enviado']=False. Em bots_conversa._entregar, para um jid de para_entregar() que já existe com avisado=True e tem auditoria_dona com enviado=False, voltar avisado para False e, depois de mandar, marcar enviado=True. Isso evita duplicar o '✅'. bots_conversa.py é NÚCLEO: a mudança é feita à mão.
2. [media] REFAZER do Opus colocado em e['refazer'] é sobrescrito por uma reprovação de outro item: desfaz e nunca refaz — D:\video-fila\auditoria_final.py 551-556; melhoria_continua.py:1113 (_reprovado) e 1181 (_terminou_critica)
   - correção: No ramo REFAZER de _agir_um, mandar sempre para o topo do backlog com opus=True (bl.insert(0, novo); _gravar). O _pegar_item já põe esses na frente. Não usar e['refazer']. Opcional: em _reprovado e _terminou_critica, se e['refazer'] estiver ocupado, mover o item que estava lá para o backlog antes de sobrescrever.
3. [media] REFAZER do Opus não tem teto: tentativa volta a 1 e o ciclo desfaz/refaz pode durar dias — D:\video-fila\auditoria_final.py 548-550
   - correção: Em _agir_um, antes de desfazer no ramo REFAZER: n = sum('auditoria Opus' in str(k) for k in item.get('criticas') or []). Se n >= int(c['tentativas_max']) - 1, chamar _para_dona(e, ent, v, f'o Opus já mandou refazer {n} vez(es)') e não desfazer.
4. [media] P0 que vira 'nao_auditado' sem outro item pendente: o auditor reserva nunca roda e a dona não é avisada — D:\video-fila\auditoria_final.py 724-726 (retorno antecipado 'nada na fila') e 732-733 (_reserva só quando not ok)
   - correção: Em ciclo(), chamar _reserva(e, c) também antes do return de 'nada na fila' e quando ok mas nenhum lote saiu. Em _colher, quando um P0 virar nao_auditado, mandar um _m()._avisar(...) curto.
5. [baixa] Exceção ao executar um veredito marca o item como 'dona' em silêncio (sem mensagem, sem auditoria_dona) — D:\video-fila\auditoria_final.py 534 (int(v.get('confianca') or 0)) e 590-592 (except -> ent['estado']='dona')
   - correção: Ler a confiança com try: conf = float(str(v.get('confianca') or 0).replace(',', '.')), e em ValueError usar conf = 0. No except do _agir, chamar _para_dona(e, ent, ent.get('veredito') or {}, f'a auditoria não conseguiu agir ({type(ex).__name__})') em vez de só mudar o estado.
6. [media] Crítico e revisor sem veredito válido contam como aprovação: plano 'aprovado por 0 de 2' é aplicado — D:\video-fila\melhoria_continua.py 1208-1211 (_terminou_critica) e 1331-1332 (revisores: 'sem revisão')
   - correção: Em _terminou_critica, se nenhum veredito for APROVADO no fim da fila, chamar o crítico C (Kiro adversário) uma vez. Se ainda assim ninguém aprovar, seguir o ramo da DÚVIDA (pergunta pra dona: 'nenhum crítico respondeu no formato'). Nos revisores, quando não houver nenhum veredito válido, gravar e['duvidas'][ap['id']] e aceitar com nota 'revisão em dúvida: ...'. Assim o item vira P0 e a dona recebe o 🤔.
7. [media] Auditor reserva roda com as melhorias PARADAS e, ao terminar, zera a pausa/espera do motor — D:\video-fila\auditoria_final.py 613-620 (_reserva não olha ligado nem proxima_em); melhoria_continua.py:1232 (_fim_de_rodada(e, c, 0))
   - correção: No começo de _reserva: if not c.get('ligado') or not c.get('opus_camada'): return False. No ramo auditor_reserva de _terminou_papel, não mexer em proxima_em: trocar _fim_de_rodada(e, c, 0) por uma limpeza sem mudar a espera (por exemplo, pausa = max(0, (e.get('proxima_em', 0) - time.time()) / 60)).
8. [baixa] PRECISO_VER 'log:caminho:texto' quebra quando o texto procurado tem ':' (hora, 'ERRO:') — D:\video-fila\auditoria_final.py 337-341
   - correção: Trocar o parse por mm = re.match(r'^log:\s*([A-Za-z]:[^:]*|[^:]*):(.*)$', ped, re.S); caminho, procura = mm.group(1).strip(), mm.group(2).strip().
9. [baixa] Desfazer automático (revisor, Opus, vigia, aplicação quebrada) fica registrado como 'pelo dono no painel' — D:\video-fila\melhoria_continua.py 398 (_desfazer chama painel_ia.desfazer(job['id']) sem quem)
   - correção: _desfazer(job, motivo, quem='melhorias contínuas (motor)') repassa quem= só se 'quem' estiver em inspect.signature(painel_ia.desfazer).parameters, como já faz o _pedir. A auditoria_final passa quem='auditoria final (Opus)'. No bots_conversa (NÚCLEO, à mão), passar quem='dona'.
10. [baixa] Prompt da dona com mais de 974 caracteres corta a regra [PERGUNTA] (gastar dinheiro) e o CHECK do executor — D:\video-fila\melhoria_continua.py 1741 (comando: prompt[:3000]); painel_ia.py:224 (pedido[:4000])
   - correção: Em comando(), limitar o prompt salvo a ~700 caracteres e dizer à dona que cortou, ou mandar o «prompt» no CONTEXTO. Subir a linha do [PERGUNTA] para antes do <<CHECK>>. No _pedir, se len(pedido) > 4000, cortar o prompt e nunca o fim.
11. [alta] Guarda contornada por interpretador com o comando entre aspas (powershell -Command, bash -c, cmd /c, iex) — D:\video-fila\painel_ia.py 922 (_INTERP), 1065-1088 (_vistas_comando); regras fora_aspas em config\melhoria_guarda.json linhas 24, 25, 30, 35, 43, 44, 46
   - correção: Em _vistas_comando, quando classe == 'interp', pôr o texto entre aspas sem as marcas \x01/\x02 (ele entra nas duas vistas). Incluir iex, invoke-expression, start-process e saps em _INTERP. Acrescentar ao teste_guarda.py os casos acima.
12. [alta] Script escrito e depois rodado passa por toda a guarda (heredoc pra /tmp, ou Write de .py no aplicar) — D:\video-fila\painel_ia.py 966-985 (_tirar_heredoc), 1124-1132 (Edit/Write), regra permitir de arquivo temporário em melhoria_guarda.json linha 19
   - correção: Em _tirar_heredoc, manter o corpo quando a linha redireciona (> / >> / tee) para um arquivo que não seja o VIGIA_DIARIO.md. Em guarda_decidir, para Edit/Write/MultiEdit de .py/.ps1/.bat/.cmd/.sh, testar content/new_string contra 'bloquear' como texto de interpretador.
13. [media] Lote do Opus disparado no ciclo() some do estado se o passo() cair depois: o teto não conta e o lote é disparado de novo — D:\video-fila\melhoria_continua.py 1554-1559 (ciclo antes de qualquer _gravar), 1318-1320 (_pedir_revisao sem try); auditoria_final.py 404-428
   - correção: No passo(), logo depois de auditoria_final.ciclo(e, c), chamar _gravar(ESTADO, e) dentro do mesmo try. Ou gravar o estado no fim de _disparar.
14. [baixa] Chave do gateway (ANTHROPIC_AUTH_TOKEN no ambiente do agente) sai por vários comandos, e o registro da guarda não mascara chave de 35 caracteres — D:\video-fila\config\melhoria_guarda.json 32 (regra de variáveis de ambiente); painel_ia.py 721 (env do agente), 1161 (_cmd_curto)
   - correção: Ampliar a regra 32: '\bset\s*$' depois de cmd /c, 'export' sem argumento, 'os\.getenv|os\.environ', 'GetEnvironmentVariables?', '-Path\s+Env:', 'process\.env' e o nome literal 'ANTHROPIC_AUTH_TOKEN'. Em _cmd_curto, usar as mesmas trocas do camada_opus._limpar ((?:sk|pk|rk)-[\w-]{8,}, Bearer, x-api-key).
15. [media] Busca recursiva lê segredos e cookies: a guarda só olha o caminho escrito no comando — D:\video-fila\painel_ia.py 1109-1112 e 1133-1149 (segredos só no texto do comando e no path/glob); melhoria_guarda.json linhas 4-12 e 39-40
   - correção: Em 'segredos', incluir os .jsonl do painel que têm o conteúdo do cookies.txt (ou estado[\\/]painel_ia[\\/][^\\/]*\.jsonl). Para grep/rg/findstr/Select-String recursivos e para Grep/Glob, bloquear quando a raiz da busca contém uma pasta secrets, a não ser que a busca exclua secrets e *cookie*.
16. [baixa] Dossiê e documentação do Opus sem limpeza de segredo: o PRECISO_VER lê qualquer arquivo, inclusive o .jsonl com cookies — D:\video-fila\auditoria_final.py 330-359 (_ler_trechos), 389-400 (montar_dossie), 666-682 (_documentar_lote); melhoria_continua.py 587-603 (_comandos)
   - correção: Limitar _ler_trechos aos arquivos do manifesto do item, aos backups e às pastas logs\ do projeto, e recusar estado\painel_ia\*.jsonl. Passar o texto final de montar_dossie por um limpador (o _limpar do camada_opus mais as linhas de cookie Netscape) antes de gravar e mandar.
17. [media] Edit/Write no NÚCLEO e na config da guarda não são barrados; config quebrada desliga a guarda — D:\video-fila\painel_ia.py 1124-1132 (Edit/Write só testa segredos e mídia), 1217-1219 (hook: sem config ou ligado=false -> return 0); melhoria_guarda.json linha 17
   - correção: Em guarda_decidir, para Edit/Write/MultiEdit, bloquear quando Path(alvo).name estiver no NÚCLEO (inclui melhoria_guarda.json) ou o caminho tiver .claude[\\/]settings. No hook, para job de melhoria, config ilegível = exit 2 (fechar, não abrir). Nos permitir do VIGIA_DIARIO, exigir que ele seja o único alvo.
18. [media] Papéis 'só leitura' (buscador, votante, críticos, revisores, auditor reserva, propor) podem gravar, mover e apagar pelo terminal — D:\video-fila\painel_ia.py 1113 (bloquear_aplicar só quando aplicar=True), 1230 (eh_aplicar = tipo == 'aplicar')
   - correção: No hook_guarda, para job de melhoria do tipo pergunta ou propor, aplicar também 'bloquear_aplicar'. Acrescentar em 'bloquear': \brobocopy\b[^\n]*\s/(?:MOVE?|MIR|PURGE)\b e \bgit\b[^\n]*\s(?:rm|mv|checkout\s+(?!-b)\S|restore|stash(?!\s+list))\b.
19. [media] Porta lateral do painel: POST em 127.0.0.1:8790 roda tarefa agendada, muda controle e desfaz forçado, e a guarda só anota 'suspeito' — D:\video-fila\config\melhoria_guarda.json 51 (curl POST só em 'suspeito'); painel_controlador.py 869-885 (api_tarefa_rodar: Start-ScheduledTask), 1840 (api_controle_mudar), 1081-1093 (api_ia_acao desfazer forcar)
   - correção: Em 'bloquear', sem exec nem fora_aspas: (?:127\.0\.0\.1|localhost):8790/api/(?:tarefa_rodar|controle|ia_acao|ia_pedir|ia_corrigir_todos|abrir)\b|X-Painel.
20. [baixa] Botão DESLIGAR não para o lote no caminho sem stream (resposta 400 ao stream), e a janela diz 'Pode usar o Opus' — D:\video-fila\camada_opus.py 372-377 (repete sem stream), 477-502 (_ler_inteiro não olha desligada()), 591 (mensagem do desligar)
   - correção: Em _ler_inteiro, depois do read: if self.respeitar and desligada(): return self._fechar('desligado', 'a dona desligou durante a resposta sem stream'). No desligar(), se o lote vivo estiver com sem_stream, avisar que ele pode levar até o teto.
21. [media] Regra de mídia com dois lookaheads é O(n²): comando de 20 KB leva 18 s e o de 60 KB leva 153 s (o hook tem 60 s) — D:\video-fila\config\melhoria_guarda.json 33 (gravar por cima de mídia com .save/imwrite)
   - correção: Ancorar as lookaheads: depois do comentário, (?#...)\A(?=[\s\S]*(?:...))(?=[\s\S]*(?:...)). Revisar as outras regras com [\s\S]*. Pôr 'timeout' explícito na entrada do hook da guarda em _hooks.
22. [baixa] Hook de backup roda junto com a guarda: Write bloqueado em cookies ou mídia ainda copia o arquivo para o backup e entra no manifesto — D:\video-fila\painel_ia.py 617-628 (_hooks: duas entradas PreToolUse que casam Edit/Write), 865-896 (hook_backup não consulta a guarda)
   - correção: No hook_backup, para job de melhoria, chamar guarda_decidir(nome, ent, aplicar=True) e não copiar se der bloquear. Outra saída: juntar os dois num hook só (a guarda decide, depois faz o backup).
23. [baixa] Veredito PRECISO_VER com 'ver' que não é lista trava a camada para sempre — D:\video-fila\auditoria_final.py 470-471 (_colher chama _ler_trechos(v.get('ver'))), 333 ((pedidos or [])[:3] fora do try)
   - correção: No _colher: ver = v.get('ver'); ver = ver if isinstance(ver, list) else []. Pôr try/except por veredito (o que falhar vai para a dona) e zerar e['opus']['lote'] antes de distribuir. Em _ler_trechos, aceitar só uma lista.
24. [media] Dossiê do Opus cortado em silêncio: com 4 aplicações reais o 4º item perde o fim do DIFF e os ERROS NOVOS — D:\video-fila\auditoria_final.py 389-400 (montar_dossie: return texto[:opus_dossie_max_chars]); 369 (_diff limite=8000)
   - correção: Em montar_dossie, dar cota (opus_dossie_max_chars - len(cab)) // len(ents) a cada bloco, cortando primeiro o diff e escrevendo '[CORTADO: N caracteres]'. Outra saída: tirar do lote o item que não couber inteiro.
25. [media] Revisores B, C e A recebem só ~840 caracteres do diff porque as lições [FIXA] passam do limite — D:\video-fila\melhoria_continua.py 1025-1030 (_pedir_revisao) e 556-576 (_licoes: as [FIXA] entram sem respeitar 'limite')
   - correção: Em _pedir_revisao, pôr o DIFF logo depois do item, com cota fixa (_corta(diff, 2500)), e deixar LIÇÕES e NÃO MEXER no fim, onde o ctx[:6000] corta. Listar sempre os nomes de todos os arquivos mudados antes do diff.
26. [baixa] dona_usando_opus não vê o uso real: olha só os últimos 64 KB e as linhas do .jsonl passam de 500 KB — D:\video-fila\auditoria_final.py 220-236
   - correção: Ler de trás para frente em blocos (1 MB, até ~8 MB) até achar o ÚLTIMO '"model":"..."' e decidir por ele.
27. [baixa] monitor_opus.py: os.replace sem nova tentativa quebra o monitor da dona quando alguém está lendo o JSON — D:\monitor_opus.py 81-85 (salvar_estado)
   - correção: Em salvar_estado, repetir o os.replace até 20 vezes com time.sleep(0.1) quando der PermissionError, como em camada_opus._gravar_json. É sistema da dona: mudar com cópia antes.
28. [baixa] Aplicação que termina em erro/parado (inclusive morta pelo vigia novo) e rodou comandos não passa por revisão nem auditoria, e a dona não fica sabendo — D:\video-fila\melhoria_continua.py 1387-1404
   - correção: Nesse ramo, se não houver manifesto e _comandos(jid, 600) não vier vazio, mandar o mesmo _avisar do _reprovado. Chamar também auditoria_final.enfileirar(e, c, atual, 'parou no meio') para entrar como P0.
29. [baixa] P0 'só rodou comandos' pega aplicação que só leu, porque o append no VIGIA_DIARIO é obrigatório e conta como comando — D:\video-fila\auditoria_final.py 164-167 (_prioridade)
   - correção: Em _prioridade, só contar comandos de classe 'outro' ou 'interp' em painel_ia._vistas_comando, tirando o append do VIGIA_DIARIO, ou os que estão em suspeitos/bloqueios. Aplicação só de leitura não vira P0.
30. [baixa] O 'quem' da auditoria reserva fica gravado e assina depois o veredito do Opus — D:\video-fila\auditoria_final.py 658 (ent['quem'] = 'auditoria reserva ...') e 510 (_para_dona usa ent.get('quem'))
   - correção: Passar quem como parâmetro de _para_dona (o padrão é 'Auditoria final (Opus)'; terminou_reserva passa o da reserva) e não guardar em ent['quem'].
31. [baixa] DESFAZER/REFAZER numa aplicação sem arquivo mudado manda à dona o motivo errado 'o arquivo mudou depois' — D:\video-fila\auditoria_final.py 536-542 e 546-562
   - correção: Antes de chamar _desfazer, nos ramos DESFAZER e REFAZER: se not ap.get('manifesto'), chamar _para_dona(e, ent, v, 'não mudou arquivo: só rodou comandos; o que voltar está em fora_de_arquivo').

## Situação dos 31 achados (conferido em 24/10, fim do dia)
- **Os 31 estão corrigidos no código.** 30 foram feitos pelo outro agente, com testes em `testes\teste_achados_24out.py`.
- **O 19 foi terminado nesta sessão.** A regra antiga só barrava algumas rotas do painel. A nova bloqueia qualquer POST/PUT/DELETE em `127.0.0.1:8790`, por curl, PowerShell ou python. A leitura (GET) continua liberada.
  - Na primeira versão, a regra tinha um `(?i)` no meio, que o Python recusa. Por isso ela era ignorada sem aviso. Já foi trocado por `(?i:...)`.
  - Conferi as 37 regras e todas compilam.
- **Testes, todos passando:** `teste_motor_camadas.py`, `teste_guarda.py`, `teste_camada_opus.py` e `teste_achados_24out.py`.
- **Pendente:** pôr no `teste_guarda.py` uma checagem de que toda regra do `melhoria_guarda.json` compila. Hoje uma regra que não compila deixa a guarda aberta, sem aviso.

## Opus 5.5 (24/10, tarde) — implementado
- **Conferido sem gastar:** `cc/claude-opus-5-5` (e as variantes de -low a -xhigh) está no catálogo da 20133. O Claude Code 2.1.301 tem `--effort max`.
- **`cota_claude.py`** (só lê, por ssh `hermes-bloqueio`): grava `estado\cota_claude.json` com contas com cota, sobra da semana e "quase vencendo" (30% ou mais da semana sobrando e renovando em até 24 h).
- **Modo 1, REVISAR AGORA:** `revisao_opus55.py` monta o dossiê das aplicações desde a última revisão, e `opus55_revisar.ps1` abre o Opus 5.5 (esforço max, sem edição, comandos pedem permissão) com o chat na janela.
  - Atalhos: "Opus 5.5 REVISAR AGORA" e "Opus 5.5 continuar ultima revisao".
  - **Ainda não foi testado com o modelo de verdade:** o primeiro teste é a dona apertando o botão.
- **Modo 2, ASSUMIR:** `opus55.py` + `painel_ia.pedir(rota="vscode", esforco=...)`. Com o botão ligado e com cota, todo pedido das melhorias vai para o Opus 5.5.
  - Fica de fora a reserva de 15% e há teto de 10 pedidos por dia.
  - Sem cota, volta sozinho ao Kiro + Gemini.
  - Avisa 1 vez por dia se há token quase vencendo.
  - Atalhos: "Opus 5.5 ASSUMIR LIGAR (tokens vencendo)" e "Opus 5.5 ASSUMIR DESLIGAR".
- **Detecção:** `auditoria_final.dona_usando_opus(versao="5-5")` já reconhece o Opus 5.5 (as cotas do 4.6 e do 5.5 são diferentes).
- **Backups:** `*.bak_20261024_opus55`.
- **Falta:**
  1. as respostas da dona (reserva 15%? teto 10? o ASSUMIR aplica sozinho? o chat fora do VS Code está ok?);
  2. o primeiro uso real dos dois modos;
  3. subagentes ("ultracode") no ASSUMIR: hoje ele usa esforço max no fluxo de várias camadas, mas sem subagentes dentro de cada pedido.

## 29/10 — aviso da outra sessão (Fable)
- Existe agora um **melhorador central** (`D:\video-fila\melhorador_central.py`, doc `MELHORADOR_CENTRAL.md`, tarefa MelhoradorCentral a cada 10 min, botões na Área de Trabalho). Começa **desligado, em sombra**. Não mexeu em `painel_ia.py`, `melhoria_continua.py`, `monitor_opus.py` nem `camada_opus.py`.
- **Encaixe sugerido para a auditoria do Opus:** depois de cada rodada de linha, lendo `estado\central\estado.json` ("rodadas"). Ainda não ligado — fazer quando a dona pedir.
