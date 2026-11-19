# Artes de canal para aplicar (18/11)

Gerado por `D:\manhwa-react\canais_novos_18nov.py`. Folha de conferência: `canais\_NOVOS_18NOV.jpg`.
Cada pasta tem `perfil.png` (800x800), `banner.png` (2560x1440, texto na área segura), `marca_dagua.png` (150x150),
`descricao.txt`, `palavras_chave.txt` e `canal.md`.

Página pública conferida sem login em 18/11 20:45: todos abaixo estão com avatar padrão e/ou sem banner.

## Pelo PC (cada um pela saída fixa da conta, um por vez, nunca em laço)
O chat das capas aplica esses 6 em 18/11 às 21h, um canal por vez, com
`python bin\youtube_studio_extras.py --canal <slug> --foto ...\perfil.png --banner ...\banner.png --sobre ...\descricao.txt`.
Resultado em `canais\aplicar_pc_18nov.log`.

| Canal | @ | Pasta | Faltava |
|---|---|---|---|
| Clínica Lucrativa IA | @clinicalucrativaia | canais\clinicalucrativaia | perfil + banner |
| Empresário Inteligente IA | @empresariointeligenteia | canais\empresariointeligenteia | perfil + banner |
| Imóvel em Foco | @imovelemfoco | canais\imovelemfoco | perfil + banner |
| Lei e Lucro | @leielucroia | canais\leielucro | perfil + banner |
| Por Dentro | @pordentrobr-d4w | canais\pordentro | perfil + banner |
| Vendas que Escalam | @vendasqueescalam | canais\vendasqueescalam | perfil + banner |

## Celulares: aplicar SÓ pelo app do YouTube no próprio aparelho (teste 3 contas)
Copiar as imagens para o celular (adb push para /sdcard/Pictures) e aplicar no app. Nada pelo PC/Chrome do cofre.
| Canal | @ | Aparelho / conta | Pasta | Faltava |
|---|---|---|---|---|
| Curioso Demais | @CuriosoDemais-l6p | A2 / 2042 | canais\curiosodemais | perfil + banner |
| Fatos Ocultos | @FatosOcultos-x8j | A3 / 2054 | canais\fatosocultos | perfil + banner |
| Segredos Revelados | @SegredosRevelados-q8h | S20 Ultra / 2052 | canais\segredosrevelados | banner (perfil já tem; trocar é opcional) |

S20 (2043, "mundocuriosobr-h8e"): nome recusado, canal não concluído. Sem arte até a dona decidir.
Captcha ou confirmação = PARAR e avisar a dona.

## Também sem banner (já têm perfil): ficaram de fora
inovare_eng, inovare_french e inovaremanhwabr. Os kits antigos estão em canais\<slug>\banner.png e podem ser subidos se a dona quiser.

## Feito nos celulares (18/11 21:30-21:55, pelo app, chat das rondas)
- Segredos Revelados (S20U): foto + banner + descrição ✔.  Curioso Demais (A2): foto + banner + descrição ✔.
- Fatos Ocultos (A3): PENDENTE — o A3 está com confirmação do Google (conta antiga murilodoctor192) na tela; a dona decide.
  Quando liberar: `cd "D:\projeto celular sub controle\celular_canal"` e `python canal.py A3 kit D:\manhwa-react\canais\fatosocultos`.
- O banner 16:9 é cortado pelo editor do app; o canal.py gera `banner` preparado (quadro TV). Ver celular_canal\LEIA_ME.md.
