# Vídeo longo 16:9 — estado atual e plano da biblioteca de efeitos

Pedido do dono (14/10, depois de ver o cap 1 em 16:9): "gostei do longo, só que repete muito aquele efeito de
trocar para o lado como páginas; temos que desenvolver para o longo uma biblioteca de efeitos grande como a
do outro [o vertical], pra termos variedade, tendo a mesma base do outro, mas com mais variedade, já que podemos
explorar os efeitos laterais".

## O que existe hoje (`bin/hiper-longo.py`)

Cada fala do roteiro vira um **momento** (duração = voz + 0,25 s). Um momento = **layout** + **transição de
entrada** + legenda desenhada no quadro. Tudo em OpenCV -> Quick Sync. Só usa cache (zero IA nova).

| Layout | O que mostra | Quando |
|---|---|---|
| `tira` | painel no meio, vizinhos apagados nas laterais (história andando pro lado) | padrão |
| `cheio` | painel na largura toda, a câmera desce por ele (ou fica no meio, se baixo) | sorteio |
| `duo` | painel anterior apagado à esquerda + atual à direita | sorteio |
| `close` | painel à esquerda + o ROSTO dele grande à direita | reação, painel não sugestivo |
| `recorte` | painel à esquerda + personagem recortado subindo à direita | personagem com recorte limpo |

| Transição | Efeito |
|---|---|
| `desliza` | a tira anda pro lado (o "virar página" de antes) |
| `sobe` | o painel entra de baixo |
| `funde` | dissolve do quadro anterior |
| `corte` | corte seco com flash branco |

Regras: nunca a mesma transição 3x seguidas; layout comum não repete 3x; `close`/`recorte` no máx. 1 a cada
3 momentos. Painel alto desce devagar dentro do quadro. Fundo = o próprio painel borrado e escuro.

## Plano da biblioteca (próximos capítulos — ir ligando e medindo)

Base igual ao vertical (`fx_parallax`, `effects_engine`, `fx_acabamento`), adaptada ao espaço lateral:

1. **Parallax 2.5D em 16:9** — reaproveitar `fx_parallax._render_camadas` com canvas 1920x1080 (o personagem
   recortado anda sobre o painel com desfoque de profundidade). Hoje o 16:9 só tem o `recorte` estático subindo.
2. **Impacto / tensão** — `impacto` (salto + linhas de velocidade + tremor) e `tensao` (tremor leve) do
   vertical, disparados pelas mesmas palavras (`fx_detect.is_impact_panel / is_tension_panel`).
3. **Tríptico** — 3 painéis curtos seguidos lado a lado, o ativo aceso e os outros apagados (diálogo rápido).
4. **Tela dividida diagonal** — dois personagens em conversa (painel A e B), corte diagonal com borda branca.
5. **Zoom no balão** — punch-in no balão de fala (`censura_visual._mascara_baloes` já acha os balões).
6. **Mangá aberto** — dois painéis como páginas de um livro, com sombra no meio (para virar de capítulo).
7. **Flash de memória** — painel em sépia/preto e branco com vinheta quando a narração fala do passado
   (palavras: "lembra", "antes", "anos atrás", "passado").
8. **Overlays do vertical** (`effects_engine.get_event_package`: brilho, pétalas, faíscas, chuva) e **cor por
   clima** (`EffectsManager.clima`) nos layouts 16:9.
9. **SFX e gatilhos por palavra** do `fx_acabamento.planejar_sons` (hoje o 16:9 só tem voz + trilha).
10. **Legenda palavra a palavra** (Groq) como no vertical, em vez de frase inteira.
11. **Capítulo como "episódio"** — cartão de abertura animado (logo da obra + número) e cartão de fim com
    "próximo capítulo" (o vertical tem CTA; o longo não tem).

Ordem sugerida: 8 e 9 (baratos, já existem) -> 1 e 2 (maior ganho visual) -> 3, 4, 5 -> resto.
Medir a cada capítulo: tempo de render (cap 1 = 11 min na UHD 620) e a retenção no YouTube Studio.

## Postagem

A fila posta a compilação "caps 1 a N" em cada canal: a 1ª com 2 capítulos (`longo_primeiro`) e depois a cada 3
capítulos novos (`longo_a_cada`). Título/descrição/tags pelo agente de SEO (`bin/seo.py`), com a lista de
capítulos e minutos na descrição; capa no estilo sensual; playlist "<obra> — Maratona".
