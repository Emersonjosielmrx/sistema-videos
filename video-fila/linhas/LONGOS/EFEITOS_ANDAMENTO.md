# Pedido da dona 28/10 04:05 — abertura/resumo, mascote com voz, efeitos (andamento retomável)

Pedido: (1) ambientação + explicação inicial + RESUMO no começo ("hoje vamos ver nosso prota X... expulso da guilda,
traído pela namorada... depois ganhou poderes e virou um cara foda" com as imagens desses momentos + gancho);
(2) mascote aparecendo e FALANDO (nova: waifu bonita tipo Crunchyroll, mais sexy); (3) efeitos como os do hipercool
(impacto, 2.5D, overlays, transições queimando/água/raio, movimento de câmera dentro da imagem, parecer anime).
REGRA: em camadas — primeiro o que custa pouco tempo e dá mais impacto; medir quanto cada efeito acrescenta
(% e horas num longo de ~4 h de render) e LISTAR tudo pra dona decidir.

Assumido pela claude-36 em 28/10 ~09h (claude-fe caiu nos erros 502/429 e não fez nada).

## Frentes
- [ ] F1 mapear o que o longo já faz (código do render deitado, efeitos ligados/desligados)
- [ ] F2 mapear efeitos do hipercool que existem e dá pra portar
- [ ] F3 medir custo de cada efeito (trecho curto real, s de render por min de vídeo)
- [ ] F4 abertura com resumo (texto + imagens dos momentos) — implementar
- [ ] F5 mascote falando — ver o que existe (mascote_overlay, mascote_mov)
- [ ] F6 lista final pra dona (tabela custo x impacto)

## Achados
- F1: o longo deitado liga SÓ ANIME_FX_MOV (fx_clips._movimento: zoom-in/pan/zoom-out 12% + tremida/clarão na
  frase de impacto), descaracterizador (crop 10%, cor), xfade entre falas (concat_with_xfade), SFX por palavra,
  gancho escrito, capítulos, mascote PARADA (overlay em 8 momentos), CTA falado. Nada de overlays/partículas/
  divisórias/grade de cor. Assets prontos e sem uso no longo: assets\overlays (128: sparks, speedlines, rain,
  petals, fx_anger...), _divisorias/dividers (fogo/raio/glitch), hyperframes, mascote_mov (14 .mov animados).
- [CERTEZA] NVENC não é usado em lugar nenhum (grep nvenc/cuda/hwaccel em bin/colab = 0). No Kaggle a GPU só
  serve ao Applio; todo clipe é libx264 -preset fast na CPU (4 núcleos). Trocar o encoder dos clipes por
  h264_nvenc deve baratear o render e abrir espaço pros efeitos — TESTAR no Kaggle quando a cota voltar.
- F4 FEITO (28/10): anime-pipeline._resumo_longo + anime_segments._inicios (ANIME_RESUMO_N: resumo pode voltar no
  tempo; a história recomeça do 0) + config/longo.json "resumo". Gemini 3.8 direto (o Gemini 3 padrão copiou
  frases e esqueceu o prota). Travas: imagens espalhadas (≤1 no 1º décimo, metade na 2ª metade), nada nos últimos
  12% (spoiler — a IA usou o desfecho mesmo proibido). Sem tempos = proporção do texto. resumo.json na pasta.
  Testado sem render em RA4H e BTG0 (bench\teste_resumo.py, bench\resumo_*.json): 6 frases concretas, ~45 s.
  FALTA: ver num render real (quando a cota do Kaggle voltar) e subir o pacote (montar_pacote.py --codigo).
- F5 FEITO (28/10): mascote FALA os 3 CTAs com voz própria (edge Francisca +6%/+22Hz, config mascote.fala/voz/tom;
  anime_segments._falas_mascote + anime-pipeline._marcar_falas_mascote) e fica na tela a fala inteira
  (mascote_overlay: segura o quadro 1,33 s — o último quadro do MOV é ela transparente, 1º teste saiu apagada).
  Prova: bench\saida\painel_mascote.jpg + mascote_falando.mp4. Visual novo (waifu) = dona aprovar desenho.
- [CUSTO ESCONDIDO] _mascote_longo recodifica o longo INTEIRO (veryfast crf19) só pra 8–11 aparições (~15 min
  estimados num longo de 75 min). Mover pro clipe = economia.
- PRÓXIMO dos efeitos (quando a dona escolher a camada): NÃO usar elemental_transitions.apply no longo (recodifica
  o vídeo inteiro a cada 6 overlays = ~17 passadas num longo). Fazer: pré-converter 1x os MOVs ProRes 1080x1920
  12-bit pra versões deitadas 1280x720 leves com alfa (cache), escolher com pick_transitions e entrar no próprio
  clipe (fx_clips.build_clip_from_video, como a variante 8 do bench). Cada efeito = alavanca DESLIGADA no
  longo.json, pro melhorador testar A/B. Câmera forte = mudar zz de 0,12 pra 0,25 em _movimento (custo ~0).
- F3 REFEITO (CPU real, ultrafast, fonte AV1 da MlgX, s de CPU por min de vídeo): sem mov 66,8 | ATUAL 71,3 |
  câmera forte 69,6 | impacto todo 78,0 | aberração 108,5 | partículas 148–157 | paralaxe 166,5 | grade 135,4 |
  bloom 190,9 | mascote no clipe 196,9 | elemental 205,9. MESMA fonte em H.264: sem mov 39,6 | ATUAL 48,9
  => AV1 custa +46% na montagem. F6 lista em EFEITOS_LISTA_DONA.md.
- F4/F5 PROVADOS no pipeline real (bench\render_teste, 70 frases): resumo 6 frases com cortes 76/676/1571/2799/3430
  e a história recomeçando em 0; mascote fala as frases 10/41/78.
- !! OS NÚMEROS ABAIXO NÃO VALEM: com -v error o ffmpeg não imprime "bench: utime" e o script caiu calado no
  relógio de parede (PC1 em 100%). Refeito com -v info + ultrafast (igual ao clipe real) + teste AV1 x H.264:
  resultados_av1.json / resultados_h264.json.
- F3 (1ª tentativa, bench\bench_efeitos.py, tempo de CPU do ffmpeg — o relógio de parede não serve com o PC1 em 100%;
  4 clipes de 4,7 s da fonte MlgX, 1280x720 libx264 fast). Segundos de CPU por minuto de vídeo, montagem dos clipes:
  sem movimento 46,8 | ATUAL 63,4 | impacto em todo clipe 75,1 | câmera forte 71,7 | paralaxe displace 83,8 |
  mascote no clipe 84,8 | aberração cromática 92,9 | partículas sparks 109,8 / speedlines 115,6 / chuva 117,5 |
  elemental fogo 138,8 | grade+vinheta+grão 141,0 | bloom 143,2.
  Horas num longo de 75 min (montagem sequencial, ~2,5 núcleos úteis no Kaggle): h ≈ Δ × 75 / 2,5 / 3600.
- pipeline.log dos longos prontos não fica guardado (trabalhador apaga a pasta) — tempo por etapa medido no PC1.
