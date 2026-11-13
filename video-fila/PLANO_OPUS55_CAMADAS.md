# Plano final: Opus 5.5 (cc/claude-opus-5-5) em 2 modos, com botões na área de trabalho

Este plano revisa o plano anterior. Para revisar, só li o código e não chamei nenhum modelo.

## O que corrigi no plano anterior (conferido no código)

1. **`painel_ia._rodar` vai precisar de `base_url` e também de token por job.** Hoje ele lê `base_url` e `auth_token` do `claude_proxy.json`, que aponta para a porta :20128 do Kiro. Se mudar só a URL, o pedido sai para a :20133 com a chave errada. Por isso o job ganha um campo `rota`, com dois valores possíveis: `"padrao"` ou `"vscode"`. A rota `"vscode"` lê a URL e o token do `settings_5_OPUS-5.5_NORMAL.json` na hora do pedido. A chave nunca é copiada para o job, para o `.ps1` nem para o log.
2. **`ia_reserva._fora(...)` pode trocar o modelo sem avisar.** Se ele marcar `cc/claude-opus-5-5` como fora do ar, o modo ASSUMIR passa a rodar com Kiro ou com o modelo grátis, e ninguém percebe. No modo ASSUMIR, quando o modelo estiver fora, o certo é **parar e devolver o controle**, não trocar de modelo.
3. **O chat do modo 1 não pode usar `CLAUDE_CONFIG_DIR=.claude-vscode` com os hooks do usuário.** O `portao_final` e o `portao_agente` exigem planejador e revisor, e isso travaria a revisão. O próprio `painel_ia` já tira os hooks pelo mesmo motivo (comentário de 21/10). Então o chat usa `--setting-sources project,local` e os hooks de guarda do `painel_ia` (`_hooks`), e fica sem ferramentas de edição. O histórico da conversa fica em `estado\opus55\`. Dá para retomar com `claude --resume <id>` pelo mesmo `.ps1`, mas a conversa não aparece no VS Code. Isso é uma troca consciente.
4. **Não existe "ultracode" no CLI.** Quem decide o raciocínio é o modelo/rota ou a palavra **"ultrathink"** no prompt. Não conferi se o CLI 2.1.301 lê a variável `CLAUDE_CODE_EFFORT_LEVEL`. Por isso o plano faz assim:
   - coloca "ultrathink" no prompt;
   - usa `--model cc/claude-opus-5-5`;
   - libera a ferramenta `Task` (subagentes) só no modo ASSUMIR.
   
   Antes de usar a variável, confirmo com `claude.exe --help`, que roda localmente e não gasta nada.
5. **Pausar o motor com `ligado=False` não faz o `passo()` parar inteiro.** Nesse caso ele continua chamando o `auditoria_final.ciclo` e a vigia da produção. O ASSUMIR precisa de uma marca própria (`estado\opus55_ASSUMIU`). Enquanto ela existir, o `passo()` pula o `auditoria_final.ciclo` e não dispara pedido novo. As vigias de produção continuam rodando.
6. **O teto é contado em pedidos e em %, e não em tokens.** O `quota_snapshots` é por conta e tem atraso: algumas contas tinham leituras com mais de 15 horas. Não dá para medir o gasto em tokens com confiança. O teto fica:
   - em N pedidos por dia;
   - em "parar se a soma da semana nas contas utilizáveis ficar abaixo da reserva da dona", com padrão de 15%.
   
   Leitura com mais de 30 minutos conta como "sem cota".
7. **O `dona_usando_opus` hoje só reconhece `opus-4-6`.** O padrão passa a ser `claude-opus-(4-6|5-5)`. O `exigir_modelo` da 3ª camada continua `opus-4-6`.
8. **Não pegar os "31 achados" automaticamente.** Vários são de risco ou dependem da dona. O ASSUMIR só pega:
   - itens do backlog do motor;
   - achados que a dona marcar como `auto` numa lista `estado\opus55_fila.json`.
9. **Dois agentes ao mesmo tempo.** A trava do orquestrador guarda o PID e é conferida pelo PID. Se a trava ficar órfã, ela é limpa só depois de confirmar que o PID morreu. Nenhum processo é morto, e o `pythonw` nunca.

## Modo 1: REVISAR AGORA (botão)

- **Atalho:** `Opus 5.5 REVISAR AGORA.lnk`, que chama `revisao_opus55_botao.ps1`. Abre uma janela visível.
- **`revisao_opus55.py preparar`:** monta o dossiê desde `estado\opus55_ultima.json` e grava em `estado\opus55\<id>_dossie.md`. Entra no dossiê:
  - o `pacote_revisao()`;
  - os jobs do `painel_ia` com status;
  - os vereditos de `estado\opus\*.json`;
  - as reprovações;
  - o `_erros_novos`.
  
  Antes, preciso corrigir o corte por bloco do `montar_dossie`, citado no achado do `CAMADAS_MELHORIAS_24OUT.md`. Limite total de cerca de 120 mil caracteres. O que passar disso vira lista com caminho do arquivo.
- **`cota_claude.tem_cota()`:** se não houver conta com sessão e semana sobrando, abre uma janelinha avisando e para.
- **O chat:** roda `claude.exe --model cc/claude-opus-5-5 --setting-sources project,local --disallowedTools Edit,Write,MultiEdit,NotebookEdit --append-system-prompt-file regras_revisor.md "Leia @...dossie.md. ultrathink. Relatório: ..."`.
  - URL e token vêm do settings_5 só no `env` do processo.
  - Abre no Windows Terminal, ou no `cmd` se não houver.
  - O chat fica aberto para ela perguntar. Ela fecha com /exit.
- **Formato do relatório:**
  - o que mudou;
  - o que ficou bom;
  - os problemas (arquivo, risco e sugestão);
  - o que precisa dela;
  - e por fim "quer perguntar algo?".
- **Fim da sessão:** a marca `ultima` só avança quando a sessão termina sem erro.

## Modo 2: ASSUMIR (LIGAR e DESLIGAR)

- **Atalhos:** `Opus 5.5 ASSUMIR LIGAR.lnk` e `Opus 5.5 ASSUMIR DESLIGAR.lnk`, que chamam `opus55_assumir_botao.ps1 ON|OFF`. É o mesmo modelo do `camada_opus_botao.ps1`.
- **Ligar:**
  1. Grava `opus55_ASSUMIU` com a hora, o teto e o estado anterior do motor e da 3ª camada.
  2. Põe `ligado=False` no motor e roda `camada_opus.desligar()`.
  3. Abre a janelinha com a cota e o teto.
- **`opus55_assumir.py` (pythonw, com trava por PID):** a cada ciclo de 5 minutos faz o seguinte.
  1. Confere a cota. Se não estiver OK, faz uma de duas coisas:
     - **espera**, se a sessão de 5 horas zerou mas a semana ainda tem cota (esse é o "trabalhar quando liberar token");
     - **devolve**, se a semana acabou ou se o teto foi atingido.
  2. Se `dona_usando_opus()` disser que ela está usando, espera.
  3. Pega um item do backlog ou da `opus55_fila.json` e roda `painel_ia.pedir(tipo="propor", modelo="cc/claude-opus-5-5", rota="vscode", voltas=80, auto_aplicar=True)`.
     - A guarda, o backup, o `desfazer` e as `TRAVAS_VIGIAS` continuam valendo.
     - O prompt leva "ultrathink" e libera `Task`.
  4. Depois de aplicar, abre uma **sessão nova** para revisar só o diff (`_pedir_revisao`). Se reprovar, roda `desfazer` e grava uma lição.
- **Devolver o controle** quando: ela aperta DESLIGAR; a marca some; aparecem duas leituras sem cota; a resposta é 402, 429 ou "reached the limit"; o modelo fica fora do ar.
  1. Espera o pedido atual terminar (até 45 minutos).
  2. Restaura **exatamente** o `ligado` do motor e da 3ª camada como estavam antes.
  3. Apaga a marca.
  4. Manda um aviso pelo `avisos.py` com as feitas, as desfeitas e o motivo.
- **Configuração no `melhoria_continua.json`:**
  - `opus55_max_dia: 10`
  - `opus55_max_hora: 2`
  - `opus55_reserva_pct: 15`
  - `opus55_voltas: 80`
- **Status:** aparece em "melhorias status", no painel e na janelinha.

## Medidor de cota: `cota_claude.py` (só lê)

- **De onde lê:** o mesmo SSH do `monitor_opus` (`hermes-bloqueio`, `BatchMode`), com o SQLite em `mode=ro`. As tabelas são `provider_connections` (com `is_active=1` e sem `rate_limited_until` no futuro) e `quota_snapshots` (`session (5h)` e `weekly (7d)`).
- **Funções:**
  - `ler()`
  - `tem_cota()`
  - `liberou(antes, agora)`
  - `quase_vencendo(horas=24, minimo=30)`, que é só um **aviso** para a dona ("vale ligar o ASSUMIR") e não liga nada sozinho
  - `sobra_total()`
- **Onde grava:** `estado\cota_claude.json`, gravado de uma vez (escreve num arquivo temporário e troca).
- **Quando roda:** dentro do `monitor_opus` (a cada 10 minutos), sem criar Tarefa nova.

## Arquivos

- **Novos:**
  - `cota_claude.py`
  - `revisao_opus55.py`
  - `regras_revisor.md`
  - `revisao_opus55_botao.ps1`
  - `opus55_assumir.py`
  - `opus55_assumir_botao.ps1`
  - os 3 atalhos `.lnk`
- **Alterar:**
  - `painel_ia._rodar`: `rota` (URL e token), liberar `Task` e "ultrathink" quando `job.modo=="assumir"`, e no ASSUMIR não trocar de modelo sozinho;
  - `painel_ia.pedir`: aceitar `rota` e `modo` e herdá-los na aplicação, como já faz com `modelo_fixo`;
  - `auditoria_final.dona_usando_opus`: reconhecer 5-5;
  - `auditoria_final.montar_dossie`: limite por bloco;
  - `melhoria_continua.passo` e `status`: respeitar a marca `opus55_ASSUMIU`;
  - `monitor_opus.py`: chamar o `cota_claude`;
  - LEIA-ME de modelos: avisar que o 5-5 já funciona (visto no `portao_final.log` em 24/10).

## Testes sem gastar

1. `cota_claude.py --seco` tem de bater com a consulta SQL. Leituras fixas (fixture) testam `liberou`, `quase_vencendo` e leitura velha.
2. `revisao_opus55.py preparar --seco` mostra o tamanho e os itens.
3. Os `.ps1` com um `claude.exe` falso que só repete os argumentos. Confirmar que o token não aparece em nenhum log.
4. LIGAR e DESLIGAR numa pasta de estado temporária: o estado tem de voltar idêntico.
5. Cota fixa em 0%: ele tem de devolver o controle. Sessão em 0% e semana com cota: ele tem de esperar.
6. `guarda_decidir` com comandos proibidos dentro de um job `modo=assumir`.
7. `claude.exe --help`: ver se existe flag ou variável de esforço.

## Ordem de implementação

1. `cota_claude.py`
2. `dona_usando_opus` e `montar_dossie`
3. Modo 1, que a dona valida
4. `rota` e `modo` no `painel_ia`
5. `opus55_assumir.py` a seco
6. Os botões
7. Primeira rodada real com ela presente e `max_dia=3`
8. Atualizar os documentos

## Perguntas que só a dona responde

1. A **reserva** para ela usar no VS Code: 15% da semana está bom?
2. No modo 1, ela aceita que o chat **não apareça no VS Code**, ficando só na janela e retomável pelo botão?
3. O ASSUMIR pode **aplicar sozinho** (com revisão e desfazer), ou só propor e esperar ela aprovar?
4. Quais dos 31 achados podem entrar na fila automática?
5. O "ultracode" que ela quis dizer é raciocínio máximo com subagentes, ou é alguma rota ou comando específico do OmniRoute?
6. O teto de pedidos por dia no ASSUMIR: 10 está bom?
