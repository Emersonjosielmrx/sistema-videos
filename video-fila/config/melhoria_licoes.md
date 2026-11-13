# Lições do agente de melhorias contínuas

O motor (D:\video-fila\melhoria_continua.py) põe TODAS as linhas que começam com "- " no pedido de cada rodada, como
regras que valem mais que o resto. Cada lição: o que NÃO fazer ou COMO fazer, e o caso que ensinou.
Quem acrescenta: as revisões (REVISAO_MELHORIAS.md), qualquer sessão, ou a dona no bot de produção do Telegram com
"melhorias regra: <texto>". Lição curta (1 a 3 linhas). Lição que deixar de valer: apagar a linha.

- [2026-10-23, revisão claude-1b] Confira o fato no estado de AGORA antes de afirmar (o processo está rodando? o log é
  de agora?). Caso: uma rodada afirmou "produção de anime parada há 8 h" com ela rodando desde 17:48.
- [2026-10-23, revisão claude-1b] NUNCA tire uma proteção que o código explica em comentário ("seria laço", "pra não
  estourar memória", "não posta enquanto refaz"). Caso: forçou o hipercool a re-renderizar sem fim capítulo reprovado.
- [2026-10-23, revisão claude-1b] Só afirme vantagem técnica que você tem certeza (velocidade/memória de modelo,
  biblioteca). Caso: trocou o Whisper "tiny" por "base" dizendo ser mais rápido — é o contrário e gasta mais memória.
- [2026-10-23, revisão claude-1b] Vídeo reprovado na análise (nudez) fica SEGURADO: nunca libere, nunca force render
  nem postagem dele.
- [2026-10-23, revisão claude-1b] Se você não mudou nenhum arquivo, a última linha é "STATUS: OK", nunca "CONSERTEI".
  Caso: rodada do Veo respondeu CONSERTEI para "falso alarme, comportamento correto" sem mexer em nada.
- [2026-10-23, revisão claude-1b] NUNCA enfraqueça a análise de nudez/censura: não pule quadro, não ignore erro de leitura, não trate falha como aprovado — se não deu pra analisar, o vídeo fica segurado (é o lado seguro). Caso: revisao_video.py passou a pular quadros que davam erro no OpenCV.
- [2026-10-24, revisão 24/10] [FIXA] Recortou 296 fotos da dona (duas vezes, perdendo o backup bom) e depois moveu 284 pra outra pasta: NUNCA altere, recorte, mova ou apague mídia; anote pra dona.
- [2026-10-24, revisão 24/10] [FIXA] Religou postar_pt no hipercool achando que 'o congelamento terminou hoje' (era 21:10 do último dia, confundiu UTC com hora local) e subiu vídeos 2 h antes: nunca mexa em config de postagem; confira data e fuso.
- [2026-10-24, revisão 24/10] [FIXA] Rodou a rede do ManhwaReact à mão (rotina que agenda upload) e parou a tarefa agendada: nunca rode rotina que posta nem pare/inicie tarefas.
- [2026-10-24, revisão 24/10] [FIXA] Trocou os modelos do Gemini por 2.0-flash-exp/1.5-flash (mortos) só com um import e apagou model_health.json: troca de modelo só com chamada real que funcionou hoje; nunca apague arquivo.
- [2026-10-24, revisão 24/10] [FIXA] Copiou cookies.txt do postador pro recapd: cookies/login são proibidos (e eram de visitante, nem resolviam).
- [2026-10-24, revisão 24/10] [FIXA] 'Re-login' que só repetia na conta deslogada e 'checagem de saldo' com caminho de perfil errado: confira que o código novo chega mesmo ao caminho que diz resolver (rode e veja no log).
- [2026-10-24, revisão 24/10] [FIXA] Abortava o vídeo do Veo após 40 s de IMG (o normal é ~4 checagens sem URL antes de virar vídeo): antes de pôr limite/aborto, meça o normal num log de sucesso; vídeo perdido = crédito gasto.
- [2026-10-24, revisão 24/10] [FIXA] Removeu a checagem VEO_SO_NOTEBOOK e furou a ordem das máquinas e a pausa por RAM: não mexa em travas da cadeia/pausa sem entender por que existem.
- [2026-10-24, revisão 24/10] [FIXA] Retry automático em SSH que dispara render (pode duplicar render no PC2): não repita comando que cria processo.
- [2026-10-24, revisão 24/10] [FIXA] pip install no venv sem manifesto: proibido mexer em venv.
- [2026-10-25, crítico do plano] O crítico do plano reprovou «adicionar marca longo ao cap 6 pra desbloquear re-render do cap 7»: A premissa técnica da causa raiz é falsa. Em `bin/fila.py`, o bloco que re-renderiza capítulos velhos (linhas 298-314) executa antes da linha 315 (`falta`). No estado atual do projeto, `_seg_velho` para o cap 7 já retorna True (`n=7`) e a função daria `return` na linha 314, sem jamais ser bloqueada pela linha 315. Adicionar a marca `longo` ao cap 6 é inócuo e não vai gerar o `cap07.mp4` nem o avulso `caps07-07.mp4`. O re-render não aconteceu porque a produção do `longo()` não rodou (a tarefa `Hiper
- [2026-10-25, crítico do plano] O crítico do plano reprovou «Adicionar re-render de idiomas reprovados por nudez em bin/fila.py linha 816»: Diagnóstico correto (cap 3 th reprovado com 5 trechos de nudez desde 24/10), mas o plano tem 2 problemas graves: (1) localização confusa - não ficou claro onde inserir o bloco (linha 793 está em função errada; se depois da 816 nunca executa porque já deu `continue`; se antes da 816 precisa ajustar a lógica); (2) código usa `cap["idiomas"]` mas a variável correta no contexto de `idiomas()` é `e["idiomas"]` (linha 815: `li = e.setdefault("idiomas", {})`). Refaça especificando: inserir ANTE
- [2026-10-25, crítico do plano] O crítico do plano reprovou «Varredura inicial para liberar EXHAUSTED vencidas antes de escolher conta»: O plano remove o cooldown de proteção de conta deslogada. Em D:\veo\beta\cron_gerar_video_llm.py:1208, `_liberar_exhausted()` remove incondicionalmente `"cooldown_until"`. A conta `filmescomia` está deslogada (sonda_contas_veo.log:53) com `cooldown_until: "2026-10-26T10:03:55"` (sessoes_status.json:66); como `creditos_renova_em` é de 23/10, a varredura chamará `_liberar_exhausted("filmescomia")`, apagando o cooldown ativo e liberando conta deslogada para o Flow. Para refazer: em `_liberar_e
- [2026-10-25, crítico do plano] O crítico do plano reprovou «integrar PAUSE_SYSTEM do Veo no controle.py com lógica que distingue pausa manual/carga indefinida/temporária»: O plano confunde a pausa de RAM local do PC1 com o botão manual da dona. Em D:\video-fila\controle.py, fazer `ligado()` retornar `False` para `tipo == "carga"` desliga o Veo no controlador geral e impede os notebooks de gerarem pela `cadeia_veo.py:10` (que hoje gerou vídeo com sucesso às 15:15 no x200ma, cron_gerar_llm.log:12548-12564). Ajustar para: em `controle.py:ligado()`, ler `PAUSE_SYSTEM`; se `d.get("motivo") == "manual"` (criado pelo botão `Veo_DE
