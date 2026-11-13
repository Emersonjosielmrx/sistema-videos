# Fluxo "Vídeo de Anúncio com IA" sem video-oficina (30/10)

Pedido da dona: cópia do fluxo n8n6 YAqU7XKvLFmryX0C usando API externa (pros alunos, que não têm o video-oficina).
Fazer 2 ou 3 versões até 30/10 10h. Original fica intacto. Cron de hora em hora (:17) nesta sessão continua o trabalho.
Pasta: D:\hipercool-materiais\fluxo-anuncio-api (saiu do D:\tmp porque algo apaga arquivos lá).

## Peças (testadas de verdade)
- JSON2Video: conta aulacomia@gmail.com (Google do cofre), chave em j2v_chave.txt (NÃO publicar), 600 créditos únicos
  (~10 min), marca d'água no grátis. No n8n6: credencial "JSON2Video (x-api-key)" id q7liHJkulD2fpkHt.
- n8n6: chave da API (label "vibe") em n8n6_chave.txt; n8n6.py importa/ativa. Caminho dinâmico ":id/xxx" não pode
  repetir entre fluxos (conflito mesmo com outro webhookId) -> página pública = :id/anuncio-video.
- catbox.moe recusa envio da VPS 157 ("Invalid uploader"); do PC funciona. Exemplos e trilhas estão lá (urls.txt).
- Fotos dos alunos: o próprio n8n guarda no Redis (30 dias) e entrega em /webhook/anuncio-video-j2v-arquivo?id=...
- wsrv.nl: miniatura e medidas por URL (lê o endereço do n8n). Testado.

## V1 = JSON2Video — PRONTA (fluxo 6tkiscDQZPbSHVov, ativo)
- formulário: /webhook/anuncio-video-j2v · gerador em v1/gera_v1.py (rodar: python gera_v1.py q7liHJkulD2fpkHt; depois
  python ../n8n6.py importa v1/fluxo_v1.json)
- testes ok: exemplos apartamento vertical 30 s (124 s) e fotos ENVIADAS hamburguer quadrado 15 s (77 s);
  quadros em provas/ (narrado com legenda, só música sem voz/legenda, cartão final, selo de preço).
- limites conhecidos: marca d'água; vídeos somem em 7 dias (página fica, capa no Redis); legenda é transcrição
  automática (ouviu "Fitas" por "Fritas"); HEIC não (a página converte para JPG no navegador, só falha se o navegador não abrir).

## V2 = Shotstack — PRONTA (fluxo dqn4gkVwqgaFWhmr, ativo, credencial SjCl7TFaI1BYM4oD = chave SANDBOX)
- formulário /webhook/anuncio-video-ss · gerar: v1/gera_v1.py e depois v2/gera_v2.py SjCl7TFaI1BYM4oD (parte do fluxo_v1.json)
- testes ok: fotos enviadas hambúrguer vertical 30 s (171 s) e exemplos apartamento deitado 15 s voz Andrew (167 s).
  Vídeos ficam no CDN do Shotstack sem prazo. Legenda longa ajustada (letra menor, caixa maior) e progresso não desce.
- notas antigas abaixo:
- conta: aulacomia@gmail.com (Google do cofre, questionário respondido). shotstack_chaves.txt: linha 1 = sandbox
  (stage, render grátis com marca), linha 2 = produção (v1, 10 créditos). Voz ElevenLabs ~0,19 crédito/anúncio,
  cobrada do saldo de produção MESMO no sandbox; voz repetida não paga de novo.
- v2/monta_filme.js testado no sandbox (provas/v2_t2_quadros.jpg, v2_mus_quadros.jpg): ok. Legenda = texto exato do
  roteiro subindo palavra por palavra (transcrição deles errou "suíte" -> "switch").
- falta: v2/gera_v2.py (parte do fluxo_v1.json e troca só o motor), credencial, importar, teste ponta a ponta.

## Mudança comum (07:40): fotos de EXEMPLO também passam pelo n8n (/…-arquivo?id=exemplo-apartamento-1); o
wsrv.nl dava 404 lendo direto do catbox. V1 e V2 regeradas, reimportadas e V1 retestada ok (124 s).

## V3 = Very Good FFmpeg + voz do Google Tradutor — PRONTA (fluxo YCgHfZsOdiHeoeCw, ativo, credencial ReRD13CCkctXbd8w)
- conta verygoodffmpeg.com (Google do cofre, SEM cartão, US$ 1 = 2 GB grátis), chave em vgf_chave.txt.
- formulário /webhook/anuncio-video-ff · gerar: v1/gera_v1.py, depois v3/gera_v3.py ReRD13CCkctXbd8w
- sem marca d'água, 720p, voz Google acelerada 25% (atempo). Trilhas e fotos de exemplo passam pelo n8n
  (/…-arquivo?id=trilha-elegante / exemplo-…), pois o catbox derruba downloads da nuvem. Vozes e .ass no Redis 1 dia.
- testes ok: hambúrguer fotos enviadas vertical (78 s de fluxo, mas vídeo 48 s antes do atempo) e apartamento
  quadrado 15 s (71 s, vídeo 29,6 s). Links do vídeo valem 7 dias.

## V3 antiga (Rendi) — DESCARTADA
- conta Rendi criada (Google do cofre), chave em rendi_chave.txt (a de 93 letras). MAS a conta fica em "Sample mode"
  e o plano Free ($0) abre o Stripe pedindo CARTÃO -> parei (não pôr cartão).
- v3/monta_ffmpeg.js pronto e testado no ffmpeg local (provas: v3/local/sai_*): zoom/pan, xfade, voz do Google
  Tradutor (translate_tts, sem chave, 64 kbps -> duração = bytes*8/64000), trilha que abaixa com a voz, .ass com
  manchete/preço/legenda/cartão final, 2 saídas + capa num comando só. Reaproveitável em qualquer ffmpeg-na-nuvem.
- próximo: achar motor sem cartão (pesquisa em andamento) ou trocar a V3 por outra API.

## Cópias "textos novos" (30/10 ~09h, pedido da dona: melhorar os textos SEM mexer nas V1/V2/V3)
- V1b BYyH9SPeNrlrDFZF /webhook/anuncio-video-j2vb · V2b 57bJ6v4CkTujnp24 /webhook/anuncio-video-ssb ·
  V3b bnaGhuEuCMZr9GBq /webhook/anuncio-video-ffb. Gerar: python gera_copias_textos.py (lê fluxo_v1/v2/v3.json e
  troca só o nó do filme pelo v1b/v2b/v3b/*.js). Testadas ponta a ponta (hambúrguer 15 s): provas/tn_todos.jpg.
- Textos: manchete em CAIXA ALTA letra 900 com sombra, selo de preço maior e inclinado, legenda maior em caixa alta
  com destaque na palavra, degradê escuro atrás da legenda (V1b/V2b), cartão final maior; V3b usa Montserrat Black
  (fonte enviada junto ao ffmpeg) e legenda karaokê palavra a palavra.
- Marca d'água JSON2Video: só some com plano pago (US$ 49,95 pacote). Não há opção na API grátis; remover depois
  violaria os termos (grátis = não comercial). Shotstack: some só no ambiente v1 (produção, gasta créditos).
