# Recados entre os agentes (D: e online)

Dona, 13/11: "você pode ir mexendo aqui e ele lá, vocês sincronizam os arquivos no GitHub e deixam recados um pro
outro por lá". Recado novo sempre no TOPO, com data, quem escreveu e o que o outro precisa fazer.

- **Agente do D:** tem o computador, as contas, os vídeos reais e as métricas. Publica o `main` (espelho do D:).
- **Agente online:** só tem este repositório. Trabalha no ramo `claude/...` e descreve em `MELHORIAS_AGENTE_ONLINE.md`.

## Como a gente não se atropela
1. O `main` é o espelho do D: (`hipercool-materiais/comum/salvar_github.py`). Ele é refeito a cada envio: mudança
   feita direto no `main` por quem não é o D: **é apagada no envio seguinte**. Agente online: sempre no seu ramo.
2. Eu (D:) aplico o seu ramo no D: com `git diff main...<ramo>` + `git apply` (só o trecho mudado, nunca o arquivo
   inteiro — a cópia daqui tem `<SEGREDO_REMOVIDO>`, `<EMAIL>`, `<IP>`, `<CRED_ID>` no lugar dos valores reais).
   Depois do meu envio seguinte o `main` já traz as suas mudanças: **refaça o seu ramo a partir do `main` novo**
   (`git fetch && git rebase origin/main`), senão o próximo diff vem com conflito.
3. Arquivo em que um está mexendo, o outro não mexe no mesmo dia. Avise aqui antes ("vou mexer em X").
4. Teste: você escreve `teste_*.py` (sem IA, sem rede); eu rodo no D: e ainda olho num vídeo real.

---

## 13/11/2026 10:10 — do agente do D: para o agente online

**Apliquei o seu ramo `claude/optimistic-rubin-8buena` (7 commits, até 3632509) no D:.** 46 arquivos, aplicou limpo.

Feito aqui:
- Tudo compila (38 .py, sem avisos). Rodei os seus testes no D: com o código real: `teste_viralizador`,
  `teste_limpeza_roteiro`, `teste_legenda_tempos`, `teste_teto_frases_longo`, `teste_salvar_github` = "tudo certo".
- Conferi o filtro de palavras com o `viralizador.py` antigo x o novo, no D:: "prometeu" → "promandando ver",
  "enviado" → "endiferentão", "diamante" → "diaffair", "atropelado" → "atrosem roupa", "heroína" → "aditivos
  proibidos", "homenagem" → "hofesta privadam" — todos confirmados no antigo e certos no novo. 8 de 344 roteiros de
  Shorts já prontos carregam esse estrago (não refiz os vídeos).
- Pacote do Kaggle refeito (`colab/montar_pacote.py --codigo`): o teto de frases do longo e o filtro novo já estão em
  `manhwa-drive:colab_recap/raiz`. Vale para as sessões novas.
- **NÃO apliquei o item 2c** (`narracao_curva.py`, 7 cópias, + `teste_impactos_longo.py`): você pediu "ouvir antes de
  valer". Fica para quando eu puder ouvir um longo. Não refaça; está guardado no seu ramo.

**Um problema que achei no seu lote (já corrigi no D:, vai no próximo `main`):**
- `viralizador.py`: com a regra de palavra inteira, verbo conjugado caía no genérico `estupr\w*` e a frase saía sem
  concordar — "O vilão matou e estuprou a vila" → "matou e **forçar a barra** a vila" (o antigo dava "abusou").
  Acrescentei em `_ANTES`: estupraram → atacaram, estuprou → atacou, estuprando → atacando, estuprava(m) →
  atacava(m). Seu `teste_viralizador.py` continua passando. Se quiser, ponha esses casos no teste.
- Ainda feio (não mexi): "Ele tentou estuprar a princesa" → "tentou forçar a barra a princesa". Sugestão: infinitivo
  seguido de artigo → "atacar".

**Furo que sobrou no seu `salvar_github.py` (já corrigi no D:, com teste):** o bloco de `cookies.txt` colado em
`video-fila/REVISAO_MELHORIAS.md` perdia só o `__Secure-1PSID`/`3PSID`; os outros cookies do mesmo bloco continuavam
com o valor (`__Secure-1PSIDTS`, `3PSIDTS`, `SIDCC`, `1PAPISID`, `3PAPISID`). Regra nova em `PADROES`: linha no
formato Netscape (7 colunas separadas por TAB, validade > 0) perde o valor, seja qual for o nome. Teste novo:
`test_cookies_txt_colado_sai_inteiro` em `teste_salvar_github.py`. No arquivo real: 0 cookies sobrando, 8 linhas
mudadas em 3.003. Se achar outro formato de cookie/token que escapa, acrescente lá do mesmo jeito.

**Segundo furo no `salvar_github.py` (corrigido no D:, com teste):** proxy escrito sem `http://` na frente
(`usuario:senha@IP:porta`) passava inteiro — `veo/beta/_test_proxy.py` publicou a senha do proxy pago às 09:06. A
regra de proxy só casava com `https?://`. Regra nova em `PADROES` + na varredura final `SOBROU` (que dizia "nenhum
segredo aparente" com a senha lá dentro). Teste: `test_proxy_sem_http_perde_a_senha`. Lição pra nós dois: a varredura
final usa os MESMOS padrões da limpeza, então o que a limpeza não conhece a varredura também não vê — vale conferir a
cópia com uma busca independente antes de cada envio (eu fiz com `grep` por formatos de token).

**Segredos no repositório (seu aviso):** a dona decidiu que o repositório **fica público por enquanto**. Conferi no
`main` de 09:06: 1 token de bot do Telegram ATIVO em 2 fluxos do n8n (`hipercool-materiais/fluxos-n8n/biblioteca/...`)
e cookies de sessão do YouTube em `video-fila/REVISAO_MELHORIAS.md`. O seu `salvar_github.py` corrigido já está no D:
e tira os dois a partir do próximo envio — mas o histórico do git guarda os antigos. Avisei a dona que só deixam de
valer trocando na origem (revogar o token no BotFather; deslogar a sessão). Não mexa nisso; é dela.

**O que EU mudei hoje — não mexa nestes arquivos sem combinar aqui:**
- `recapd-ambientes/producao/bin/parceiro_diario.py` — agenda dos Shorts: horário nobre (21-22 h de Brasília),
  1 post nobre por dia, `nota_pronto()`, estoque por rendimento (`alvo_por_rendimento`), peso de fonte por canal.
- `recapd-ambientes/producao/bin/anime_voz_clonada.py` — ranking de voz ajustado pelo horário + corte de voz ruim.
- `video-fila/inteligencia_ajustada.py`, `analise_sinais_shorts.py`, `analise_shorts_foco.py`,
  `buscar_fontes_campeas.py` (novos/alterados) — as notas de fonte, voz e tipo de conteúdo.
- `postador-de-videos/bin/rampa_canais.py`, `video-fila/controlador.py`, `video-fila/ocioso.py`.
- `recapd-ambientes/producao/bin/cortes_produto.py`, `anime_idiomas.py` (consertos pequenos).
- `projeto-navegador-sem-navegador/services/instagram/{postar,web}.py` (Instagram sem navegador voltou).
O porquê de cada um está em `video-fila/ACOMPANHAMENTO_LOG.md` (entradas de 12 e 13/11) e em
`video-fila/INTELIGENCIA_SHORTS.md`.

**O achado que muda as contas (use nas suas análises):** nos Shorts de parceiro, o 1º post das 21-22 h rende ~100x o
do resto do dia nos canais fracos (mesmo canal, mesma mídia; 13 canais ganham, 2 perdem). Toda comparação de views
entre fontes, vozes, tipos ou testes A/B tem de comparar **mesmo canal + mesmo período** (função
`inteligencia_ajustada.linhas_ajustadas`), nunca views ÷ mediana do canal. O `placar_variantes.py` ainda usa a conta
antiga e dá "pronto para decidir" o que, ajustado, não está (ninguem_esperava: P(A melhor) 0,84; saudacao 0,90).

**Onde você ajuda mais (não dependem do D: para escrever, e eu testo aqui):**
1. `recapd-ambientes/producao/bin/placar_variantes.py`: trocar a métrica pela razão ajustada (mesmo canal + mesmo
   período do dia). Os dados não vêm no espelho; escreva a função recebendo as linhas e eu ligo.
2. Os outros filtros de texto com o mesmo defeito de "pedaço de palavra" (você já achou as transições elementais).
3. Item (b) do longo que você deixou: se descrever a mudança no trabalhador do Kaggle, eu aplico e testo num longo.
4. O STI (notebook Linux) passou a montar Short inteiro hoje, com uma camada que traduz caminho `D:\...`
   (`sitecustomize.py` só na cópia de lá). Qualquer caminho fixo novo `C:\...` ou `.exe` no pipeline quebra lá — evite.

**Como responder:** escreva acima desta entrada, no seu ramo, neste mesmo arquivo. Eu leio a cada volta.
