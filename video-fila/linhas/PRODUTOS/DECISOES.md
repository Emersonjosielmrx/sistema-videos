# Linha PRODUTOS — decisões (mais nova em cima)

Formato: data | o que mudou | por quê | prova | como desfazer. [GRANDE] = muda o que o público vê/ouve ou a produção.
Histórico detalhado antes de 26/10 18h: `D:\postador-de-videos\docs\PRODUTO_PROFISSIONAL.md` (tabela "Rodadas de melhoria").

- 13/11 05:17 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = No chat simulado, mensagens do Sentinela/bot ficam à esquerda (recebidas, balão cinza/branco); respostas da equipe à direita (balão azul). Cor e lado fixos por  | Os balões estão invertidos e mudam de lado e cor entre mensagens, o que confunde quem avisa e quem responde. É um defeito de CERTEZA apontad | modelo cw/claude-sonnet-5-5
- 13/11 05:17 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = Cabeçalho do chat simulado: o subtítulo deve combinar com o tema do vídeo (ex.: 'Bot Sentinela • monitoramento 24h'). Nunca usar 'atendimento com IA' quando o a | O subtítulo 'online • atendimento com IA' destoa do tema de monitoramento de VPS e pode confundir a mensagem. A regra usa só fatos do produt | modelo cw/claude-sonnet-5-5
- 13/11 03:28 | [MELHORADOR ensaio — NÃO aplicado] desligar_variante dono_tres_veo_final =  | O formato falhou de novo: o dono e o Veo caíram para foto de reserva (veo_total 0, cenas todas de banco de imagem). O placar mostra 3 usos e | modelo cw/claude-sonnet-5-5
- 13/11 03:28 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Registrar o vídeo como fallback quando o dono/Veo falhar (não contar como dono_tres_veo_final). Conferir no log por que o dono e o Veo caíram para foto. Se a fo | Duas causas que precisam de programação: a contagem errada do formato quando há fallback (distorce o placar) e o movimento baixo no júri (3, | modelo cw/claude-sonnet-5-5
- 12/11 22:42 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Exibir elementos dinâmicos sincronizados com a fala nas cenas de dono (badges, ícones ou palavras-chave entrando em movimento junto aos pontos principais) em ve | O quesito 'movimento' é consistentemente a pior nota do júri (média 5.04 nos últimos 12 vídeos) por falta de dinamismo gráfico sincronizado  | modelo gemini-4-argon
- 12/11 17:25 | [MELHORADOR ensaio — NÃO aplicado] desligar_variante dono_tres_veo_final = dono_tres_veo_final | A variante mantém o apresentador em 3 cenas seguidas sem mostrar tela ou demonstração do produto, acumulando placar [3, 0] e travando a nota | modelo gemini-4-argon
- 12/11 12:10 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = Em cenas de desafio ou dor, não exibir ícone de checkmark (✔) nos cards de destaque; usar marcador neutro ou alerta condizente com o problema relatado. | Eliminar contradição visual entre o ícone de confirmação positiva e a fala que relata falta de método e direção na cena de desafio. | modelo agy/gemini-3.8-flash-high
- 12/11 11:36 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = Em cenas com fotos estáticas, escalonar a entrada de novos destaques visuais ao longo da fala para manter o dinamismo da cena e evitar sensação estática. | Evitar sensação de cena estática e elevar a nota de movimento em fotos sem depender apenas do zoom Ken Burns. | modelo agy/gemini-3.8-flash-high
- 12/11 04:59 | [MELHORADOR ensaio — NÃO aplicado] peso_variante dono_mesma_foto = 0.5 | O formato repete o mesmo plano do dono na abertura e no fecho, o que deixa o ritmo previsível. O júri deu nota 5,62 a este vídeo, com movime | modelo cw/claude-sonnet-5-5
- 12/11 04:59 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = Na cena de imagem do problema, a foto de fundo deve combinar com a dor da fala (frustração, terminal, servidor). Nunca use gente comemorando. Marcador neutro ou | Três jurados (movimento, roteiro_marca e diretor) apontam a incoerência da cena 1: foto de homem comemorando enquanto a fala é de dor, com ✓ | modelo cw/claude-sonnet-5-5
- 11/11 22:46 | [MELHORADOR ensaio — NÃO aplicado] peso_variante dono_tres_veo_final = 0.3 | A variante 'dono_tres_veo_final' rodou com veo_total=0 e caiu para fotos estáticas repetidas nas cenas 1 e 3, acumulando 3 vídeos com 0 apro | modelo gemini-4-argon
- 11/11 16:34 | [MELHORADOR ensaio — NÃO aplicado] regra_roteiro  = Na cena de resultado ou beneficio, descreva no prompt de imagem o profissional sorrindo, tranquilo ou atendendo cliente com sucesso; proiba expressao de estress | Contradição visual grave na Cena 3 ('O resultado'), onde a imagem gerada mostrou um profissional com a mão na cabeça em expressão de estress | modelo gemini-4-argon
- 11/11 10:37 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo card O RESULTADO (cena 3) = Fazer os 3 boxes do card entrarem um a um, cada um no momento em que a fala o cita, com um destaque curto que acompanha a fala. Animar o card que já existe, sem | O movimento é a nota mais fraca em quase todos os vídeos. O que falta é elemento se mexendo junto com a fala, e o card hoje fica estático en | modelo cw/claude-sonnet-5-5
- 11/11 10:37 | [MELHORADOR ensaio — NÃO aplicado] ajuste pulso_botao = 0.09 | O cartão final (cena 4) tem o menor movimento medido do vídeo (4,61%). Aumentar um pouco a amplitude do pulso é uma mudança pequena e revers | modelo cw/claude-sonnet-5-5
- 31/10 10:27 | [MELHORADOR ensaio — NÃO aplicado] regra_roteiro  = Em simulações de conversa ou atendimento, nunca invente nomes próprios para clientes (como Carlos), revise a acentuação (Alô, vocês) e alinhe o texto ao formato | A cena 2 simulou ligação de voz com balões de chat de texto, usou nome fictício ('Carlos') e apresentou erros de acentuação ('Alò', 'vocès') | modelo gemini-4-argon
- 31/10 04:19 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Fazer os elementos da cena de imagem entrarem na hora da fala: pílulas 'moderação ativa' e 'resumo das conversas' surgindo uma por vez, com deslize ou overshoot | Movimento é a nota mais fraca e se repete: ficou entre 5,0 e 6,0 nos 12 vídeos anteriores e caiu para 4,0 neste. A medida de movimento é alt | modelo cw/claude-sonnet-5-5
- 31/10 04:19 | [MELHORADOR ensaio — NÃO aplicado] regra_roteiro  = Todo bullet de resultado ou benefício na tela deve ser frase curta completa, com verbo ou resultado (ex.: 'grupos no automático'), nunca só um substantivo solto | O júri apontou 3 vezes (legibilidade, roteiro_marca e diretor) que a pílula da cena 3 é um substantivo solto e não diz o resultado narrado.  | modelo cw/claude-sonnet-5-5
- 30/10 20:45 | [MELHORADOR ensaio — NÃO aplicado] ajuste chat_fonte_msg = 44 | Reduzir o tamanho da fonte das mensagens do chat (de 52 para 44) para que os 3 balões da conversa caibam simultaneamente no card sem remover | modelo gemini-4-argon
- 30/10 17:37 | [MELHORADOR ensaio — NÃO aplicado] regra_roteiro  = Na cena de conversa simulada, mostre uma dúvida real de cliente sobre o serviço sendo respondida pela IA na prática, evitando perguntas genéricas apenas sobre o | O júri apontou problema no diretor e roteiro_marca na cena 2 porque o diálogo simulado foi raso ('Qual é o seu ramo?') e não demonstrou a IA | modelo gemini-4-argon
- 30/10 16:28 | [MELHORADOR ensaio — NÃO aplicado] peso_variante dono_tres = 0.4 | A variante 'dono_tres' manteve o apresentador no mesmo enquadramento por 27s seguidos sem mostrar nenhuma tela ou demonstração do produto, r | modelo gemini-4-argon
- 29/10 23:30 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Na cena de imagem (foto de banco de imagem), fazer entrar cartões sincronizados com a fala quando ela cita os valores. Os cartões mostram o valor em algarismos, | Cena 3 tem movimento alto (13,1%) mas falta elemento novo em sincronia com a fala. O selo aparece tarde e sobre a foto do humano, o que pass | modelo cw/claude-sonnet-5-5
- 29/10 23:30 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Fazer o chat acumular as mensagens anteriores e rolar para cima quando a resposta do cliente entra, em vez de trocar o estado por bloco. Conferir se o limite de | Na cena 2 as mensagens anteriores da IA somem quando a resposta do cliente chega, e isso quebra a prova visual de insistência e recuperação  | modelo cw/claude-sonnet-5-5
- 29/10 21:40 | [MELHORADOR ensaio — NÃO aplicado] ajuste conversa_subida = 80 | A cena 2 (conversa simulada) teve apenas 3.87% de movimento medido (abaixo do mínimo de 4.0%), sendo um problema de CERTEZA repetido. | modelo gemini-4-argon
- 29/10 20:30 | [MELHORADOR ensaio — NÃO aplicado] peso_variante dono_tres_veo_final = 0.3 | Formato com 3 cenas seguidas apenas do dono (>20s sem tela do produto ou simulação de conversa) derruba repetidamente as notas de movimento  | modelo gweb/gemini-3.1-pro
- 29/10 20:30 | [MELHORADOR ensaio — NÃO aplicado] ajuste legenda_fonte = 66 | Legendas com palavras longas em fonte 74 invadem a margem lateral de segurança (< 60 px das bordas). | modelo gweb/gemini-3.1-pro
- 29/10 19:19 | [MELHORADOR ensaio — NÃO aplicado] ajuste legenda_fonte = 68 | Evitar que linhas compridas da legenda karaokê encostem a menos de 60 px das bordas laterais do Reels ou quebrem expressões no fim da linha. | modelo gweb/gemini-3.1-pro
- 29/10 19:19 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Garantir que o card de destaque visual (destaques_tela) sempre gere ao menos 1 ou 2 entradas animadas na cena 3 ('imagem') sincronizadas com a fala, ou exibir í | Nota de movimento travada entre 4.0 e 5.0 em 11/12 vídeos por falta de elemento dinâmico sobre a foto estática na cena 3, mesmo com destaque | modelo gweb/gemini-3.1-pro
- 29/10 18:06 | [MELHORADOR ensaio — NÃO aplicado] ajuste folga_fala = 0.4 | Aumentar o respiro após cada fala (de 0.28s para 0.40s) para impedir que o corte da cena aconteça cedo demais e que a legenda karaokê suma e | modelo gemini-4-argon
- 29/10 16:25 | [GRANDE] MELHORADOR LIGADO em modo APLICAR (dona: "ative com esses 3 de fallback, sem o Gemini puro,
  vamos acompanhar") | cadeia dos 3 papéis = gweb/gemini-3.1-pro -> argon-pro -> argon-flash (argon-pro saiu dos
  desligados) | prova: teste no MESMO vídeo real (Hermes 04:41, nota 5,5), gabarito do Opus escrito antes
  (`teste_modelos\GABARITO_opus.md`): prompt antigo = todos 6–6,5 (compraram o falso "legenda sem caixa", ninguém usou
  a variante); prompt novo (analista/decisor: legenda sem caixa por desenho, efeito de transição, FORMATO -> peso da
  variante; dados.json com efeito_transicao) = gweb 10 (157 s), argon-pro 9,5 (328 s), argon-flash 9,5 (711 s): os 3
  propuseram peso_variante dono_tres 0,3–0,4 + respiro do topo da cabeça (= gabarito) | desfazer:
  `python -m produto.melhorador --desligar` ou voltar `config\melhorador_produtos.antes_29out_teste.json` |
  RISCO anotado (Fable D9): alcance 0–4 views ainda não diz qual formato rende; o vigia desfaz se a nota cair.

- 29/10 16:48 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Vincular o identificador do cartão final ao arroba real da marca anunciada (ou omitir caso não exista no cadastro do produto) em vez de herdar diretamente o nom | O vídeo promove o produto 'Cardápio Digital', mas o cartão final exibe '@futebolcom.ia2', gerando desconexão com a marca anunciada. | modelo gemini-4-argon
- 29/10 15:37 | [MELHORADOR ensaio — NÃO aplicado] peso_variante dono_tres = 0.3 | O formato 'dono_tres' mantém o apresentador em plano médio frontal por mais de 26 segundos sem intercalar telas de demonstração do produto o | modelo gemini-4-argon
- 29/10 15:37 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo enquadramento_dono_pilula_etapa = Reposicionar a pílula de indicação da etapa ('1 O problema', '2 Como funciona', '3 O resultado') ou ajustar o enquadramento/escala vertical do vídeo do apresent | A pílula de indicação da etapa fica sobreposta e encostando diretamente no topo da cabeça do apresentador, violando a regra de não cobrir o  | modelo gemini-4-argon
- 29/10 14:31 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = Afaste a pílula de etapa superior ou desça/reduza levemente o enquadramento do apresentador para nunca encostar no cabelo ou rosto, e garanta corte limpo antes  | A pílula superior está encostando e sobrepondo o topo da cabeça/cabelo do dono de forma repetida (violando a regra fixa de nunca cobrir o ro | modelo gemini-4-argon
- 29/10 14:31 | [MELHORADOR ensaio — NÃO aplicado] regra_editor  = Na legenda karaokê, mantenha sempre tarja escura sólida ou contorno contrastante em todas as palavras, especialmente nas destacadas em verde sobre roupas escura | Problema de CERTEZA repetido onde a palavra destacada em verde-escuro perde o fundo protetor e fica sem leitura sobre a camisa azul-marinho  | modelo gemini-4-argon
- 28/10 19:40 | [GRANDE] destaques em TODO bloco (não só imagem/veo) + conversa de RESERVA no bloco 2 com Veo
  (`agentes` prompt/_validar/revisor; `video.gerar`: Veo do bloco 2 falhou -> conversa em vez de foto) | Hermes
  15:37 (1º vídeo com tudo novo: voz pica_pau no PC2 ok, efeitos ok, 6,5 = melhor dos 4): dono do bloco 1 e Veo do
  bloco 2 falharam -> 2 fotos SEM destaque (o roteiro só dava destaque p/ imagem/veo) e bloco "como funciona" com
  foto de banco; júri "parado/slide" (medida real 12-15%, efeito de transição visível no quadro: júri errou essas
  duas) e diretor "falta prova visual do produto" | teste: roteiro variante (1,3)+veo 2 -> destaques nos 3 blocos e
  conversa de 4 msgs aprovada pelo revisor | desfazer: tirar "or (i == 2 and b.get('conversa'))" em video.gerar.
  + `video._visao` tenta 3 Gemini (gemini-3-flash -> 3.5-flash -> 3.8-flash-high) antes de desistir: as 2 imagens
  novas do Hermes foram descartadas por timeout da visão e trocadas por foto do banco (mulher sorrindo na fala de
  "comercial travava"); reconferidas depois = nota 9, sem defeito | teste ao vivo: 5 s / 5 s / 29 s.
- 28/10 13:20 | [GRANDE] VOZ CLONADA na narradora: edge Francisca vira BASE (pronúncia + tempo das palavras) e o RVC
  troca o timbre (`video.clonar_vozes`, voz sorteada de config\produto_vozes.json: fatos_desconhecidos, moana — as 2
  que a DONA citou; gravada em side["voz_clonada"] p/ júri/views compararem). Roda no PC2 (`_clonar_pc2`: o Applio do
  hipercool já está lá, `subst D: C:\`); falhou = PC1; falhou/duração mudou = voz base no vídeo TODO | DONA: "Francisca
  é voz ruim; temos clonadas muito melhores (Moana, Fatos Desconhecidos)... cuidado com o público (jovem não compra)"
  -> FORA dos anúncios: voz jovem/meme e pessoa real famosa (Cid Moreira, Silvio, Galvão, Faustão, Lula = soaria
  endosso) | teste: 2 trechos 2,59->2,58 s / 2,42->2,40 s; PC1 carregado 10,9 min, PC2 7,5 min | "ligado": false.
  Amostras p/ a dona: D:\hipercool-materiais\produtos_ultimo_video\teste_vozes
- 28/10 13:20 | júri Hermes Call 6,0 (código antigo): regras 10–12 em config\produto_regras_roteiro.md (dono fala
  como quem já usa, nunca duvidando; cenário do dono limpo; acento certo e Hermes Call = transcrição de LIGAÇÃO),
  trava "acento grave fora do à" na conversa, margem da legenda 50 -> 70 px | editor: Gemini 1 h estourado em 4 de 5
  e a única edição perdeu do molde -> prazo `gemini_prazo_min` 35 (config já estava 35/1 por rodada).
  FALTA: tela de LIGAÇÃO no chat_ui para o Hermes Call (diretor: "narra ligação de voz e mostra chat de texto").
- 28/10 11:55 | [GRANDE] bloco 2 ("como funciona") LIVRE = obrigatoriamente "conversa" (o produto funcionando na
  tela) em vez de foto de banco | diretor Disparo ("fala de rotação de instâncias, tela com stock") e Follow-up
  ("sala de reunião vazia enquanto explica o follow-up") | teste nas 10 variantes: só exige onde o bloco 2 está livre
  (dono_uma_cena, dono_abre_fecha, dono_mesma_foto, dono_e_cena_veo, sem_dono) | tirar o 1º elif em agentes._validar
- 28/10 11:50 | placar das variações NUNCA mediu (todo post de produto é pelo navegador, tokens vencidos) ->
  `produto\medir_insta.py` escrito, NÃO ligado (429 no teste; ver ESTADO)
- 28/10 11:40 | [GRANDE] cena do DONO acaba 0,45 s (botão folga_dono) depois da última palavra; a voz dele é
  cortada junto (wav _corte com fade 0,15 s), senão o ambiente do clipe vaza | júri Fábrica q12 / Disparo "legenda
  some e ele continua falando" -> CONFERIDO no vídeo real: legenda certa, fala acaba em 5,7 s e a cena usava o clipe
  de 8 s inteiro = 2 s de dono mudo (tempo morto). 1ª hipótese (Whisper perdendo o fim) DESCARTADA: energia da
  voz nos 3 clipes do tmp acaba onde o Whisper parou | Hermes Call real: 8,0 -> 7,33 s | folga_dono=1.2 (máx) ~ antes.
- 28/10 11:00 | [GRANDE] 3 consertos dos graves que se REPETEM (contagem dos 6 últimos júris):
  (1) DESTAQUES DA FALA na cena de imagem: roteirista manda "destaques" (2 trechos de 2–4 palavras COPIADOS da fala,
  `agentes.destaques_validos` descarta o que não está na fala/na ordem — teste: "grátis pra sempre" caiu); entram
  deslizando 0,1 s antes de serem ditos e sobem 26 px até o fim da cena (`video._chip`/`seg_imagem`/
  `tempos_destaques`) | júri: foto "parada/slide" em 5 de 6 vídeos e "tela desligada da fala" (diretor) MESMO com
  a medida de movimento 5–15% -> o que falta é elemento, não zoom | quadros 1,5/1,8/3,0/3,7/4,9 s conferidos |
  botão destaques_tela=0.
  (2) CARTÃO DA PERGUNTA livra a CABEÇA do dono: YuNet acha o rosto; cabeça (+45% pro cabelo) acima do fim do
  cartão = a foto desce até 380 px e o alto vira a foto borrada (`_livrar_cabeca`) | júri Follow-up e Fábrica
  ("cobre testa/topo da cabeça") | antes/depois com a foto real da Fábrica: cabeça inteira livre | tirar a linha
  `_livrar_cabeca` em card_pergunta.
  (3) CARTÃO FINAL: botão entra crescendo (0,25–0,6 s), brilho atravessa a cada 1,5 s, pulso 1,1 -> 0,83 s | júri
  Follow-up/Fábrica "q13–q15 idênticos": o pulso de 1,1 s caía na mesma fase dos quadros do júri (~1,2 s) | 5
  quadros conferidos, todos diferentes | botão brilho_botao=0.
  As 3 lições foram pro prompt do ANALISTA do melhorador (config\melhorador\analista.md, "Como pensar"). Valem a
  partir da rodada 13:41 (a de 09:27 já tinha carregado o código). MEDIR: movimento e diretor do júri nos próximos 3.
- 28/10 10:20 | [GRANDE] RENDER REMOTION DO EDITOR NO PC2 (`editor._render_pc2`): PC1 manda 1 tar (src/lib +
  src/videos/<id> + trabalhos/<id>/public) -> PC2 `C:\produto-pc2\remotion` (npm ci do MESMO package-lock, 287
  pacotes; o Remotion traz ffmpeg e baixou o Chrome sozinho) -> mp4 volta. 3 conexões por render. Sem instalação /
  RAM < 2,5 GB lá / qualquer erro = render local como antes | DONA "PC2 a mais produtiva" + PC1 caiu por "Cannot
  allocate memory" | teste 4 s com karaokê da lib: 58 s ida-render-volta, 1080x1920, quadro conferido | config
  `editor.render_pc2=false` em produto_lapidar.json. ARMADILHA achada: ssh do Python com entrada herdada, `-n` ou
  DEVNULL NÃO fecha o canal (powershell lá espera stdin; render pronto em 3,5 min e conexão presa 15 min) -> só
  `input=""` (pipe vazio) fecha. Vale pra qualquer ssh novo pro PC2 a partir do Python.
- 28/10 09:25 | trava da rodada (`produto_tmp\.rodando`) guarda o PID e só vale com o processo vivo | a rodada de
  27/10 21:21 morreu no Veo e a trava segurou a de 04:41 ("outra rodada em andamento") -> manhã sem vídeo | teste dos
  3 casos (antiga sem PID, PID vivo, PID morto); rodada perdida relançada 09:27 | voltar a regra só das 10 h em
  diario._trava_viva
- 27/10 21:10 | [GRANDE] máquinas (DONA: "PC2 a mais produtiva; navegador notebooks -> PC2 -> desktop -> PC1"):
  telão PC2 com medidor CPU/RAM + saude.csv 24 h; análise diária 08:05 (AnaliseMaquinas24h); desktop instala sozinho
  quando o sshd voltar (eu derrubei com stdin — esperar_desktop_telao.py tenta 1x a cada 40 min); vitrine travado 16:15
  consertado (sai 5 min após o fim); ordem fixa do navegador em maquina_remota; 37 ativações (YouTube no PC2, Instagram
  fora do PC1) pelos logins já conferidos | medido 20:25 PC1 100% / PC2 17% / desktop 0% | backups *.bkp_*_ativar,
  ORDEM_NAVEGADOR em maquina_remota
- 27/10 20:00 | CHAT da dona com o melhorador no terminal (`CONVERSAR_MELHORADOR.bat`): continua a última conversa,
  abre com "onde estamos", atende pedido extra direto (CLAUDE.md da pasta = papel + regras); Gemini 3.8 -> API 3.5;
  config isolada .conversa | DONA: "quero abrir um chat pra falar com ele se quiser, já na conversa, só pra digitar"
  | teste -p: CLAUDE.md lido, Read ok, --continue lembrou | apagar o .bat. Ciclo automático segue DESLIGADO (dona:
  "ainda não ligue")
- 27/10 17:30 | [GRANDE] TODA cena do dono no mesmo vídeo parte da foto da 1ª (mesma roupa/óculos/cenário; Veo varia
  o movimento e a fala). Antes: foto nova por cena (só a variante dono_mesma_foto reaproveitava) | júri: Agenda IA
  16:18 REPROVADA 5,33 "quebra severa de continuidade do apresentador" (dono_tres) + VPS 26/10 + os 8 modelos do
  teste acharam o mesmo | Disparo (cinco_veo) de 16:18 ainda saiu com 2 fotos (processo carregou o código antes) |
  voltar o `if mesma_foto and foto_fixa` em video.py
- 27/10 16:05 | TESTE RÁPIDO antes de cada etapa longa (motor.responde: "responda OK", 60 s; Argon 90 s; cache 10 min)
  -> editor, corretor e melhorador pulam na hora o modelo que não responde. + reserva da API: gemini/gemini-3.5-flash
  (editor modelo_reserva2, melhorador 3º da cadeia, roteirista 3º do MODELOS) | DONO: "tem o Gemini por API no
  OmniRoute; ajustar pra não esperar 30 min um modelo responder". Medido 16:00: com chave "cooling down" o OmniRoute
  segura 4–5 min antes do 429 (API 3.8/3.7 >300 s, API argon/3.1-pro 227 s -> 429); API 3.5 Flash 7 s e funciona
  com ferramentas (Read/Write, 11 s); tiered 5 s; 3.8 high 23 s | tirar modelo_reserva2 / o ping em _cadeia
- 27/10 15:40 | DONO: "não use Opus nem Kiro por agora, só o Argon se tiver e o Gemini" -> conferido: produção e
  melhorador sem Opus/Kiro; melhorador modelos_desligados = Opus 4.6, Opus 5.5, Kiro, argon-kiro, argon-opus,
  argon-pro (trava); teste do Opus 4.6 cancelado | dono | modelos_desligados no config\melhorador_produtos.json
- 27/10 15:30 | DONO: "Argon curto; se começar a demorar muito, troca pro Gemini" -> prazos só do Argon:
  roteiro 180 s (config argon_prazo_roteiro_s), editor 30 min e corretor 30 min (editor.argon_prazo_min; corretor
  ganhou reserva Gemini, antes não tinha), melhorador 360 s por papel (melhorador argon_prazo_s). O Gemini continua o
  Video.tsx que o Argon deixou no disco | — | prazos na config
- 27/10 15:10 | REGRA DO DONO: "o Opus só deve ser usado no melhorador, nos testes; não para vídeo". Produção (roteiro,
  editor, júri) não usa Opus. Teste Opus 4.6 sozinho = só análise + caixa (melhorador); o de roteiro foi apagado.
  Opus 4.6 está com 403 (conta Antigravity recusada: "must be 18") -> refazer quando voltar | dono | —
- 27/10 15:00 | [GRANDE] DONO: "por hora vamos usar o Argon com fallback Gemini 3.8" -> roteiro gemini-4-argon (falhou
  1x -> Gemini tiered), editor/corretor argon-gemini (2ª tentativa Gemini 3.8 high), melhorador (ainda DESLIGADO)
  analista/decisor/revisor = [gemini-4-argon, Gemini 3.8] (Kiro e Opus fora). Júri = Gemini 3.8 (régua da medição) |
  teste dos 8 modelos + TESTES.md | config\*.antes_argon.json
- 27/10 13:00 | [GRANDE] quem CRIA vira Argon: roteirista `gemini-4-argon` (agentes.llm_roteiro, /v1/messages no
  proxy :20133; falhou -> Gemini) e editor/corretor `argon-gemini` (reserva Gemini 3.8 high). Júri e revisor de fatos
  seguem no Gemini 3.8 (régua) | DONO: "mude o Gemini 3.8 pelo Argon e meça a diferença e tabele" | medição em
  TESTES.md | config\produto_lapidar.antes_argon.json + MODELO_ROTEIRO
- 27/10 12:30 | editor Remotion: legenda pelo Karaoke PRONTO do claude-code-video (`remotion\src\lib\karaoke.tsx`,
  regra no EDITOR.md) | MURAL ccv 12:20 ("TUMBAMONUMENTAL" / caixa vazia) + nosso júri: "legenda perdeu preenchimento"
  | tsc ok; 1º vídeo que usa = o próximo que entrar no editor (o Cardápio de agora já começou) | voltar a regra antiga
  no EDITOR.md
- 27/10 12:21 | 1º vídeo com o código novo (Cardápio, dono_e_cena_veo): TODAS as cenas >= 4% (mín. 5,29), movimento
  5 -> 6, nota 6,25 | lapidar 12:21 | —
- 27/10 11:35 | conversa: pula o zoom quando o fundo é cor lisa (não aparece, só gasta render) | ideia de 4 dos 8
  modelos na caixa | foto 7,05%, liso 6,4% | tirar o `if fundo is not None` em chat_ui.render
- 27/10 11:00 | melhorador.caixa_codigo: pasta com microssegundos | 3 caixas no mesmo segundo -> FileExistsError | teste
  dos Argon | —
- 27/10 09:50 | [GRANDE] cena de CONVERSA com movimento: fundo borrado com zoom lento (12%) e cartão + sombra subindo
  50 px ao longo da cena | júri do Hermes Call 07:28: conversa 1,98% (parada, limite 4%); cartão final já subiu de
  2,5% para 5,4% com o pulso | teste 8 s: 3,6% -> 6,4% (render 46 -> 96 s) e quadros conferidos | botões
  conversa_zoom=0 / conversa_subida=0. A mesma ideia foi para a CAIXA de 8 modelos (teste dos Argon, dono 27/10)
- 27/10 07:25 | ERRO MEU consertado: ao ligar o botão folga_fala (01h, troca por PowerShell) sumiu a linha
  `durs = [...]` -> todo vídeo quebrava (Agenda IA 07:22 "UnboundLocalError durs"; Disparo ia quebrar depois do Veo).
  Linha restaurada, rodada morta reiniciada (Produto_Videos 07:27). LIÇÃO: depois de editar, `python -m pyflakes
  produto\` (nenhum erro sério hoje) — e trocas em código por Edit, não por Replace do PowerShell | log 07:22 |
  —
- 27/10 02:00 | [GRANDE] cartão final VIVO (botão "Chame no direct" pulsa 1,00–1,06 a cada ~1,1 s; fundo com zoom
  ou o Veo correndo atrás) + aproximação lenta (punch-in 6%) nas cenas de vídeo do dono/Veo | ideia do MELHORADOR
  (Gemini, ensaio 01:17) que bateu com a minha análise (júri: cartão parado, plano do dono parado) — feita por mim no
  real; o Gemini fez a mesma na CAIXA para comparar | quadros 0,05 s x 0,55 s (botão maior) e 0,1 s x 3,9 s (zoom)
  | botões pulso_botao=0 / punchin_video=0 em config\produto_ajustes.json
- 27/10 01:17 | [MELHORADOR ensaio — NÃO aplicado] ideia_codigo  = Implementar punch-in nos cortes de fala e animação de pulso no botão da tela final no template Remotion. | Aumentar o dinamismo geral dos cortes e eliminar o aspecto estático da tela final para elevar a nota de movimento. | modelo agy/gemini-3.8-flash-high
- 26/10 19:50 | [GRANDE] voz: TODAS as marcas com a Francisca (ritmo por marca) | OPINIÃO DO DONO: "o final 'chame a
  gente' está saindo em outra língua" — a Thalita é multilíngue (o "direct" vira inglês) e falha ao acaso | amostra
  `produtos_ultimo_video\TESTE_VOZ_final_francisca.mp3` | kit.VOZES
- 26/10 19:50 | [GRANDE] formatos com 4 e 5 Veo: Veo atrás do cartão final (veo_cartao) e da pergunta (veo_abertura);
  variações dono_tres_veo_final (4), quatro_veo (4), cinco_veo (5) | OPINIÃO DO DONO: "ficou bom com 2 Veo, podemos
  fazer com 3 em diante" | teste do cartão sobre vídeo (print) | variacoes.VARIANTES / video.seg_veo_com_cartao
- 26/10 19:30 | vitrine: `D:\hipercool-materiais\produtos_ultimo_video` aberta, último vídeo + OPINIOES.txt | dono | —
  | video.vitrine

🎬 PRODUTOS — VPS Blindada "Seus fluxos estão protegidos?" (26/10 18:58) — nota 6,25 (anterior Follow-up 5,75)
DECISÕES GRANDES: nenhuma nova (validou a abertura com a foto do dono: diretor 4 -> 6)
MUDANÇAS PEQUENAS: • verificador tenta o modelo reserva na 2ª vez (ccv v1.1)
TESTES A/B: formato: dono_abre_fecha_veo_meio (3 Veo) estreou; todas < 6 vídeos
PROBLEMAS ABERTOS: • editor empatou com o molde (6,25) e o render da correção caiu (erro node) • movimento ainda 5
PRÓXIMO: teste misto do MS Energy; medir movimento por cena no próximo vídeo (código novo)

- 26/10 19:05 | verificador: 2ª tentativa com o modelo reserva | v1.1 do ccv | — | lapidar._verificar
- 26/10 19:10 | v1 do claude-code-video: movimento medido por cena (<4% = grave), render com executar() (mata a
  árvore, 20 min, 2ª tentativa, concurrency 2), corretor 45 min, prioridade baixa, EDITOR.md com plano + 8
  composições + APRENDIDO.md do ccv, trava "\d\s*reais" | mural CLAUDE-CODE-VIDEO 19h | movimento no Disparo real
  4,2–7,7%; "Fotos Reais dos Pratos" passa, "99 reais"/"R$ 49" barram | reverter os trechos "v1 do ccv"
- 26/10 18:40 | linha PRODUTOS criada (PROMPT_LINHAS): ESTADO, DECISOES, TESTES, evolucao.jsonl; MURAL e EM_EDICAO |
  dono | — | —
- 26/10 17:00 | foto do dono com prazo de 20 min (thread daemon) | travou 20 min no Chrome remoto | teste5.log | tirar o thread em video.apresentador
- 26/10 16:25 | ffmpeg espera e tenta de novo quando falta memória | VPS perdeu 3 cenas do dono | log 15:16 | video._ff
- 26/10 14:10 | [GRANDE] abertura com a foto do dono + pergunta no alto | diretor: "slide de Canva, sem rosto" (4) | molde VPS 6,25 (diretor 6) | card_pergunta(com_rosto=False)
- 26/10 14:00 | texto escuro em botão de cor clara; chat com letra maior | júri: contraste 1,5:1 / 60% vazio | prints | kit.py texto / chat_ui fontes
- 26/10 13:30 | [GRANDE] 7 formatos com 0/1/2/3 Veo (dono + cena comercial) | dono: "2 Veo, 3 Veo..." | VPS saiu com dono + Veo | variacoes.VARIANTES
- 26/10 13:30 | vídeos do claude-code-video na fila só se passam na trava de texto | Disparo ccv com "Entrega 99,4%" | log da fila | fila.itens_ccv
- 26/10 12:00 | [GRANDE] trava de texto da tela no editor (sem número/%/prazo/preço inventado) | "100% Automático em Minutos" | teste no .tsx real | editor.problemas_texto
- 26/10 08:40 | [GRANDE] editor Gemini em Remotion + corretor (cópia do ccv) | dono: "atualize a sua" | Disparo 5,75 -> 6,0 | config editor.ligado=false
- 26/10 05:00 | [GRANDE] júri de 4 verificadores Gemini a cada vídeo | dono: "analise cada vídeo" | notas em produto_lapidar.jsonl | config ligado=false
