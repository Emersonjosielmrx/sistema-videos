# Prompt para o próximo agente (30/10/2026)

## Prompt

```
Continue o trabalho de fluxos n8n grátis em D:\hipercool-materiais\fluxos-n8n. Leia antes: PROGRESSO.md, INDICE.md e
este arquivo. Responda em português do Brasil, direto, sem perguntar nada à dona (ela pediu para fazer tudo).

O QUE JÁ EXISTE
- Biblioteca central: biblioteca\<assunto>\ (115 fluxos achados no D:\, 78 atuais + versões em _versoes), INDICE.md e
  indice.json; refazer com: python ferramentas\centraliza.py (varre o D:\ ~20 min) ou --manifesto <arquivo>.
- servidor-n8n6\: cópia dos 50 fluxos ATIVOS do n8n6 (python ferramentas\n8n_servidor.py copia-ativos).
- Ferramenta da API: ferramentas\n8n_servidor.py (lista | copia-ativos | importa <json> | get | execucoes | execucao).
- Fluxos novos (gerador em novos\<pasta>\gera.py + .js; JSON ao lado; importar com n8n_servidor.py importa):
  🎙️ Narrador grátis /webhook/gratis-voz (3FuIs8661Kb24vre) — ok
  🖼️ Imagens grátis /webhook/gratis-imagem (RpeQyhTQOQDoUPqf) — ok
  🎥 Clipes IA LTX /webhook/gratis-clipe (XNadVMuv6DDWaTMX) — texto→vídeo e foto→vídeo ok (01/11). O POST responde
     NA HORA com {id, status} e a página consulta /webhook/gratis-clipe-status?id= (antes a conexão ficava aberta até
     3 min e o navegador derrubava: "Failed to fetch", 499 no traefik). Cota do HF é por IP: quando a da VPS acaba,
     a página gera direto do navegador (CORS liberado) — o clipe fica só na página (blob), não no Redis.
     Testes: _testes\testa_clipe.py (API) e _testes\testa_pagina_clipe.py (Chrome sem janela + print).
  🎬 Fábrica de vídeos /webhook/gratis-video (PJ3YVnULgH0IMoBd) — 16:9 ok ponta a ponta (108 s); 9:16 montado no
     navegador (página -ver) ainda NÃO testado em navegador de verdade
  📊 Radar dos canais /webhook/gratis-radar (PReaUwJnCXImRHTN) — ok, 21 canais, todo dia 7h20
  🌉 Ponte PC /webhook/ponte-pc (Fyw9qx5jQ2Edw0MG) + ponte-pc\trabalhador.py — saude e montar_video testados ok
  🧪 Teste de recursos (G3wzPVn34KF7zReF) — só diagnóstico
- Testes e amostras: _testes\ (chama.py, acompanha_video.py, testa_ponte.py, transcreve.py com o Whisper local).

FALTA (em ordem)
1. Ponte/montar_video: o MP4 saiu yuvj444p (High 4:4:4) — pôr "-pix_fmt yuv420p" na saída do ffmpeg em
   ponte-pc\trabalhador.py e retestar (python _testes\testa_ponte.py pede montar_video <job>; depois
   python ponte-pc\trabalhador.py --uma-vez). Conferir quadros e a legenda .ass.
2. Fábrica: reimportada com legenda em trechos de ~4 palavras (sobe_montador.js), sufixo anti-colagem nas imagens e
   seed aleatória no texto — rodar um vídeo 16:9 novo e conferir quadros; testar o modo 9:16 (navegador) abrindo
   /webhook/gratis-video-ver?id=<job> no painel de navegador e apertando "Montar o vídeo".
3. Ligar a ponte na fábrica: opção "montar no PC" (pede montar_video à ponte e a página mostra o vídeo do PC).
4. Testar imagem_flow pela ponte (abre Chrome do Flow no PC; só com RAM livre > 3 GB).
5. (FEITO 01/11) Clipes: foto→vídeo confirmado pela página (plano B do navegador).
6. Desligar (não apagar) o fluxo 🧪 de teste se não for mais usar; atualizar PROGRESSO.md, INDICE.md (rodar
   centraliza.py) e incluir os fluxos novos na biblioteca.
7. Vídeo de Anúncio V4 sem chave (fluxo-anuncio-api): trocar agentes com credencial por chamadas ao Pollinations
   (Code com o mesmo nome do nó, 1 chamada a cada 31 s) e a montagem por montador grátis/navegador/ponte.

COMO TESTAR: python _testes\chama.py POST <caminho> @arquivo.json [saida]; acompanhar vídeo com
python _testes\acompanha_video.py <job>. Ver execução com falha: n8n_servidor.py execucoes <id_fluxo> e execucao <id>.
```

## Restrições (o que não fazer)

```
- NADA pago e NADA que precise de chave de API (dona, 30/10): só serviços grátis sem chave — Pollinations (texto
  1 resposta/30 s por IP, reasoning_effort "low", sem response_format; imagem com selo), Hugging Face Spaces públicos
  (FLUX schnell, LTX-Video, Tim13ekd/video-ffmpeg; cota anônima por IP), Bing Tradutor (voz), Google Tradutor (voz
  reserva), Wikipédia (fatos), YouTube RSS/browse público, wsrv.nl. Nada de JSON2Video, Shotstack, Very Good FFmpeg,
  Cloudflare, Gemini API, ElevenLabs nos fluxos novos.
- NADA para instalar na VPS do n8n (nem nó da comunidade, nem Execute Command, nem ffmpeg lá).
- Limites do Code no n8n6: para em 60 s; sem WebSocket/fetch/módulos (só crypto e moment); o httpRequest do Code
  ESTRAGA binário no corpo (manda como UTF-8) — upload de arquivo só pelo nó HTTP multipart (n8nlib.http_envia_arquivo).
- Vozes PROIBIDAS em qualquer projeto: pt-BR-AntonioNeural e pt-BR-FranciscaNeural (só Multilingual aprovadas:
  Thalita, Andrew, Brian, Emma). Não cortar o selo do Pollinations nem marca d'água de serviço grátis.
- NUNCA postar nada (YouTube/TikTok/Instagram): a ponte só guarda na caixa de saída para aprovação; postagem real só
  com OK da dona. Google/YouTube só pelo navegador, nunca criar chave no Google Cloud. Vídeo do Veo nunca direto no YouTube.
- Não mexer nos fluxos de produção do n8n6 (os 50 ativos) nem nos originais espalhados pelo disco; a biblioteca é cópia.
- Não editar D:\projeto-navegador-sem-navegador (outra sessão mexe), PC2, Atlas, Lucrativa, MS Energy.
- Não apagar nada (fluxo, arquivo, chave do Redis): desligar em vez de apagar. Não copiar chaves/tokens para chat ou
  documento (o token da ponte fica só em ponte-pc\config.json).
- Disco D com pouco espaço (~2 GB livres em 30/10 15h): nada de baixar coisa grande; testes em D:, nunca no C.
- RAM: abaixo de ~3 GB livre, otimizar antes (Wise Memory Optimizer, regra do CLAUDE.md); não matar processos de outras
  sessões nem produção (pythonw).
- Não gerar vídeo com Veo/Flow à toa (gasta conta/crédito); imagem_flow é 0 crédito mas abre Chrome no PC.
```
