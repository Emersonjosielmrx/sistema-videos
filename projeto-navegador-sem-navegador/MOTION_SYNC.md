# Motion Sync no Flow (01/11/2026)

Pedido da dona: adicionar a função do vídeo https://youtu.be/OoMpgOJFTCw (Valeria Abtibool, "Motion control no Flow").
Ideia: **IMAGEM = APARÊNCIA** (rosto, cabelo, roupa, cenário) + **VÍDEO = SÓ MOVIMENTO** → a pessoa da imagem
repete os gestos do vídeo. Prompt mestre dela: `D:\tmp_motion\prompt.txt` (Google Doc 1SZXbRQhM94Qyvqo_rUZdTqaMdtqZ9EzlrH0l_gWQcZI).

## Como o Flow faz por dentro (JS capturado, capturas/flow_js_s1.js)
- Modo `EDIT_VIDEO` (vídeo base + `referenceImages`), modelo `abra_edit` / `abra_edit_360p` (grupo "abra" = Omni Flash).
  Aparece no catálogo ao vivo (HTrJv) da fabiovideoseducativos em 01/11.
- Ferramenta do agente: `generate_video_edit_video` (recebe `video_media_id` com papel "base").
- Upload de vídeo: Scotty retomável em `/upload/v1/flow/upload/video/<projeto>`; Xsrf = o `at`; sem reCAPTCHA;
  corte no servidor com `x-trim-start` / `x-trim-end` (ms). Erro 55 = vídeo longo demais.
- Erro 60 = "Editing uploaded videos isn't available in your region" (pode bloquear por região).

## O que foi feito
- `services/veo_flow/flow_http.py` → `FlowHTTP.subir_video(caminho, corte=None)`.
- `services/veo_flow/flow_gerar.py` → `FlowGerador.motion(imagem, video_base, saida, prompt="", formato, modelo="Omni Flash", max_s=10)`
  + `MOTION_PROMPT` (prompt interno padrão dela, em inglês) + comando:
  `python -m services.veo_flow.flow_gerar <conta> motion "instruções extras" saida.mp4 --imagem pessoa.jpg --video mov.mp4`
- Teste: `D:\tmp_motion\teste_motion.py` (log em `D:\tmp_motion\teste\log.txt`).

## Testes (fabiovideoseducativos, 01/11) — falha não cobra crédito
- 1 (prompt longo, vídeo 7,9 s com áudio): agente chamou certo (abra_edit, video :base) → servidor FAILED código 13.
- 2A (prompt curto, mesmo vídeo): **PUBLIC_ERROR_SPEECH_EDIT / SPEECH_EDIT_BLOCKED** → o ÁUDIO do vídeo base bloqueia.
- 2B (corte 5 s no servidor): FAILED 13.
- Correção: motion() agora sobe o vídeo base SEM ÁUDIO (ffmpeg -an, corte max_s local). Status de falha lido pelo
  iFxMud (`FlowHTTP.falha_geracao`) — o baixar para na hora em vez de esperar 15 min.
- 3 (vídeo mudo: C prompt curto, D motion() completo): os dois FAILED 13.
- 4: **E = edição simples SEM referência no vídeo mudo do rapaz → OK** (edit_E.mp4, chapéu vermelho, 8 s, 720x1280,
  20 créditos). F = vídeo parado (zoompan de foto) → FAILED. Conclusão: editar vídeo enviado funciona; o que falha é
  a imagem de referência / troca de pessoa. Saída é 720p → precisa upscale p/ 1080p (regra da dona).
- 5: G = referência de objeto (chapéu gerado no Flow, id direto); H = troca de pessoa com id gerado direto
  → **OS DOIS OK** (edit_G.mp4 chapéu de palha; edit_H.mp4 = MOTION SYNC: a ruiva fictícia repete gesto/timing do
  rapaz, rosto/cabelo/suéter da ref). Prompt curto natural + ref gerada no Flow. 950 créditos depois (20 por vídeo).
- 6: I = ref ENVIADA por upload + prompt do H (fundo da ref) → **OK** (edit_I.mp4: ruiva na cozinha
  da foto, expressões do vídeo). 1ª tentativa deu UNUSUAL_ACTIVITY (reCAPTCHA após muitos testes); repetir resolveu.
- Finais 1–3 pelo CLI (vídeo enviado na hora, prompt curto / com descrição): FAILED.
- 7: J = vídeo e3e7691f (enviado ~10 min antes, tinha falhado) + o prompt GENÉRICO → **OK**.
- **CAUSA REAL: pedir logo após enviar o vídeo** (o Flow ainda processa → "state: FAILED" código 13, sem cobrar).
  Todos os que passaram usaram vídeo enviado minutos antes. O prompt não era o problema.
- Correção: motion() espera o link /video/ existir e `MOTION_ESPERA_S` (120 s, env FLOW_MOTION_ESPERA_S) desde o
  envio; vídeo base mudo (`-an`, copia sem recodificar se ≤ max_s); upscale 1080 (`_para_1080`).
- **Final 4 pelo CLI → OK**: `D:\tmp_motion\teste\FINAL_motion.mp4` 1080x1920, 8,04 s, com áudio. 20 créditos.

- Vídeo REAL do dono (`postador-de-videos\remotion\trabalhos\followupia_ia_20261029_182908\public\dono_1.mp4`,
  8,1 s, sem áudio): K = o dono de terno numa usina solar (imagem do Nano Banana a partir de um quadro dele) e
  L = a ruiva com os gestos dele → **os dois OK** 1080x1920 (`D:\tmp_motion\teste\dono\`). 850 créditos depois.

- **Dona 01/11 ~21h: o vídeo base tem que ser GRAVAÇÃO REAL dele (dono_1 é Veo, não serve) e o final tem que sair
  em PORTUGUÊS.** Plano: vídeo real com voz → corte ≤ 10 s → motion() (sobe mudo) → recolocar o ÁUDIO ORIGINAL dele
  (a boca segue o movimento da fala original, então bate). Buscando vídeos reais no Google Fotos das contas dele
  (`buscar_fotos_google.py --videos`, destino `D:\tmp_motion\fotos_dono`, log `D:\tmp_motion\log_fotos.txt`).

- **Vídeo REAL da Advance** (`fluxo-anuncio-api\videos_prontos\EDITOR_Advance_Solar_video_real\1_ORIGINAL.mp4`,
  10 s): troca da pessoa mantendo a rua + fala ORIGINAL em PT recolocada → `D:\tmp_motion\advance\
  ADVANCE_pessoa_trocada_PT.mp4` (1080x1920). Dona aprovou ("ficaram boas, deu certo"). Saiu meio a meio (rosto/cabelo
  novos, corpo/barba do original); variações M (prompt forte) e N (mulher) em `teste_advance2.py`: na fabio deram
  UNUSUAL_ACTIVITY, na mundosolar o Chrome deu timeout — não rodaram.
- 01/11: arquivos de cookie velhos (não confirmado logout) em emerson2030, emersonjosiel649, inovaremanhwaverseesp,
  emersonjosiel2027, emersoncunha, jogoscomia2. Com abra_edit e crédito: fabio (830), mundosolar e canalalucinaai (50).

## Status / falta
- [x] Teste real passou (final 4, 01/11 ~20h).
- [ ] Copiar para `dist/nsn_worker` e `maquina_remota.py instalar-nsn <maq>` (notebooks/PC2) depois do teste.
- [ ] Ligar numa linha de produção (ex.: Shorts de dança/trend com a mascote) — só quando a dona escolher.
