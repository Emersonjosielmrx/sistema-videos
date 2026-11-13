# Fluxos n8n centralizados + fluxos novos sem chave — andamento (30/10/2026)

Pedido do dono (30/10): analisar `D:\hipercool-materiais\fluxo-anuncio-api`, juntar num lugar só os fluxos n8n
espalhados pelo disco, criar mais fluxos baseados nos criadores do PC (Veo, imagem, vídeo, postadores, navegador sem
navegador) sem instalar nada na VPS. Depois (30/10 13:10): **nada pago e nada que precise de chave** — só grátis sem
chave, mesmo com resultado inferior. Não perguntar nada; fazer tudo.

## Feito
- Varredura do D:\ inteiro (125 arquivos de fluxo, 115 fluxos distintos) → `biblioteca\<assunto>\` (78 atuais +
  37 versões antigas em `_versoes`), `INDICE.md`, `indice.json`. Originais NÃO mexidos. Refazer:
  `python ferramentas\centraliza.py` (varre tudo, ~20 min neste PC) ou `--manifesto <arquivo>`.
- n8n6 tem 1.932 fluxos (50 ativos); credenciais: Redis `TgnZ028ccZYrorGM` (redis2), roteador 20128 etc.
- Testes de serviços grátis sem chave (`_testes\testa_gratis.py`, resultado em `_testes\resultado_gratis.json`):
  - imagem: Hugging Face FLUX.1-schnell (Space `black-forest-labs/FLUX.1-schnell`, rota `/infer`) ok 2-4 s, sem marca,
    MAS cota anônima do ZeroGPU por IP acaba rápido (2ª imagem já deu `event: error`). Reserva: Pollinations
    `image.pollinations.ai/prompt/...` ok ~7 s, sem chave, com selo "pollinations.ai" no canto (não cortar o selo).
  - texto: Pollinations `text.pollinations.ai/<pergunta>?model=openai` ok (só `openai-fast`), 1 resposta/30 s por IP.
  - voz: Google Tradutor ok; Edge-TTS neural (Space `innoai/Edge-TTS-Text-to-Speech`, rota `/tts_interface`,
    vozes pt-BR Francisca/Antonio/Thalita).
  - vídeo IA (tipo Veo, inferior): `Lightricks/ltx-video-distilled` `/text_to_video` ok em 11 s (3 s, 512x704, bom).
    Wan 2.2 (`zerogpu-aoti/wan2-2-fp8da-aoti-faster`) deu erro no teste (cota ou formato da foto).
  - montagem sem chave: Space `Tim13ekd/video-ffmpeg` `/generate_slideshow_with_audio` (fotos + áudio + legenda).
  - dados públicos: YouTube RSS (15 vídeos) e youtubei/browse sem login, TikTok oEmbed, wsrv.nl — ok.

- Limites do n8n6 descobertos (fluxo de teste `G3wzPVn34KF7zReF`, /webhook/gratis-teste-recursos): o Code NÃO tem
  WebSocket, fetch, nem módulos (só `crypto` e `moment`), e para em **60 s** → espera longa só em nó HTTP.
- Voz neural sem chave pelo Bing Tradutor (página pública → tfettts), testada do PC e do n8n6. Só as vozes
  Multilingual aprovadas (Thalita padrão, Andrew, Brian, Emma); Antonio e Francisca PROIBIDAS (regra da dona,
  `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md` §4b).
- Montagem sem chave: Space `Tim13ekd/video-ffmpeg` funciona (7 s), MAS só sai 1280x720 deitado e só aceita
  arquivo enviado por upload (`/gradio_api/upload`), não link.

### Fluxos novos no ar no n8n6 (gerador em `novos\<pasta>\gera.py`, JSON ao lado; importar com
`python ferramentas\n8n_servidor.py importa <json>`)
| Fluxo | id | Endereço | Teste |
|---|---|---|---|
| 🎙️ Narrador grátis | 3FuIs8661Kb24vre | /webhook/gratis-voz | ok: 9 s de voz Andrew em 7 s |
| 🖼️ Imagens grátis | RpeQyhTQOQDoUPqf | /webhook/gratis-imagem | ok: 2 FLUX em 35 s, prompt melhorado |
| 🎥 Clipes IA grátis (LTX) | XNadVMuv6DDWaTMX | /webhook/gratis-clipe | ok: 3 s 480x832 em 22 s; 01/11 resposta imediata + consulta de andamento; foto→vídeo ok; sem cota na VPS a página gera pelo navegador |
| 🧪 Teste de recursos | G3wzPVn34KF7zReF | /webhook/gratis-teste-recursos | só diagnóstico |

## Em andamento / próximos
- 🎬 Fábrica de vídeos grátis (tema → roteiro → imagens → voz → vídeo; 16:9 na nuvem, 9:16 no navegador).
- 📊 Radar de canais (YouTube RSS/browse, TikTok oEmbed), 🌉 Ponte PC (Flow/Veo/ffmpeg/postadores do PC).
