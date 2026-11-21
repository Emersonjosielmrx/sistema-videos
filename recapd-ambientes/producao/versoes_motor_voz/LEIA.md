# Versões do motor de voz (dona 20/11: "não descartar o motor antigo; versionar; se não der certo, voltar")

| Versão | O que é | Arquivos |
|---|---|---|
| **v1_antigo_RVC_kitten_p3_18nov** | Motor ANTERIOR ao Fish: Kitten 2 + RVC na GPU (kitten_tudo), p3 (Kokoro/Francisca/Piper + técnicas: curva do locutor, climas, +10% de fala, fim de frase do perfil, humanizar) nos PCs. Commit `1370e236` do D:\github_sistema (18/11 10:01). | anime_tts, anime_segments, voz_clonada_nuvem, narracao_curva, climas_voz, lote_shorts_kaggle, anime_auto |
| **v2_fish_20nov** | Fish (Kaggle + site) com: referência animada+rápida, sub-vozes por frase, ritmo pelo conteúdo, aceleração do gol + desfecho, S do "respeito", kkk fora, roteiro com duplo sentido/marcas/vocabulário, gatilho pela imagem. | + fish_nuvem, gatilho_visual, anime_script, duplo_sentido.json |

| **v0a_antes_do_p3_rvc_edge_kokoro_16nov** | O motor de ANTES do p3 (commit `af0a1ccb`, 16/11): voz clonada RVC em cima do Edge Francisca / Kokoro (p1), sem Piper e sem Kitten. É "o outro antes do Kitten" que a dona citou em 20/11. | mesmos 7 arquivos |
| **v0b_p3_kokoro_francisca_piper_rvc_18nov** | p3 (commit `e0ac939b`, 18/11 09:32): revezamento Kokoro/Francisca/Piper + RVC + técnicas, antes do Kitten virar padrão. | mesmos 7 arquivos |
| **v3_fish_A_homogeneo_20nov** | **A versão "A" que a dona achou a MELHOR (20/11 noite, ouvindo o Virjão)**: "melhor que a do Kitten, mas não muito melhor — pouco melhor". Fish com a sub-voz SEMPRE junto da referência normal (âncora), lento com piso 0,92, falha sem tom fora do Mike, S do respeito pela posição no texto, gol no meio da sequência, pausa antes da pergunta. Testada no `COMPARACAO_A_novo_B_desligado_C_motor_antigo`. D (Fish+RVC) ficou "praticamente igual ao desligado, só que inferior". | + fish_nuvem, gatilho_visual, anime_script, duplo_sentido.json, motor_voz.json |

Comparação 20/11 (mesmo roteiro do gol, `amostras_voz\ACELERACAO_DO_GOL_e_NARRACAO_CONTINUA\COMPARACAO_...`):
A > C (Kitten) por pouco; B ≈ D; E (Fish+RVC+3 passos) — ainda não avaliado. Kitten: "muito igual em todas as
frases"; Fish: "bom, mas instável — engrossa/afina demais".

## Voltar ao motor antigo SEM perder as melhorias de outros chats (recomendado)
`config/motor_voz.json` → `"motor": "antigo"` e rodar `colab\montar_pacote.py --codigo`. O código atual já tem o caminho
antigo inteiro (o Fish só vem na frente); a chave desliga só o Fish. O roteiro novo (duplo sentido, marcas
registradas, vocabulário) continua valendo — dá pra "melhorar o antigo com o que aprendemos agora".
Por variável: `MOTOR_VOZ=antigo`.

## Voltar os ARQUIVOS da v1 (só se o código atual quebrar)
Copiar os arquivos de v1 por cima de bin\ — ATENÇÃO: desfaz o que outros chats mudaram nesses arquivos desde 18/11.
