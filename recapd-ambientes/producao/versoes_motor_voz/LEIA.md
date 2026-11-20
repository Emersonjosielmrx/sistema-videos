# Versões do motor de voz (dona 20/11: "não descartar o motor antigo; versionar; se não der certo, voltar")

| Versão | O que é | Arquivos |
|---|---|---|
| **v1_antigo_RVC_kitten_p3_18nov** | Motor ANTERIOR ao Fish: Kitten 2 + RVC na GPU (kitten_tudo), p3 (Kokoro/Francisca/Piper + técnicas: curva do locutor, climas, +10% de fala, fim de frase do perfil, humanizar) nos PCs. Commit `1370e236` do D:\github_sistema (18/11 10:01). | anime_tts, anime_segments, voz_clonada_nuvem, narracao_curva, climas_voz, lote_shorts_kaggle, anime_auto |
| **v2_fish_20nov** | Fish (Kaggle + site) com: referência animada+rápida, sub-vozes por frase, ritmo pelo conteúdo, aceleração do gol + desfecho, S do "respeito", kkk fora, roteiro com duplo sentido/marcas/vocabulário, gatilho pela imagem. | + fish_nuvem, gatilho_visual, anime_script, duplo_sentido.json |

## Voltar ao motor antigo SEM perder as melhorias de outros chats (recomendado)
`config/motor_voz.json` → `"motor": "antigo"` e rodar `colab\montar_pacote.py --codigo`. O código atual já tem o caminho
antigo inteiro (o Fish só vem na frente); a chave desliga só o Fish. O roteiro novo (duplo sentido, marcas
registradas, vocabulário) continua valendo — dá pra "melhorar o antigo com o que aprendemos agora".
Por variável: `MOTOR_VOZ=antigo`.

## Voltar os ARQUIVOS da v1 (só se o código atual quebrar)
Copiar os arquivos de v1 por cima de bin\ — ATENÇÃO: desfaz o que outros chats mudaram nesses arquivos desde 18/11.
