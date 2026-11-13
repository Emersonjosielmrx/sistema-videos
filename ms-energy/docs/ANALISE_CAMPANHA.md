# Análise da campanha MS Energy (iniciada 21/10/2026 20:45)

Pedido do dono (21/10): "analise o que podemos melhorar na campanha da ms energy pra ter melhores resultados? os
vídeos às vezes saem com erros e nem sempre são boas propagandas, e mesmo quando usa minha imagem o prompt vai pra
um caminho que o vídeo troca logo no primeiro frame em vez de o vídeo partir em si da imagem".

Regra: cada achado é gravado aqui NA HORA (com a evidência real: arquivo, quadro, log). Ao retomar, seguir só o
que estiver "pendente".

## Frentes

| # | Frente | Status |
|---|--------|--------|
| 1 | Foto do dono não vira o começo do vídeo (como a imagem entra no Flow, o que o prompt pede, o que a montagem põe na frente) — com quadros reais | feito 22/10 |
| 2 | Erros nos vídeos (logs de geração + quadros dos vídeos finais: texto, logo, legenda, corte, áudio, rosto, fala) | feito 22/10 (fala do Veo não transcrita) |
| 3 | Qualidade da propaganda (prompts dos agentes, roteiro/fala, CTA, legenda, card de produto) | feito 22/10 |
| 4 | Resultados reais (Instagram: views/alcance/curtidas/salvos por Reel; TikTok) e o que os melhores têm em comum | Instagram feito 22/10; TikTok não medido (4 posts) |
| 5 | Estratégia de postagem (horário, frequência, legendas/hashtags, Facebook) | feito 22/10 |
| 6 | Lista final priorizada de melhorias | feito 22/10 — aguardando o dono escolher o que implementar |

## Implementação (dono 22/10 00:35: "faça todas as melhorias possíveis pra de fato conseguirmos clientes, tire os
## vídeos quebrados da fila, fotos tem no próprio insta, não precisa da minha voz porque os clientes não me conhecem
## e o Veo já tem a voz dele")

Decisões do dono: fotos de instalação = as do próprio Instagram (@msenergycap); voz = a do próprio Veo (sem voz
clonada do dono; o dono não aparece — clientes não o conhecem). Não respondeu: números que pode prometer (→ nenhum
número), apagar posts de teste/meme (→ perguntar; a API não apaga).

| # | Etapa | Status |
|---|-------|--------|
| I1 | Tirar os 2 quebrados de 21/10 da fila (→ `videos\_revisar`, com MOTIVOS.txt) | feito 22/10 00:40 (fila insta: 3) |
| I2 | Baixar do Instagram: foto de perfil (logo) + fotos de instalação (inclui carrossel) → `assets\fotos_instagram` | feito 22/10 (`bin\baixar_fotos_insta.py`: 142 imagens; logo real = vermelho/preto) |
| I3 | Classificar as fotos por visão (foto real sem texto? descrição lugar/cena) e gerar quadros 9:16 | feito 22/10 (39 boas; 12 viram 1º quadro: sem rosto/texto, sem inversor com marca, recorte ≥330 px, borda preta aparada) |
| I4 | `bin\roteiro_ms.py`: briefing real + pautas (objeções) + regras (sem "zerar", sem número, sem concessionária) + histórico anti-repetição + legenda própria | feito 22/10 (testado: regra pega "zerar"/CEMIG/95%; LLM corrige sozinho; reserva escrita à mão) |
| I5 | `bin\qa_ms.py`: trava (quadro 0 = foto, cena contínua, sem corte, sem faixa preta, duração, cartão, áudio) | feito 22/10 (calibrado: reprovou os 3 clipes ruins antigos pelos motivos certos; Whisper medium ouve a fala) |
| I6 | `bin\montagem_ms.py`: frase no topo + legenda sincronizada (texto do roteiro, tempo do Whisper) + cartão final com logo/foto real/WhatsApp + emenda simples | feito 22/10 (testado num clipe antigo: 11,0 s, trava final aprovou) |
| I7 | `gerar_short_veo.py`: novo fluxo (foto real do Insta OU apresentador IA; sem fotos do dono; sem efeitos de meme; QA antes da fila) | feito 22/10 (escada de contas mantida; reprovado na trava → refaz 1x como apresentador, máx. 2 por short; conta travada no Flow → troca de conta na hora; prova em `cache\veo_clips\reprovados`) |
| I8 | `postar_ms_energy.py`: legenda do sidecar (local, arroba certo, sem CEMIG); novos primeiro | feito 22/10 (antigo só como reserva se a fala passar nas regras: Insta 2 barrados, TikTok 17 barrados) |
| I9 | Agenda: Instagram 2/dia em horário de pico (gera 2/dia); bats LIGAR/DESLIGAR + txt da área de trabalho | feito 22/10 (10:17 e 19:37; botão 1 não liga mais o loop infinito; botão 6 posta 1 por vez) |
| I9b | Token do Instagram: estava no arquivo desde 25/08 sem renovar (vence 60 dias → ~24/10, a postagem pararia) | feito 22/10 02:02 (`postador\bin\renovar_token_insta.py`: novo vence 21/12/2026, testado; roda antes de cada post e renova 1x/semana; cópia `instagram_contas.json.bak_20261022`) |
| I10 | Teste real: 1 vídeo foto-real + 1 apresentador pelo pipeline novo, conferir quadros/QA | parcial 22/10: roteiro, trava (calibrada nos clipes reais), montagem, cartão, postador e agenda testados; 5 clipes reais do Veo gerados e reprovados com razão (drone/placas inventadas); o crédito das 3 contas do pool acabou (renova 23/10 00:05) — a 1ª geração aprovada sai na rodada automática de 23/10 ~01:01 (o controlador tenta de novo 60 min depois do "sem conta" das 00:01) |
| I11 | Revisão do diff + memória + relatório | feito 22/10 05:15 |

22/10 07:50 — dois achados que não dependem de mim:
- **Só 3 contas do Flow no pool** (seebotsia, mundosolar, canalalucinaai): em 16/10 outra sessão comentou 10 das 13
  contas em `D:\veo\beta\contas.py` como "Onda 1.6: teste 2 dias com 3 contas" e nunca voltou (sem registro em
  nenhum doc). MS Energy e Veo dividem essas 3; cada uma faz poucos vídeos por dia. Voltar as contas é decisão do
  dono (mexe no Veo inteiro).
- **Vídeos antigos do Instagram não servem de reserva**: dos 11, só 2 são filmagem real de instalação (drone, com
  marca d'água do TikTok e faixa preta); o resto é desenho 3D, modelo do Canva ("Fauget") ou quadro preto; 1 mostra
  uma funcionária real com a camisa da MS Energy (bom material — só a empresa pode gravar mais).

22/10 ~08:00 — dono respondeu "1 sim, 2 sim, 3 se já tiver novo coloca novo se não deixa o velho":
- 10 contas do Flow religadas em `D:\veo\beta\contas.py` (perfis conferidos no cofre; `contas.py` validou OK).
- 6 posts apagados do @msenergycap (Teste, Teste feed, IA wi-fi, jogador, Viking, Cleópatra) — a API não apaga
  ("Unsupported delete request"); foi pelo navegador do cofre (perfil msenergypara, fora da tela), conferindo conta
  logada, dono e legenda de cada post; a API confirmou que os 6 não existem mais.
- Ordem da postagem já faz o item 3 (novo ms_v2 na frente; sem novo, sai o antigo de reserva); geração disparada
  na hora para tentar ter vídeo novo antes das 10:17.

22/10 08:09–08:34 — 1ª rodada com as 13 contas (lote 2):
- **1º short do formato novo APROVADO**: `videos\shorts_veo\ms_energy_solar_20261022_080937.mp4` (10,7 s): consultor
  de polo vermelha diante de casa com placas e coqueiros, "Chove muito no Pará?" no topo, 8 legendas, Whisper ouviu a
  fala igual ao roteiro (1,0), cartão com logo/WhatsApp. Folha: `_diag\analise\folhas\primeiro_ms_v2.jpg`. Sai 10:17.
- Foto real: 0 de 6 aprovados até agora — mesmo com "tripé travado" o Veo desliza a câmera e rearruma as placas
  (folha `solar_20261022_080937_r1_reprovado.jpg`); o desvio para consultor funcionou como planejado.
- Short 2 reprovado 2x: rosto trocando/mão deformada; depois **barra de status de celular** no topo e letreiro na
  camisa — causa: "vertical smartphone framing" no pedido. Corrigido (câmera de cinema, camisa lisa sem logo/letras).
- LLM devolveu fala sem acento ("A manutencao e dificil?") porque o pedido estava sem acento: pedido reescrito
  acentuado + regra que reprova palavra que só existe com acento. Legenda agora termina antes da emenda do cartão.

22/10 08:37–08:47 — consultor com o pedido corrigido: **2º short APROVADO** (`ms_energy_solar_20261022_083702.mp4`,
10,8 s, "Energia solar no campo", consultora de polo vermelha lisa junto de placas no chão em fazenda; 2 votos nota 8,
sem barra de celular; Whisper 1,0; legenda termina antes do cartão). Fila do Instagram de hoje: 10:17 = 083702,
19:37 = 080937; o antigo (052841) fica de reserva. TikTok 12:10/19:10 pega os mesmos 2 novos primeiro.

Mudanças finais (22/10 03:00–05:10, depois dos testes): foto de drone vai por último na escolha; pedido do Veo com
"tripé travado, câmera parada"; foto real reprovada vira apresentador e no máximo 2 clipes por short; conta que
trava no Flow sai do rodízio por 1 h (antes insistia 4x, ~24 min cada); juiz por visão com 2 votos e temperatura
0,1 (deformação/outra cena só reprovam se os 2 concordam) — recalibrado: os 3 clipes ruins antigos continuam
reprovados.

Aprendido no 1º teste real (22/10 01:50, foto do telhado metálico de 14/04/2022): os 2 primeiros clipes COMEÇARAM
na foto e ficaram na mesma cena (o problema do dono resolvido), mas a câmera "sobrevoou" o telhado e o Veo inventou
placas; um terminou com faixa preta lateral só no último quadro (7,8 s). Ajustes: prompt com câmera quase parada
(aproximação ≤ 10%, sem andar de lado, sem acrescentar placas); número só no início (quadro 0 ≥ 0,80 e 2 s ≥ 0,40 —
os vídeos antigos davam 0,01–0,27 aos 2 s), do meio ao fim vale o juiz por visão; montagem corta os 0,3 s finais.
Whisper medium não carrega 2x ao mesmo tempo (limite de memória confirmada 31,8 GB quase cheio): agora tenta 1 thread
e, se falhar, a trava segue sem conferir a fala (legenda distribuída por igual).
Roteiro: o LLM copiava a frase da pauta (16–22 palavras) e, ao encurtar, escreveu "seu ar-condicionado gera muita
energia" (errado). Agora: pauta = "só a ideia, não copie", exemplos de tamanho, correção mostrando a fala anterior, e um
REVISOR (2ª chamada, temperatura 0,1) que reprova frase tecnicamente errada/sem sentido/exagerada — testado: reprovou
a do ar-condicionado e aprovou a boa. Se tudo falhar, usa a fala de reserva escrita à mão (`RESERVA`).

## Etapa 2 (dono 22/10 ~08:50: "faça" os itens 2 a 5)

| # | Item | Status |
|---|------|--------|
| E2 | Fixar no topo do perfil 3 posts de instalação real (os de 2021 com nome do cliente e mais curtidas) | NÃO DÁ pelo navegador: o menu do Instagram no computador não tem "Fixar" nem "Arquivar" (só Excluir/Editar/Ocultar curtidas/Desativar comentários/Compartilhar/Copiar link/Incorporar); o site de celular nem abriu o menu; a API não tem. Só pelo app — passo a passo pro dono no relatório. Alvos: seu Genival e dona Dayane (CQGUdtIsYC6), seu Neto (CPBgPhVMfq0), seu Luiz Aley (COiwcRut7ts) |
| E3 | Arquivar os Reels antigos de IA (25/08–21/10, ~67: prometem "zerar", citam CEMIG, ~7 views) — arquivar dá pra desfazer | NÃO DÁ pelo navegador (mesmo motivo); não apaguei no lugar (sem volta). Lista dos 67 em `_diag\analise\alvos_perfil.json` |
| E4 | Medição semanal automática (views/alcance/tempo assistido dos Reels novos x antigos) | feito 22/10 09:28: `bin\metricas_insta.py` → `docs\METRICAS_INSTAGRAM.md` + `cache\metricas\<data>.json` + resumo da rotina no Telegram; tarefa `MSEnergy_Metricas` segunda 09:07 (sem janela). Base 22/10: 67 antigos, mediana 7 views, 2,7 s |
| E5 | Vídeo final em 1080x1920 (hoje 720x1280) | feito 22/10 09:20: `montagem_ms` em 1080x1920 (medidas escaladas, logo com realce de borda), trava final confere a resolução; testado num clipe aprovado (10,7 s, aprovado) |

22/10 ~10:10 — mais 1 teste: foto real com "a foto é o PRIMEIRO e o ÚLTIMO quadro" → o Veo obedeceu (parecido 1,0 no
início e no fim; 0,64–0,73 no meio), mas afasta a câmera no meio e o juiz viu placas a mais (nota 3): reprovado.
Consultor reprovado porque o Veo LEU A INSTRUÇÃO em voz alta ("Um homem fala com calma...") — pego pelo Whisper
(fala confere 0,14). Pedido refeito: descrição numa frase e fala no formato 'diz: "..."' + "só esta fala é dita".

Cuidado: o Chrome do cofre `msenergypara` é o mesmo da postagem do TikTok (12:10 e 19:10) — mexer no perfil pelo
navegador fora desses horários.

## Etapa 3 (dono 22/10 ~10:30: "faça")

| # | Item | Status |
|---|------|--------|
| F1 | Aviso de cliente interessado: comentário ou Direct novo no @msenergycap → Telegram na hora (a API lê os dois; o Direct tem 25 conversas) | feito 22/10 13:11: `bin\vigia_clientes_insta.py` (estado `cache\vigia_clientes.json`; 1ª vez marcou 7 comentários e 101 mensagens sem avisar), tarefa `MSEnergy_VigiaClientes` a cada 15 min sem janela; aviso de teste chegou ("enviado"). Achado: Direct parado desde 23/11/2025; 13 das 25 conversas (2024–2025) terminam com mensagem do cliente sem resposta |
| F2 | Bio: "A quase 10 anos" → "Há quase 10 anos" + "📍 Paragominas e região – PA" (limite 150 caracteres) | feito 22/10 ~10:40 pelo navegador do cofre; API confirmou. Para caber, saiu a linha "🚫 Pare de pagar energia abusiva!" (cidades nos posts antigos: Paragominas 3x, Benevides, Santa Maria do Pará) |
| F3 | Medição do TikTok @energia.solar.da (views por vídeo, novo x antigo) junto da medição semanal | feito 22/10 ~13:00: `metricas_insta.py` lê o TikTok Studio pelo navegador do cofre e alerta se tudo estiver em 0. **ACHADO GRAVE: os 5 vídeos do TikTok (19 a 22/10) estão públicos e com 0 views, 0 curtidas, 0 seguidores** — a conta não está sendo entregue (sem aviso no Studio). Suspeitas: conta nova que só posta por automação; vídeo realista de IA sem o selo "gerado por IA". Ver no app: Configurações → Status da conta |

## Etapa 4 (dono 22/10 ~14:00: "faça a postagem de imagens e carrosséis e um medidor de visualizações pro TikTok 1x por dia")

Varredura de 22/10 (perfil público de 50 contas TikTok do postador com @ conhecido; `_diag\analise\varredura_tiktok.json`):
16 com views (as maiores 2.000–2.800, quase todas contas antigas com 20+ vídeos), **32 com TODOS os vídeos em 0**
(a maioria com 1–11 vídeos = contas novas, inclusive o MS Energy), 2 não abriram (banida ou @ errado). 9 contas do
`reuso_plataformas.json` não têm @ anotado (canalalucinaai, jornalcomia, inovaremanhwaverseita...) e ficaram de fora.

| # | Item | Status |
|---|------|--------|
| G1 | Medidor diário de visualizações do TikTok (todas as contas com @ conhecido): histórico por dia, ganho do dia, contas zeradas → relatório + resumo no Telegram | feito 22/10 15:31: `postador\bin\medir_tiktok.py` (Chrome logado do cofre msenergypara; sem login o TikTok não mostra a grade e pede captcha) → `postador\TIKTOK_VISUALIZACOES.md` + `logs\tiktok_views\<data>.json`; tarefa `TikTok_MedirViews` todo dia 07:23. Base 22/10: 50 contas, 18.101 views, 32 com tudo em 0, 1 não abriu |
| G2 | Carrossel educativo do MS Energy no Instagram (6 imagens 1080x1350: capa com foto real, 4 slides, CTA), 3x/semana pela API; IA da Cloudflare só para ilustrar, com trava de visão | feito 22/10 15:25: `bin\carrossel_ms.py` (textos com as regras + revisor; ilustração FLUX.2 klein-4b pelas 60 contas Cloudflare do hipercool via `imagem_reserva` e proxy; visão reprova texto/pessoa/deformação → foto real); 1º publicado https://www.instagram.com/p/DezoB87mJFv/ ("Chove muito no Pará, e agora?"); tarefa `MSEnergy_Carrossel` ter/qui/sáb 12:37 |
| G3 | Botão no painel "medir agora" (adianta a medição do dia) para TikTok e Instagram | feito 22/10 18:05: painel :8790 → Resultados → **Medições TikTok / Insta** (`/api/medicoes` + botões que disparam `TikTok_MedirViews` / `MSEnergy_Metricas` por `tarefa_rodar`; tabelas com filtro/CSV, KPIs, hora da medição e próxima automática). `medir_tiktok.py` refaz todas as contas quando o dia já estava completo. Print PC/celular conferido; clique testado (tarefa rodou) |
| H1 | (dono 22/10 18:20 "1, sim, aí avisa pelo telegram") Resposta automática no Direct do @msenergycap para quem chama (link do WhatsApp) + aviso no Telegram | feito 22/10 18:24 no `bin\vigia_clientes_insta.py` (mesma tarefa de 15 min): Direct novo → resposta com WhatsApp da bio (1x/pessoa/24 h; pula se a empresa já respondeu; só dentro da janela de 24 h da API); comentário novo (≤ 7 dias, sem cara de spam) → resposta privada no Direct + "Te mandamos uma mensagem no Direct 😉" no comentário. Aviso no Telegram diz se respondeu ou o erro. Permissão de envio conferida (erro de teste = "usuário não encontrado", não falta de permissão). As 13 conversas de 2025 estão fora da janela da API |
| H2 | Material real: busca no Google Fotos pelo navegador nas contas já logadas (fabricadeautomacoesia, emersongenc, emersonjosiel649, emersonjosielmrx1995) → fotos de instalação → pasta do MS Energy. Script fica na pasta dos logins. Senhas que o dono colou NÃO são gravadas | feito 22/10 18:30: `D:\logins-google\buscar_fotos_google.py` (genérico, qualquer projeto; usa os Chromes do cofre, as 4 contas já estavam "vivo"; busca do site, baixa a foto em 2048 px e vídeos originais; pula foto repetida entre contas por hash) + `bin\fotos_google_ms.py` (6 buscas: painel solar, placa solar, energia solar, usina solar, inversor solar, telhado → `assets\fotos_instagram\google_fotos`, entra no MESMO `indice.json`, print de celular descartado sem visão, depois a classificação por visão de sempre). 1ª rodada: 690 fotos + 33 vídeos (641 MB). A classificação deu MemoryError aos 273/832 (memória cheia naquela hora) e foi retomada com `--so-classificar`. **Resultado: 82 fotos do Google Fotos aprovadas (as aprovadas foram de 16 para 98)**; amostra de 18 conferida a olho (`_diag\analise\folhas\google_fotos_aprovadas.jpg`): todas são instalações reais em telhado, sem rosto e sem texto, muitas de drone (o `escolher_foto` deixa drone por último) |
| H3 | Gerador de IMAGEM pelo Flow (modelos mais novos), igual ao gera_auto do Veo mas foto; pasta própria `D:\flow-imagens` | feito 22/10 18:55: `D:\flow-imagens\gera_imagem.py` + `LEIA.md`. Modelos no painel: Nano Banana Pro, 2 Lite e 2.1 (padrão). Testado na conta mundosolar: texto→imagem e foto real→mesma cena com outra luz, 768x1376, **0 crédito**. Bug achado no teste e corrigido: a foto enviada aparece na grade e era baixada como resultado |
| H4 | (dono 22/10 "sim troque e comece a produção") Carrossel com Nano Banana no lugar da Cloudflare | feito 22/10 20:55: `carrossel_ms.ilustracao` = Flow → Cloudflare → foto real (visão confere todas); cenário do Pará forçado no prompt (1º teste saiu casa americana); tarefa posta o carrossel já produzido (`_pendente`, até 4 dias). 1º produzido: `videos\carrosseis\20261022_2038` "O painel solar funciona de noite?", 4/4 ilustrações do Flow, 0 crédito, 16 min (seebotsia passou 5 min sem entregar → conta que falha fica 3 h fora). Sai sábado 24/10 12:37. `problemas_texto` agora cita a palavra (o LLM repetia "garantido" 3x sem saber) |
| H5 | (dono 22/10 21:2x) "o Flow não está fechando depois de fazer o serviço, aí fica ocupando espaço" | feito: causa no `D:\veo\beta\gera_auto.py` (vale vídeo E imagem): `_ensure_chrome_running` abria o Chrome da conta e só a pausa do sistema matava. Agora quem abre fecha (`fechar_chrome`, CDP → taskkill) e a abertura foi pra dentro da trava da porta. Testado na imagem (porta 9260 livre ao terminar); vídeo = mesma função, 1ª prova real na geração das 00:01 |
| H6 | (dono 22/10 "faça") Vídeos reais do Google Fotos nos Reels | feito 22/10 23:05: 33 vídeos baixados; 7 trechos aprovados quadro a quadro em `assets\videos_reais\clipes.json` (drone, fibrocimento, cerâmica x2, placa de perto, técnico medindo, visor dos inversores; fora: rosto do dono e filho, festa, piscina, prints de app, clipes de IA, Short de terceiros, resolução < 480). `bin\video_real_ms.py` = 3º formato `video_real` (roteiro com as mesmas regras e até 16 palavras; 2 trechos — o da pauta + o mais "frio"; narradora Thalita com tempo de cada palavra; trilha livre Mixkit/YT Audio Library a 16%; áudio original fora; mesma montagem e trava final). 1º Reel aprovado (13,4 s, Whisper ouviu a fala exata) já na fila. Produção: `--tipo misto` → 1º short dos dias pares; se o Veo ficar sem conta, sai um vídeo real no lugar. Para crescer: rodar `fotos_google_ms.py` com mais buscas/contas e aprovar trechos novos no `clipes.json` |

## Achados

### Frente 1 — foto não vira o começo do vídeo (21/10, evidência: `_diag\analise\folhas\*_cru.jpg` / `*_final.jpg`)

Medido nos 9 clipes crus "com foto" que ainda existem (`cache\veo_clips`, 12/10 a 21/10), comparando a foto com os
quadros do clipe (correlação 0..1, script `_diag\analise\quadros_foto.py`):

- **Em 9 de 9 a cena sai da foto em 0,6–2 s** e vira OUTRA cena (parecido com a foto aos 2 s: 0,01 a 0,49). Exemplos:
  surfista → homem de camiseta colorida num corredor neon (21/10 000146); cirurgião → outro homem segurando conta de
  luz (12/10 172208); cavaleiro no cavalo → outro homem numa sala (12/10 172740); "rosto com teia de aranha" → fundo
  neon de placas (20/10 052133); Monte Rushmore → placas com sol (12/10 171512).
- **Em 3 de 9 o primeiro quadro nem é a foto como ela é**: 19/10 205120 a foto (roupa medieval/dragão) nunca aparece — o
  Flow usou como "referência" e abriu num mundo de algodão-doce com relógios; 12/10 172740 e 173841 começam com a foto
  ENCAIXOTADA (faixas pretas: foto horizontal/quadrada num vídeo vertical).
- **Várias vezes quem fala depois da troca NÃO é o dono** (rosto diferente: 172208, 172740), então "usar minha imagem"
  não cumpre o objetivo.
- **Causa 1 — o roteiro é escrito sem ver a foto**: `gerar_short_veo.py` chama `gerar_prompt_multiagent(tema)` sem a
  foto; os agentes descrevem lugar/roupa/ação próprios. O `gera_auto.py` (linha ~813) só antepõe "Use the uploaded image
  as the starting frame (image-to-video mode). Animate it: <cena dos agentes>". Com texto e foto em conflito, o Veo
  parte da foto e se transforma na cena do texto em ~1 s.
- **Causa 2 — as fotos são as personas dos canais de meme**: `escolher_foto()` do MS Energy sorteia qualquer foto da raiz
  de `D:\veo\fotos` (surfista, cavaleiro, cirurgião, lorde com dragão, Monte Rushmore, Partenon...) — nada a ver com
  energia solar. **38 de 38** vídeos com foto usaram foto com marca "Grok" (relatório `veo\beta\logs\marcas_fotos.json`:
  299 das 305 da raiz têm a marca). O Veo principal filtra isso desde 16/10 (`cron_gerar_video_llm.escolher_foto` +
  `_fotos_com_marca`), o MS Energy não. O "Grok" aparece no clipe CRU (canto, conferido aos 5 s de 000146 e 052133), mas
  no FINAL some porque o `punch_gancho` dá zoom de 12% e corta a borda (sorte, não regra; conferido 0/0,3/0,8/5 s).
- **Causa 3 — a montagem cobre o começo**: `montar_final` (do Veo de memes) põe efeito de abertura no 0,0 s (chiado de TV,
  glitch, portal ou raio — 65 de 65 vídeos) e "impacto" no 0,4 s (starburst, shockwave...). No 21/10 000146, aos 0,7 s a
  tela fica **inteira preta com estrelas**. Resultado visto pelo dono: foto → risco/glitch → tela preta → outra cena.
- Detector de corte (`scene>0,25`) não acusou corte seco nos crus: a troca é uma "transformação" rápida (morph), não um
  corte — por isso parece que "troca no primeiro frame".

### Frente 2 — erros nos vídeos (22/10, evidência: `logs\gerar_diario.log`, `_diag\analise\folhas\*_inteiro.jpg`)

- **Vídeo sai sem o cartão da marca e o pipeline diz "sucesso"**: 21/10 os 2 shorts (000146, 000640) ficaram com 8,0 s,
  sem "Orçamento grátis / Link no perfil" — log: `[montar_final] propaganda falhou: cannot import name 'TiffTags' from
  'PIL' (D:\veo\venv\...)`. `gerar_short_veo.py` só confere `meta["ok"]` (cópia do arquivo), não `propaganda.aplicada`;
  exit 0 e o vídeo entra na fila de postagem. 22/10 voltou a funcionar (Pillow consertado), mas nada impede repetir.
- **Clarão/tela preta no 1º segundo (todos os 65)**: efeito de abertura do `montar_final` — aos 0,5 s o quadro fica quase
  todo branco (000152, 052133, 000640: "raio"/"chiado_tv") e aos 0,7 s inteiro preto com estrelas (000146: "starburst").
  É exatamente a janela do gancho (primeiros 2 s), onde a pessoa decide se continua.
- **Faixas pretas (vídeo encaixotado)**: 21/10 000640 (criativo) tem faixa preta em cima e embaixo do começo ao fim;
  12/10 173841 e 172740 começam com a foto encaixotada (foto não vertical). Ninguém confere isso antes de postar.
- **Pessoa troca de rosto no meio**: após a transformação, quem fala muitas vezes é outro homem (172208, 172740); no
  criativo é sempre um desconhecido (prompt "The person in the frame..." sem foto nenhuma).
- **Resto de transição em cima do cartão**: aos 8,1 s (000152, 052133) aparece um semicírculo azul enorme no topo
  (transição "agua"/"gelo") sobre o card escurecido.
- 1 falha de geração nos logs desde 19/10 (20/10 "nada começou a gerar em 8 min") — a escada de tentativas resolveu
  sozinha na 2ª tentativa.
- Volume já é nivelado desde 21/10 (−14 LUFS). Resolução é 720x1280 (o CLAUDE.md do projeto pede 1080x1920).

### Frente 3 — qualidade da propaganda (22/10)

- **Mesma fala todo dia**: últimas 4 falas = "Sua conta de luz vai zerar ou você vai continuar pagando à vista?", "...vai
  zerar e você nem sabe como", "...vai zerar com isso!", "...vai zerar e ninguém te contou como". Títulos idem ("Como
  zerar a conta de luz..."). Público cansa; e a conta não zera: sempre fica a taxa mínima/iluminação pública e, para
  sistemas ligados depois de 2023, a Lei 14.300/2022 cobra uma parte crescente do Fio B (de memória: 60% em 2026 —
  conferir) — risco de propaganda enganosa (CDC art. 37 / CONAR) para um cliente real.
- **Fórmula de meme no prompt do Veo**: sempre "The person in the frame gasps in shock / shouting to camera" + "solar
  panels flash neon blue" → caretas, gritos, painel com raios elétricos (parece perigo, não segurança/confiança).
  Herança do pipeline de memes (`D:\veo\beta\agents.py`, `run_pipeline`).
- **A causa exata da "troca no 1º frame" está no prompt do diretor de cena** (`D:\veo\beta\llm_client.py`
  `gerar_prompt_viral`, linhas 420–447), usado pelo MS Energy via `agents.run_pipeline`:
  1. formato obrigatório "The person in the frame [doing X] **in [Y setting]**" → o LLM INVENTA um lugar sem saber qual
     é o da foto (ele não recebe a foto) → o Veo sai do lugar da foto para o inventado;
  2. "Estilo: viral TikTok, cores vibrantes, lighting chamativo" (e no modo 3 cenas `_agent_scenario_director_multi`
     fecha com "neon vibrant lighting") → muda luz/cores da foto;
  3. "CRÍTICO: 0–1 s GANCHO VISUAL forte — reação de choque, nunca pose estática" (multi: "movimento brusco ... no
     primeiro frame") → força movimento brusco exatamente no começo;
  4. modo 3 cenas (30% das vezes, `multi = random.random() < 0.3`) = 3 cenas em 8 s → mais trocas.
  5. o mesmo texto supõe foto SEMPRE — no modo "criativo" (sem foto) o Veo inventa um desconhecido.
- **Nada da empresa real chega aos agentes**: só `canal="MS Energy Solar"` + um tema sorteado de 6. Não sabem que é do
  Pará, ~10 anos, residencial/industrial/rural, instalação e manutenção, orçamento pelo WhatsApp; não há regras de
  propaganda (não prometer "zerar", não citar concessionária, não inventar números). O crítico dá nota por "viral"
  (choque, medo, compartilhável), não por propaganda (confiança, clareza da oferta, CTA) → notas 8–9 para meme.
- **Por que a fala repete**: `gerar_short_veo.py` chama `run_pipeline` sem `exemplos_falas` → a regra "não repita" do
  `gerar_fala_viral` nunca recebe histórico; cada dia começa do zero e cai em "Sua conta de luz vai zerar...".
- **Cartão e voz do CTA foram feitos para a regra do YouTube**, mas o MS Energy só posta Instagram/TikTok: `cta_card` e
  `cta_builder._narracao_cta` tiram WhatsApp/contato (item IM-01 de 16/10, anti-spam do YouTube); o cartão diz só "MS
  Energy Solar / Orçamento grátis de energia solar / LINK NO PERFIL" sobre fundo genérico de IA (estrelas, grade
  neon). Sem logo (`produto_solar.json`: `logo_png: null`), sem cidade/região, sem foto de instalação real. Voz: 5
  vozes padrão em INGLÊS do ElevenLabs (sarah, bella, matilda, adam, eric) com `eleven_multilingual_v2` falando
  português — provável sotaque de gringo (não ouvi; suposição pela configuração).
- **Promessas do produto a confirmar com o dono**: `cta_longo` = "pode cair mais de 90 por cento" e "instala em até 3
  dias" — número em propaganda precisa ter base.
- **Legenda ignora o que a IA gerou**: o sidecar tem `titulo`/`descricao` (LLM), mas `postar_ms_energy.py` monta a
  legenda com os 15 ganchos fixos + CTA fixo ("Siga @MSEnergySolar...") e manda a MESMA para Instagram e TikTok.

### Frente 4 — resultados reais no Instagram (22/10, Graph API; dados em `_diag\analise\insta_insights.json`)

Perfil real: **@msenergycap** "|MS energy| Energia Solar", 2.075 seguidores, bio "Ind/Res/Rural · Instalação e
Manutenção · quase 10 anos no mercado · Orçamento Grátis", link = WhatsApp (wa.me). **A empresa é do PARÁ** (posts
antigos: "Instalação do seu Luiz Aley em Paragominas-PA", "seu Neto em Santa Maria do Pará", telefone (91)).

| Grupo | n | views (mediana / média / máx) | curtidas | assistido em média |
|---|---|---|---|---|
| Reels de IA (desde 25/08/2026) | 70 | **7** / 8,4 / 41 | **3 no total** (0 coment., 0 compart., 0 salvos) | 3,3 s (mediana 2,7 s) de ~12 s |
| Reels antigos com vídeo real (2022–2024) | 10 | 170 / 232 / 638 | 73 | 4,1 s |
| Fotos de instalação/feed (2021–2024) | 82 | — | 966 (média 11,8; 21 salvos, 8 coment.) | — |

(os antigos tiveram anos para acumular, mas a diferença é de ~25x em views e de 0 para 7–12 curtidas por post.)

- **O público sai nos primeiros 2–3 s** (mediana 2,7 s): bate com o 1º segundo destruído (foto aleatória → clarão/tela
  preta → transformação) — o gancho não segura ninguém.
- **Postagem em rajada** (agosto): 26 Reels em 27/08 e 18 em 28/08; 20 Reels saíram a menos de 15 min do anterior
  (12/10 também: 6 em 30 min — foi a rodada manual que eu rodei a pedido, com 2 min de intervalo). Rajada + legenda
  repetida = sinal de spam.
- **Legendas repetidas**: a 1ª linha vem de 15 ganchos fixos do `postar_ms_energy.py` (GANCHOS_VIRAIS): "O segredo pra
  NUNCA MAIS pagar conta de luz cara!" 8x, "Isso tá deixando as distribuidoras LOUCAS!" 6x, etc.
- **"A CEMIG não quer que você veja isso..." (4x)**: CEMIG é de Minas; a empresa atende o Pará (Equatorial Pará).
- **Arroba errado nas legendas**: CTAs fixos mandam "Siga @MSEnergySolar" (marca.json watermark), mas a conta é
  @msenergycap; `produto_solar.json` ainda diz "@msenergy". Não conferi de quem é @MSEnergySolar.
- **Posts que não deveriam estar no perfil de um cliente real**: "Teste" e "Teste feed" (27/08), "A inteligência
  artificial já usa seu wi-fi..." (26/08), "jogador... pressão 😂" (24/03/2026), "Viking ia #shitpostbrasil" e
  "Cleópatra solar #shitpostbrasil" (14/07/2025). Apagar é decisão do dono (não mexi).

### Frente 5 — estratégia de postagem (22/10, `videos\postagem_log.json` + preview do postador)

- **Fila do Instagram cresce 1 por dia**: gera 2/dia (07:20 → na prática 00:01, ver tarefa) e o Instagram posta 1/dia
  (10:17). Hoje: 5 pendentes — incluindo os 2 QUEBRADOS de 21/10 (sem cartão; 000640 com faixas pretas e um rapaz que
  não é o dono), que sairiam 23 e 24/10.
- **TikTok (@energia.solar.da) posta os mais VELHOS primeiro** (fila por nome): os 4 posts desde 19/10 são vídeos de
  26/08 (pipeline antigo). Os novos só chegam lá depois de ~49 antigos. Números do TikTok não medidos (só 4 posts).
- Facebook (página mundosolarenergia): 16 posts em agosto, nenhum depois (não está agendado).
- Horário único 10:17 no Instagram; posts em rajada no passado (ver frente 4).
- Quem dispara a geração hoje é o controlador central (`D:\video-fila\controlador.py` → `cron_gerar_ms_energy.bat`,
  ~00:01); a tarefa `MSEnergy_Gerar` do Agendador está desabilitada.

### Frente 6 — melhorias priorizadas (22/10)

Regra de arquitetura: `agents.py`, `llm_client.py` e `montar_final.py` são do Veo de memes (outros canais usam). Tudo
do MS Energy deve ser feito no `gerar_short_veo.py` / módulo próprio em `D:\ms-energy\bin`, sem mexer no comum.

**Prioridade 1 — o que o dono reclamou e o que vai ao ar quebrado**
1. Tirar da fila os 2 vídeos de 21/10 (sem cartão; 000640 encaixotado) — decisão do dono — e criar a trava antes da
   fila: sem cartão (`propaganda.aplicada` falso), duração < 10 s ou faixa preta → pasta "revisar" + aviso, nunca posta.
2. Vídeo partir da foto: (a) pasta própria de fotos do dono em contexto de energia solar (telhado com placas, casa,
   conta de luz, escritório), verticais, sem marca de IA — feitas 1x (foto real ou Nano Banana a partir das dele);
   (b) cada foto com descrição fixa (lugar, roupa, pose, luz) e o prompt vira CONTINUAÇÃO dela: mesma pessoa, lugar,
   roupa e luz; aproximação lenta da câmera; ele vira e fala; "um plano contínuo, sem cortes, sem mudar de lugar" — sem
   "in [Y setting]", sem neon, sem "choque no 0–1 s", sem 3 cenas; (c) conferência automática depois do Veo (quadro 0 =
   foto; aos 2 s e 4 s ainda a mesma cena; sem faixa) → refaz 1x ou descarta (base: `_diag\analise\quadros_foto.py`);
   (d) recortar a foto para 9:16 antes de subir. Testar com 2–3 gerações numa conta antes de virar produção (gasta
   crédito). Não verifiquei se a tela nova do Flow tem modo "quadro inicial" explícito.
3. Montagem sem efeitos de meme no MS Energy: sem abertura (chiado/glitch/portal/raio/starburst), zoom suave, transição
   simples para o cartão (parâmetros do `montar()` chamados pelo `gerar_short_veo.py`).

**Prioridade 2 — propaganda melhor**
4. Roteiro próprio do MS Energy: briefing (Pará, quase 10 anos, residencial/industrial/rural, instalação e manutenção,
   orçamento grátis no WhatsApp) + regras (nunca "zerar"/"R$0", não citar concessionária, número só com base) + últimas
   30 falas para não repetir + crítico que avalia propaganda (confiança, oferta clara, CTA, público local).
5. Pautas de objeções reais: em quanto tempo se paga, chuva/nuvem no Pará, financiamento, manutenção/limpeza, o que
   mudou com a Lei 14.300, rural (bomba/irrigação), comércio/indústria.
6. Cartão: logo real, "Orçamento grátis pelo WhatsApp — link no perfil", região atendida, fundo com instalação real;
   voz brasileira (ou a voz clonada do dono) no lugar das vozes em inglês.
7. Legenda: usar a legenda da IA já gerada, com termos locais; tirar CEMIG e "@MSEnergySolar"; acabar com os 15 ganchos
   fixos; legenda própria para TikTok.

**Prioridade 3 — distribuição e medição**
8. Ritmo: gerar 1/dia (economiza crédito) ou postar 2/dia espaçados; nunca rajada.
9. TikTok: novos primeiro (ou só os feitos depois das correções), não o lote de agosto.
10. Perfil: apagar "Teste", "Teste feed" e os memes (Viking, Cleópatra, jogador, IA wi-fi); fixar posts de instalação
    real — decisão do dono.
11. Material real da empresa (fotos/vídeos de instalações e clientes, com autorização): é o que mais deu curtida no
    histórico (7–12 por post x 0 dos de IA); pode até animar foto real de instalação no Veo.
12. Medir toda semana com `_diag\analise\insta_insights.py` (meta inicial: assistido > 5 s, > 50–100 views por Reel) e
    comparar formato novo x antigo.

**Preciso do dono**: cidade/região atendida; números que pode prometer (economia %, prazo de instalação); logo;
fotos/vídeos reais de instalações; se pode usar a voz dele clonada; se apaga os posts de teste/meme; se tira os 2
vídeos quebrados da fila.


