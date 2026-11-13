# Editor de vídeo pronto → Reel no estilo do nosso vídeo de produto (30/10 noite)

Pedido da dona: "uma de edição de um vídeo já pronto: a pessoa envia o vídeo e ele faz o mesmo ou o mais parecido
possível com o nosso sistema de vídeo de produtos com clone que vai para o Instagram".

## Referência (nosso sistema): D:\postador-de-videos\bin\produto\video.py
frase-gancho fixa no topo na cor da marca · tópico numerado "1 · O problema" · legenda KARAOKÊ (3 palavras, a falada
acesa na cor da marca) · barrinha de progresso · cartão final (marca, chamada, @, "Link no perfil") · trilha com
ducking · -14 LUFS. Voz clonada (RVC no PC2) NÃO dá para o aluno: aqui a voz é a da própria pessoa no vídeo.

## Peças (testadas)
- Deepgram (aulacomia, US$ 200 grátis, sem cartão): transcrição pt-BR com tempo por palavra e vícios ("Né", "é")
  marcados com filler_words=true. Chave em ../dg_chave.txt. URL não serve (o n8n não manda content-length): mandar
  o arquivo binário.
- Very Good FFmpeg (mesma conta da V3): roda o comando; /api/tmp-file dá URL para subir o vídeo (PUT) — o navegador
  NÃO pode subir direto (CORS 403), então o vídeo passa pelo n8n (n8n6 aceitou 35 MB em 89 s).
- monta_edicao.js testado no ffmpeg local com amostra/bruto_exemplo.mp4 (40 s com pausas e "né, é"): saiu 33 s,
  -14,0 LUFS, 6 trechos, karaokê ok (bug do toUpperCase no \c corrigido), cartão final ok. Prints em amostra/.
- Exemplo para os alunos: https://files.catbox.moe/gx64ow.mp4 (bruto_exemplo.mp4)

## Falta
- fluxo n8n: página (envia o vídeo + dados) → n8n sobe no tmp-file → extrai áudio (ffmpeg na nuvem) → Deepgram →
  IA (gancho, tópicos com índice da palavra, cartão, cor, trilha, legenda do post) → monta_edicao → render → página.

## PRONTO (30/10 ~19h20) — fluxo y3ckq7OSPtYWWxZo, ativo · /webhook/editor-reel
- gerador: editor/gera_editor.py (constrói o fluxo do zero, 62 nós, notas para o aluno) → n8n6.py importa
- credenciais no n8n6: Very Good FFmpeg ReRD13CCkctXbd8w, Deepgram geS91JlCJqQvmGVc (Header Auth "Token ..."),
  roteador de IA 9L3A8W0GrI5kEyTG, Redis TgnZ028ccZYrorGM.
- testes ponta a ponta: exemplo (38 s de fluxo: 40,1 s → 33,2 s, cortou "Né" e "é", -14,1 LUFS, gancho + 3
  tópicos + legenda do post) e vídeo DEITADO enviado pela rota da página (41 s; virou em pé com fundo desfocado).
  Vídeos em videos_prontos\EDITOR_*.mp4 (ANTES = bruto).
- armadilhas resolvidas: catbox bloqueia download da nuvem → exemplo, trilhas e .ass passam por
  /webhook/editor-reel-arquivo; nó HTTP perde o binário → "Junta o vídeo e o lugar"; ffprobe não existe no VGF →
  duração vem do Deepgram e largura/altura do JPEG do quadro; toUpperCase estragava o \c do .ass.
- 01/11: saída passou para 1080x1920 (regra 1080p mínimo; letras k=1,5) e yuv420p/tv (antes saía yuvj420p por causa
  do JPEG do cartão final). Teste com vídeo REAL filmado (Advance Solar, rapaz andando e falando, 39 s, 81 palavras):
  40-48 s de fluxo, -14,7 LUFS. Original + editado + capa + legenda em
  ..\videos_prontos\EDITOR_Advance_Solar_video_real. teste_editor.py aceita os dados do negócio num .json
  (amostra\dados_advance.json); baixa_resultado.py <job> <pasta> baixa o resultado.
- 01/11 CÓPIAS com mais recursos (original "- ok" intacto), pasta ..\editor_v2 (gera_versoes.py parte do
  fluxo_editor.json e troca caminhos/Redis e os 3 nós da IA e da montagem; monta_edicao.js com NIVEL 2/3/4):
  V2 Dinâmico U2mAIvZGHn5Lmxot /webhook/editor-reel-v2 — jump cut de zoom por frase, abertura grande, palavras-chave,
     whoosh/pop/impacto (feitos no ffmpeg), flash na troca de tópico, cor+nitidez+vinheta, voz limpa, ritmo 1,06x
  V3 Premium EdMGJLgLO4zKq2aa /webhook/editor-reel-v3 — V2 + emojis Noto (fonts.gstatic, 40 conferidos) e glitch
  V4 MIX H2j2ql7Tc6rDUlrh /webhook/editor-reel-v4 — as coisas do montar() do D:\ms-energy\bin\montagem_ms.py em .ass:
     card de pergunta "responder comentário" (ou faixa) 0–2,6 s fora do rosto (IA mede o rosto no quadro), faixa de
     título + etiqueta da etapa (layout aula, tópicos da IA), legenda MIX (5 desenhos, inteligente/livre, giro, pop,
     sublinhado, rastro sem encostar; fontes Luckiest Guy/Bangers/Anton/Montserrat), cartão final com botão em pílula.
  Testes reais (Advance e Globo) em ..\videos_prontos\EDITOR_*: 1080x1920 yuv420p, 60–90 s de fluxo. Teste local
  sem nuvem: editor_v2\roda_local.py <execução> <ia.json> <nivel> <video> <saida>.
- 02/11 "falha de conexão" do cliente no V4: o navegador dele (Chrome Linux, IP 45.71.241.237) desiste de pedido sem
  resposta em 1–4 s (traefik 499). Vídeo de só 1,94 MB, mas o n8n levava ~5,7 s para responder o envio (🧩 Confere o
  vídeo 3,6–4,4 s) e a página até 3,5 s (🧾 Monta a página). Conserto nas cópias V2/V3/V4 (editor_v2\envio_rapido.py,
  chamado pelo gera_versoes.py; o original "- ok" ficou igual): página entregue direto sem nó de código; a página cria
  o código do vídeo e o n8n responde "chegou" em 12 ms e guarda depois; /<rota>-video-status diz pronto/erro; caiu a
  conexão = a página confere e manda de novo sozinha (até 5x); botão Editar tenta 3x. Testado com Chrome sem janela
  derrubando a 1ª tentativa: V2, V3 e V4 ficaram prontos, e o V4 editou até o fim (82 s, 1080x1920 yuv420p).
  Teste: fluxos-n8n\_testes\testa_envio_v4.py <video> [dominio] [rota] [--cai] [--edita].
- 02/11 V5 MIX exemplos reais 1BbEyRWQoGP2Xx9p /webhook/editor-reel-v5 = V4 MIX com 2 botões de exemplo (Advance e
  Globo Solar, preenchem os dados da empresa) no lugar do apartamento (editor_v2\exemplos_reais.py). Os vídeos ficam
  no Redis (ed5:arq:exemplo-advance.mp4 / exemplo-globo.mp4, base64, sem validade; subir de novo: editor_v2\
  sobe_exemplos.py) porque o catbox parou de aceitar envios. Teste pela página (_testes\testa_exemplo_v5.py): Advance
  105 s, Globo 95 s, os dois 1080x1920 yuv420p → 6_EDITADO_V5_exemplo_real.mp4 nas pastas EDITOR_*.
- 03/11 V6 Cards modernos jZBjBYHoVzTAWdi8 /webhook/editor-reel-v6: os cards (pergunta, faixa do título, etiquetas
  das etapas, "Siga @", painel e botão do cartão final) viraram SVG — cantos redondos, degradê da cor da marca,
  brilho, borda clara, sombra; entram subindo/da esquerda junto com o texto e o botão pulsa. O ffmpeg do Very Good
  FFmpeg lê SVG (librsvg; o do PC não — roda_local.py vira PNG num Chrome sem janela). Código: monta_edicao.js
  (NIVEL >= 6, as outras versões iguais) + editor_v2\cards_svg.py (💾 Guarda os cards no Redis, entrega
  cards-<job>-<n>.svg pelo -arquivo). Teste na nuvem com a Advance: 107 s, 1080x1920.
- V6 também tem 3 exemplos CRUS de pessoa real falando (sem legenda/logo/trilha), para o antes x depois ficar nítido:
  entrevistas do AG Jornalismo no YouTube, licença CC BY (crédito no botão e no nome do negócio), cortadas sem o nome
  na tela (videos_prontos\crus\corta_crus.py) e guardadas em 720p no Redis (ed6:arq:exemplo-caue/alderon/luciana).
  Pexels/Pixabay não servem: o Pexels tira o som dos vídeos; os depoimentos do Wikimedia têm vinheta e nome na tela.
- Nova conta do Very Good FFmpeg para outro agente: ..\vgf_conta\LEIA_NOVA_CONTA_VGF.md + vgf_nova_conta.py.
- falta (melhorias, não quebra): voz clonada do nosso sistema não dá para aluno (é a voz da própria pessoa);
  o link do vídeo vale 7 dias.
