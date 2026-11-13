# Flow (Nano Banana) nos geradores de imagem dos projetos

Pedido do dono (22/10/2026 23:10): "nos lugares dos geradores de imagem coloque esse sistema para gerar capas, imagens
que precisa nos geradores de vídeo etc e teste para garantir que funciona".

Regra: o Flow entra como **1ª opção**. O gerador que já existia continua como reserva, então se o Flow falhar
(recusa por política, conta ocupada, PC sem as contas do Flow, como o PC2) o projeto segue igual a antes.

## Frentes (status gravado na hora)

| # | Onde | Usado para | Status |
|---|---|---|---|
| 1 | `D:\hipercool-materiais\comum\imagem_reserva.py` (cópias "# COMUM" nos projetos) | capas IA do hipercool (`capa_ia`) e do historias (`capa_ia_historias`) | feito 22/10 23:35: Flow = 1º da lista `MODELOS` (`flow/nano-banana-2.1`, via `cliente.py`), subido pelo `recursos.py` (hipercool, historias, recapd). Testado com o Python do hipercool: capa de casal 16:9 1376x768 em 128 s; pedido ousado (camisola no colo) NÃO foi recusado (saiu comportado, robe cobrindo) |
| 2 | `D:\historias-em-frames\bin\image_generator.py` / `omniroute_image.py` | cenas das histórias + miniatura | feito 22/10 23:45: gateway continua 1º (testado: OK em 12 s; são ~30 imagens por vídeo e o Flow leva 1-2 min); o Flow entra quando o gateway falha ou esgota, ANTES do Pollinations; com a cota do gateway esgotada o vídeo PARAVA por horas e agora segue (o `image_generator` também não aborta no cooldown se o Flow está disponível). Testado com o gateway forçado a falhar: imagem pelo Flow, `ULTIMO_RESET_S` = 0 |
| 3 | `D:\manhwa-react\mr\imagem.py` | arte dos canais (perfil/banner, com cache) | feito 22/10 23:50: Flow 1º, gateway reserva. Testado pelo próprio `mr.imagem.gerar` (1:1, 108 s) |
| 4 | `D:\veo\beta\pos_producao\omniroute_image.py` | fundo de CTA/propaganda do Veo | feito 23/10 00:35: gateway continua 1º; Flow antes do Pollinations (o pior); health-check (`premium_only`) não usa o Flow. Testado com o gateway forçado a falhar: fonte "flow", 95 s |

## Notebooks (X200MA/Acer) — 23/10

Antes: NADA do Flow rodava nos notebooks. O caminho deles existia só no `flow_bot.generate()` (usado pelo
`api_server`), e a produção usa o `gera_auto.py`/`gera_imagem.py` com o Chrome do PC1.
Agora, conta ativada pro Flow nos notebooks (`netbooks_logins.json` → `_flow`; das contas do Veo: inovaremanhwabr e
inovaremanhwaverseesp) roda primeiro lá (`maquina_remota.tentativas`: um ocupado/fora = o outro; depois o PC1):
- imagem: `gera_imagem._gerar_na_conta` → testado: texto pelo X200MA (768x1376, 0 crédito) e foto de referência pelo
  Acer (X200MA ocupado postando). Conta sem projeto: cria "Novo projeto" e salva.
- vídeo: `gera_auto._gerar_nos_notebooks` → só troca de máquina em erro de conexão/login (crédito já gasto não repete).
- Foto de referência: passar o caminho DESTE PC (o Playwright transfere o arquivo pela conexão CDP); o caminho no
  disco do notebook quebrava ("I couldn't find the attached reference image").
- `FLOW_NOTEBOOKS=0` desliga.

## Testes e achados (22-23/10)

- Produção já usando: 23/10 00:21 uma capa de anime 9:16 (recapd ou hipercool) saiu pelo Flow via `imagem_reserva`.
- "The agent is experiencing high demand" (seebotsia): agora aperta "Tentar novamente" até 3x; espera máx. 150 s por
  conta; prova de cada falha em `logs\falhas\`.
- Painel de ajustes que às vezes não abre: não derruba mais (o pedido já cita modelo/formato).
- Tempo real por imagem: 95–140 s com abertura/fechamento do Chrome; 0 crédito em todas.
- PC1 com pouca memória à noite (sessões do Claude ~7 GB, VS Code ~4 GB): 23/10 00:12 o ffmpeg do MS Energy caiu
  ("Cannot allocate memory") e o Whisper também. MS Energy agora repete a montagem 1x depois de 90 s; o clipe
  perdido foi resgatado (`shorts_veo\ms_energy_solar_20261023_000340`).
| 5 | `D:\ms-energy\bin\carrossel_ms.py` | ilustração do carrossel | feito 22/10 |
| — | recapd | fora da lista do dono | não mexer |
| — | `postador\bin\omniroute_image.py`, `hipercool\bin\scene-images.py` | sem quem chame (procurado 22/10) | não mexer |
