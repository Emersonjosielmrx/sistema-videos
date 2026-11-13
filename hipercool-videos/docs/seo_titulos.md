# Títulos, descrição e tags — regras e estudo (15/10/2026)

## Regras (dono)
- Nunca o nome da obra original (título, descrição, hashtag, tag): risco de direitos autorais.
  - `seo._sem_obra` apaga o nome mesmo se o LLM escorregar.
  - Nomes proibidos em `config/fila.json` → `obras[].nomes_proibidos`.
- Título = provocação (sensual/curiosidade) + o máximo de palavras buscadas que tenham a ver com a história.
- Mesma lógica na descrição e nas tags.

## Banco de palavras (`config/seo_palavras.json`)
Feito com o autocompletar da busca do YouTube em pt-BR. É o mesmo que aparece na caixa de busca: endpoint público,
sem chave de API:

    https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&hl=pt-BR&gl=BR&q=<semente>

Sementes usadas: "manhwa ", "manhwa recap ", "resumo manhwa ", "manhwa ele ", "manhwa reencarnou ", "manhwa sistema ",
"manhwa romance ", "manhwa harem ", "manhwa rank ", "manhwa magia ", "manhwa rei ", "manhwa apocalipse ",
"ele reencarnou ", "ele despertou ", "ele foi humilhado " etc.

Mais frequentes (15/10): reencarnou, sistema, apocalipse (zumbi), harém, completo, humilhado, rank SSS, despertou,
magia, gênio, romance escolar, vilão, dragão, dinheiro infinito, bilionário, traído, overpower, voltou no tempo,
murim, cultivo, academia.

Padrões que o público digita: "ele foi humilhado mas…", "ele despertou o sistema de…", "ele reencarnou como…",
"ele foi traído pela namorada", "…e agora todas elas querem ele". Refazer a pesquisa a cada gênero novo da fila.

## Estudo: qual estilo de título rende mais
- O completo sai com 3 títulos:
  - `busca`: frase no padrão das buscas;
  - `provocacao`: provocação sensual + palavras;
  - `curiosidade`: pergunta/revelação + palavras.
- `seo.escolher_estilo` sorteia por Thompson sobre `workspace/titulos_estilos.json`. Sem dados = rodízio.
- O estilo usado fica em `workspace/postagens/<video>__<canal>.json` → `completo.estilo_titulo`; os outros 2
  títulos ficam no cache do SEO.
- FALTA: ler CTR/visualizações por vídeo (Studio > Analytics, pelo navegador) e chamar
  `seo.registrar_resultado(estilo, venceu)`.
  - Critério sugerido: CTR acima da mediana dos vídeos do mesmo canal nas primeiras 48 h.
- Quando o Studio liberar o "Testar e comparar" de título no canal, os 3 títulos podem entrar no teste junto com
  as capas.
