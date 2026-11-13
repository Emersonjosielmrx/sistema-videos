# Linha PRODUTOS — estado (retomar daqui)
Prompt desta linha: `linhas\PRODUTOS\PROMPT_PRODUTOS.md` (cópia adaptada do `linhas\PROMPT_LINHAS.md`, que é o geral).

Dono da linha: sessão do postador (vídeos de produto com o dono no Veo). Dono 26/10 18:30: "o VEO é o Veo de
entretenimento pro YouTube; o Veo com produtos é a sua linha".

## O que é a linha
- Comerciais de Instagram dos NOSSOS produtos (Hermes Call, Cardápio, Agenda IA, Disparo, Follow-up, VPS, Fábrica) +
  formato misto do cliente MS Energy (dono no Veo + instalações reais).
- Código: `D:\postador-de-videos\bin\produto\` (video, agentes, kit, chat_ui, carrossel, lapidar, editor, motor,
  variacoes, fila, diario) + `D:\postador-de-videos\remotion\` (EDITOR.md, node_modules = junção do ccv).
- Outra sessão toca o `D:\claude-code-video` (mesma linha, ciclo em `claude-code-video\docs\CICLO_MELHORIA.md`): não
  mexo lá; os vídeos de lá que passam na trava de texto entram na nossa fila (`fila.itens_ccv`).
- Saída: `D:\video-fila\produto_fila\<conta>\` (`_postados`, `_revisar`, `_molde`); carrosséis em
  `D:\video-fila\carrosseis_marcas\<conta>\*_produto`.
- Tarefas: Produto_Videos 04:41/13:41 (`produto.diario`); postagem pelas rodadas do Instagram (06:40, 14:05, 19:35);
  carrossel Marcas_Carrossel 07:13.
- Doc detalhado (histórico, rodadas de melhoria): `D:\postador-de-videos\docs\PRODUTO_PROFISSIONAL.md`.
- Logs: `logs\produto_videos.log`, `logs\produto_contas_novas.log`, `logs\produto_lapidar.jsonl` (notas do júri),
  `logs\produto_motor.jsonl` (chamadas Gemini), `logs\instagram_auto.log`.

## Agora (27/10 11:40)
- Hermes Call (inovarecom.ia) NA FILA 11:08 pelo molde (5,75): o editor estourou 1 h DUAS vezes (10:07 Gemini 3.8 high,
  11:07 tiered) — coincidiu com o teste dos Argon martelando o gateway (suposição). Próxima rodada Produto_Videos 13:41.
- Conversa parada (1,98%) consertada no chat_ui: zoom do fundo + cartão/sombra subindo (botões conversa_zoom/subida);
  pula o zoom no fundo liso (ideia que veio da caixa). Medido: 7,05% com foto de fundo, 6,4% liso.
- TESTE DOS ARGON (dono 27/10) FEITO: análise/roteiro/código de 8 modelos -> `D:\gemini-argo\COMPARACAO_MODELOS.md`
  (documento ÚNICO de todos os chats; detalhe em `analises\2026-10-27_PRODUTOS.md`). Resultado: Argon puro 9,5 na
  análise do melhorador; roteiro curto empate (Gemini 3.8 fica, 24 s); código: quase todos 8–10, Argon+Gemini 10;
  argon-kiro resposta falsa. ESPERANDO o dono dizer se põe o Argon puro em 1º no analista/decisor do melhorador.
- melhorador.caixa_codigo: nome de pasta com microssegundos (caixas paralelas colidiam).

## Antes (26/10 18:40)
- VPS (dono + cena Veo comercial) no editor Gemini desde 17:49; molde 6,25 (melhor até agora). Depois: teste misto
  do MS Energy (`D:\ms-energy\_diag\teste_misto\teste6.log`, só pro dono aprovar).
- Postados hoje nas contas novas: Fábrica 10:21, Follow-up 14:13. Disparo: 2 versões barradas (número inventado).

## AGORA (28/10 11:00) — ciclo de melhoria (TRABALHO PRINCIPAL, dona 28/10)
Notas paradas 5,3–6,25 nos últimos 8 (fracos: movimento 4–5, diretor 4–6). Feito hoje: destaques da fala na cena de
imagem, cabeça do dono livre no cartão da pergunta, cartão final com entrada+brilho (DECISOES 28/10 11:00).
Próximo a medir: 1º vídeo da rodada 13:41 (júri movimento/diretor x 5/5 de antes). Próximos graves da lista:
(4) legenda some antes do fim da fala na cena do DONO (Fábrica q12, Disparo) — conferir a transcrição do Veo;
(5) imagem de banco genérica que não mostra o produto (diretor) -> trocar bloco "imagem" do "como funciona" por
conversa/tela do produto; (6) gancho 0–2 s parado.
FEITO 11:40: (4) era dono MUDO 2 s no fim do clipe (não a legenda) -> cena cortada 0,45 s após a última palavra.

## PLACAR DAS VARIAÇÕES NUNCA MEDIU (28/10) — o melhorador aprende às cegas
`variacoes.medir` só mede post com media_id; TODOS os 20 de produto foram pelo navegador ("navegador") e os tokens
de inovarecom/futebolcom/sintetizerisada venceram (24/10 e maio) -> placar 0 desde sempre (Thompson sem dado).
Feito: `produto\medir_insta.py` (sessão já logada pelas máquinas, API interna do site) — NÃO LIGADO no medir.
Teste 10:41: rota feed/user/<nome>/username = 404; web_profile_info+feed/<id> = 429 na 1ª (somou as 2 tentativas).
PAREI (risco de conta). Próximo, em OUTRO dia, 1 conta: página /<conta>/reels/ como pessoa (contagem do grid) e casar
por ordem só nas contas que só recebem produto; ou a dona renovar os tokens (resolve sem navegador).

## MÁQUINAS 28/10 10:20 — FEITO: render Remotion do editor vai pro PC2 (`editor._render_pc2`, C:\produto-pc2\remotion)
Falta (próximos passos): (1) conferir no log o 1º vídeo real com "[editor] render no PC2"; (2) mandar também o
render final do molde (o `_ff` grande do video.gerar, camada+áudio) e o chat_ui.render; (3) o júri (lapidar, quadros
por ffmpeg) é leve, fica. ssh do Python pro PC2: SEMPRE `input=""` (ver DECISOES 28/10).

## MÁQUINAS (dona 27/10 20h) — produto inteiro no PC2 = A FAZER (instalação de horas)
PC2 = i3-7100U (4 threads), 11,7 GB, SÓ C: com 23,6 GB livres, sem D:, nada da linha lá; tem o venv do recap (PIL,
cv2, edge_tts, playwright, numpy) e Node. Plano: PC1 continua orquestrando o leve (roteiro, Veo pelos notebooks) e
manda o PESADO pro PC2 (montagem ffmpeg, conversa animada, Remotion editor/render, júri por quadros), como os Cortes;
falta instalar: código produto + configs/fontes/trilhas em C:\produto-pc2, ffmpeg, node_modules do Remotion (~0,5 GB),
claude.exe pro editor. Veo/navegador da linha: notebooks -> PC2 -> desktop (câmera livre) -> PC1 por último.
Feito hoje: telão+medidor 24 h no PC2 (desktop instala sozinho quando o sshd voltar), análise diária 08:05.

## CHAT DA DONA COM O MELHORADOR (27/10 20h) — `CONVERSAR_MELHORADOR.bat` (nesta pasta)
Terminal com o Claude Code na pasta da linha: papel e regras em `CLAUDE.md` (daqui), permissões em
`.claude\settings.json`, config isolada em `.conversa\` (sem hooks/plugins do VS Code, no D:). Abre CONTINUANDO a
última conversa e já se atualiza ("onde estamos" em 6 linhas). Modelo: teste rápido na cadeia
`melhorador_produtos.json -> conversa.cadeia` (Gemini 3.8 high -> Gemini 3.5 API; modelo novo de código: testar depois).
Código `postador-de-videos\bin\produto\conversa.py`. Testado sem janela (-p): leu CLAUDE.md, usou Read, --continue
lembrou a conversa. A janela interativa em si não foi testada aqui (precisa de terminal real).

## MELHORADOR automático (27/10, pedido do dono) — PRONTO E DESLIGADO
Assume o meu lugar no botão: `LIGAR_MELHORADOR.bat` (ensaio: só propõe) / `LIGAR_MELHORADOR.bat aplicar` /
`DESLIGAR_MELHORADOR.bat` (nesta pasta). Tarefa `MelhoradorProdutos` (30 em 30 min) criada DESABILITADA.
- Código `postador-de-videos\bin\produto\melhorador.py`; prompts `config\melhorador\{analista,decisor,revisor}.md`
  (ir afinando com o que eu aprendo aqui); config `config\melhorador_produtos.json`; botões `produto\ajustes.py`
  (+ `config\produto_ajustes.json`); regras aprendidas `config\produto_regras_roteiro.md` e a seção MELHORADOR do
  `remotion\EDITOR.md`. Estado/placar dos modelos `melhorador_estado.json`, log `melhorador.log`.
- Só mexe em botões com faixa, formatos e regras curtas; código vira "ideia_codigo". Revisor adversário + trava em
  Python. Vigia: nota cai >= 0,5 nos 2 vídeos seguintes = desfaz sozinho.
- Modelos (dono 27/10): Kiro desligado até 01/11; Gemini 3.8 = teste de hoje; Opus 4.6 (antigravity) e Opus 5.5
  (cc, só com cota acima da reserva do dono) na cadeia do decisor; Argo entra quando o dono avisar. O placar por
  modelo (ok/falha, propostas, aprovadas, mantidas, desfeitas) decide quem fica: modelo menor só fica se aliviar os
  maiores.
- Teste: `python -m produto.melhorador --ensaio <video.json> --modelo agy/gemini-3.8-flash-high`.

## Vitrine do dono (26/10 19:30, pedido dele)
`D:\hipercool-materiais\produtos_ultimo_video\` fica ABERTA no Explorer: o vídeo mais novo começa com `0_ULTIMO_`
(+ .txt com status, formato, nota do júri), os 6 mais novos ficam. `video.vitrine()` copia todo vídeo que sai
(fila, reprovado ou teste). O dono escreve opiniões em `OPINIOES.txt` -> LER A CADA CICLO; opinião = GOSTO
(vira variante/teste) ou CERTEZA (corrigir já), e anotar no DECISOES de onde veio.

## Ciclo (como espero o próximo vídeo)
Comando em segundo plano que termina quando aparece .json novo em produto_fila/<conta>, _revisar ou
ms-energy\_diag\teste_misto (marca: linhas\PRODUTOS\.marca), ou "SEM VIDEO em 6 h". Aprendizado lido 26/10 19:15:
aprovado 5a106596 (narração informal) é das histórias — não se aplica a propaganda de produto.

## Base da seção 3 (conferido 26/10)
| item | estado |
|---|---|
| 1 borrão/tarja | não se aplica (material nosso, sem legenda queimada) |
| 2 CTA no meio + mascote | FALTA: CTA só no cartão final; mascote não se aplica (marca própria) -> testar CTA no meio (GOSTO) |
| 3 voz clonada | FALTA: narradora edge (Thalita/Francisca); dono fala com a voz do Veo -> testar clone Francisca (GOSTO) |
| 4 narração de locutor | FALTA: edge sem curva de clímax -> ver narracao_curva dos Cortes |
| 5 sincronia | ok (tempo de cada palavra do edge; legenda por fala desde 26/10) |
| 6 tecnologia do ccv | ok: júri Gemini (lapidar.py), editor Remotion + corretor (editor.py); FALTA: APRENDIDO.md reescrito a cada vídeo e medida de movimento por cena (<4% = parada) |
| 7 áudio | ok: −14 LUFS (nivelar), ducking sidechain; trava_final confere áudio |
| 8 gancho 0–2 s / nada parado | em andamento (abertura com a foto do dono, Ken Burns 16%, chat espalhado) |
| 9 SEO | ok: legenda + 5 hashtags por produto (corrigido 26/10) |
| 10 segurança | ok: trava de texto (número/prazo/%/preço), revisor de fatos, sem contato na tela |
| 11 produção fora do PC1 | FALTA: ffmpeg e Remotion rodam no PC1 (sem RAM: caiu por "Cannot allocate memory") |

## Lista de melhorias (tipo | impacto | esforço | risco | outras linhas?)
1. CERTEZA | alto | médio | baixo | sim — medida de movimento por cena (diferença 20%->80%) antes do júri; <4% = refazer a cena com mais zoom/elemento.
2. CERTEZA | alto | alto | médio | sim — render (ffmpeg/Remotion) fora do PC1 (PC2/desktop) quando a RAM < 3 GB.
3. CERTEZA | médio | baixo | baixo | não — APRENDIDO.md (resumo do júri reescrito a cada vídeo) lido pelo editor.
4. GOSTO | ? | médio | baixo | — teste: voz clonada Francisca x edge (fator "voz").
5. GOSTO | ? | baixo | baixo | — teste: CTA no meio (pílula "Chame no direct" no bloco 2) x só no fim.
6. CERTEZA | médio | médio | médio | Veo — acer falha na tela do Flow (medir por máquina antes de mexer no gera_auto).
7. CERTEZA | médio | baixo | baixo | ccv — a trava de texto não existe no claude-code-video (pedido no MURAL).

## 27/10 05:55
- Teste misto MS Energy PRONTO (molde 5,5; editor barrado por falso positivo "10 anos" — corrigido — e render
  falho): `ms-energy\_diag\teste_misto\msenergysolar_pa_20261026_185920.mp4`, na vitrine como 0_ULTIMO. Dono abre
  falando (cenário padaria — pedir cenário de telhado/obra no próximo), 3 trechos REAIS de telhado, cartão
  "Orçamento grátis". Voz Thalita e cartão parado (processo começou antes das mudanças). ESPERA APROVAÇÃO.
- Treino do melhorador (treino.jsonl): Gemini analista/decisor bom (4/5 + 1 acerto que eu errei); executor
  reprovado (resposta falsa) — não deixar mexer em código.

## PRECISA DO DONO
- Logar de novo no Flow: emersonjosiel2026, inovaremanhwaverse, inovaremanhwaverseind (deslogadas 26/10).
- Renovar token do Instagram de inovarecom.ia e videocassetadascom.ia (posta pelo navegador enquanto isso).
- Aprovar o 1º vídeo misto do MS Energy (assim que sair).
