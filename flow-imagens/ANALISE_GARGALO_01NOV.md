# Flow imagens — por que só saíam ~6 imagens/hora (análise 01/11/2026 21h, pedido da dona)

Uma imagem que dá certo leva 60–200 s (Chrome aberto ~80 s só pro token, o resto é o Flow por HTTP). Em 2 h de noite
saíram ~12. O tempo vai embora ESPERANDO máquina e em tentativa que não serve. Contagem das últimas falhas
(`logs\pedidos_falhos.jsonl`, uma falha pode citar várias máquinas):

| Onde | Motivo | Peso | O que foi feito / falta |
|---|---|---|---|
| x200ma, acer | OCUPADO (um Chrome por vez — certo nos notebooks) por Veo, TikTok, carrossel; o acer também exibe vídeo no telão | maior | nada a mudar (regra da dona); não mandar mais pedido pra eles |
| desktop | só 1 Chrome (porta 9460), disputada com a "vez do Veo" | grande | **FEITO 01/11 21h**: imagem usa portas extras 9470–9472 no desktop (`PORTAS_EXTRA` em gera_imagem.py), como o PC2 (9470–9475). Não disputa a 9460 do Veo/postagem |
| desktop | **10 contas deslogadas do Flow** (SessaoExpiradaError): canalanimescomia, emersonjosiel0, emersonjosiel1995, emersonjosielmrx1995, empressinovare, fabricadeautomacoesia, gabriellyvitoriaisabelaaraujo, mentoriaiapro, mundosolar1995, simonerebecaluizasilva | médio | **FALTA a dona**: `login_em_lote.py desktop` (ela digita só a senha) |
| desktop | "não respondeu" (ssh cai) | médio | conhecido (D38b); puxar_http já ajuda |
| PC1 (este) | Chrome local não conecta (ECONNREFUSED 9250/9260) — o PC1 está SEM MEMÓRIA VIRTUAL: commit 38/39,8 GB (reel_globo 4,8 GB, produto, reel_advance...) | médio | **FALTA decisão**: aumentar o arquivo de paginação no D: (ex.: +16 GB) ou tirar trabalho do PC1 |
| todas | Flow recusa o prompt por HTTP (UNSAFE_GENERATION) -> tentava pela TELA na mesma conta (~5 min presa, recusa de novo, dava FileNotFound/Timeout/TargetClosed) e ainda tirava a conta da fila por 20 min | grande | **FEITO 01/11 21h**: `_RecusadoInseguro` — recusa vai direto pra PRÓXIMA conta, sem tela e sem castigo (a capa B aprovada saiu assim, na 2ª conta) |
| capas | capa_ia_anime pedia só pc1,desktop,x200ma,acer e no máx. 3 contas | — | **FEITO**: + pc2 e 6 contas (`CAPA_MAQUINAS` muda) |

## 01/11 23h50 — capacidade DINÂMICA + monitor de RAM/CPU (pedido da dona)
- `logs\capacidade.json`: vagas de imagem por máquina (desktop começou 3 -> subi pra 5 com CPU 0%; PC2 6). 3 imagens
  OK seguidas = +1 vaga (só se a CPU < 75% e RAM livre > 900 MB; RAM baixa = limpa lá e mede de novo). Falha de
  capacidade (Chrome não abriu, ECONNRESET, Timeout, TargetClosed, POUCA_RAM) = -1 e teto por 2 h. Máx. 10.
- Antes de abrir Chrome no PC2/desktop: mede (cache 1 min). CPU >= 95% ou RAM < 450 MB = pula a máquina.
- `logs\monitor_maquinas.jsonl`: cada medida (cpu, ram_mb, chromes, limite).
- Achado: PC2 a 100% de CPU (hipercool) derrubava os Chromes de imagem — os 4 testes da B das 23h20 morreram assim.
- PC1 fora das capas (Chrome daqui travava 50 min sem memória virtual).
- NÃO resolvido: imagem ainda abre Chrome pra CADA token (o reCAPTCHA vale 1 vez — flow_gerar.py); manter um Chrome
  "quente" por conta fabricando tokens tiraria os ~80 s de abrir/fechar. Próximo passo.

## 02/11 02h — FÁBRICA DE TOKENS (Chrome quente) — pedido da dona "deixando fabricando os tokens"
- Decisão: UMA fábrica POR MÁQUINA (o token sai do Chrome logado daquela conta naquela máquina; os perfis/logins são
  de cada máquina, então uma central não serviria). Começou no desktop; PC2 depois do teste.
- `D:\projeto-navegador-sem-navegador\services\veo_flow\fabrica_tokens.py` roda lá (tarefa `FabricaTokens`, sessão
  da tela, pythonw oculto, porta 127.0.0.1:9399). Mantém o Chrome de cada conta parado no projeto do Flow (portas
  9480-9489) e entrega cookies + token (~0,4 s). Conta parada 20 min = fecha; RAM < 1,1 GB = fecha a mais antiga.
- `flow_gerar.py --fabrica 9399 --perfil P` (FlowGerador(fabrica=...)): só HTTP, não abre nem fecha Chrome.
- `gera_imagem.py`: `FABRICA = {"desktop","pc2"}` — tenta a fábrica ANTES da porta extra; falhou antes de pedir =
  caminho antigo. Conta quente (logs\fabrica_quentes.json, 15 min) vai na frente no sorteio.
- `chrome_conta.abrir` pede `/soltar` à fábrica antes de abrir o mesmo perfil (2 Chromes no mesmo perfil não sobem).
- A fábrica confere se o perfil já está aberto por OUTRO Chrome (WMI) antes de abrir — 02/11 a emersonjosiel2032
  travou 7 min por isso.
- Instalar/reiniciar numa máquina: copiar fabrica_tokens.py/flow_gerar.py/instalar_fabrica.ps1 pra
  C:\postador-worker\nsn\services\veo_flow\ e `powershell -File ...\instalar_fabrica.ps1`. Diagnóstico: diag_fabrica.ps1.
  ATENÇÃO: o nsn do desktop estava VELHO (sem core\arquivo.py) — rodar `maquina_remota.py instalar-nsn <maq>` antes.
- Teste 1: 1ª imagem pela fábrica (Chrome frio) 72 s total.

Capacidade depois das mudanças: notebooks 1+1, PC2 6, desktop 3 (+ a 9460), PC1 1–2 se tiver memória.
Desligar o desktop multi-porta: tirar "desktop" de `PORTAS_EXTRA`.
