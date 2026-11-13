# Projeto Navegador Sem Navegador

Automação **HTTP pura** no padrão do gemini-argo: os cookies do Chrome do cofre (`D:\logins-google\cofre`) e os
endpoints internos dos sites (batchexecute, youtubei, GraphQL, rupload), sem abrir o Chrome no fluxo do dia a dia.
O Chrome só entra para colher cookies/token quando vencem, ou (Flow) para fabricar o token do reCAPTCHA.

Histórico, provas e decisões: `PLANO_00h40.md`. Implantar numa máquina nova: `IMPLANTAR_MAQUINA.md`.
Revisão de 30/10: `MELHORIAS_30-10.md`. Primeira versão (fora de uso): `legado/`.

## O que está em produção

| Quem usa | Módulo | Faz |
|---|---|---|
| `postador-de-videos/bin/youtube_web_poster.py` | `services/youtube/upload_http.py` | upload agendado, capa, playlist, selo sintético |
| `postador-de-videos/bin/metricas_rede.py` | `services/youtube/studio_analytics.py` | Shorts, tráfego, termos de busca, retenção |
| `postador-de-videos/bin/postar_insta_auto.py`, `maquina_remota.py` | `services/instagram/postar.py` (CLI `reel`) | Reel por HTTP (PC1 e notebooks/PC2) |
| `postador-de-videos/bin/produto/medir_web.py` | `services/instagram/web.py` | leitura de perfil e Reels |
| `D:\veo\beta\gera_auto.py`, `D:\flow-imagens\gera_imagem.py`, `maquina_remota.py` | `services/veo_flow/flow_gerar.py` | vídeo/imagem do Flow por HTTP |
| tarefa `NSN_ManterCookies` (1 h) | `tools/manter_cookies.py` | gira e usa os cookies do Studio |
| tarefa `NSN_Inteligencia` (07:30/19:30) | `relatorios/inteligencia.py` | central de inteligência + contas TikTok mortas |
| tarefa `NSN_ColherNotebooks` (2 h) | `tools/colher_notebooks.py` | colhe cookies do Instagram nas máquinas |
| painel :8790 | `tools/saude.py`, `tools/monitor_banimento.py` | saúde HTTP e banimentos |

Também prontos (testados em conta real, sem tarefa): Story, carrossel, bio/link, destaque, comentário e DM do
Instagram (`postar.py`), robô QUERO (`tools/quero.py`), Google Fotos busca/álbuns (`services/google_photos/fotos_http.py`)
e catálogo com visão (`catalogo_visao.py`), TikTok analytics (`services/tiktok/studio.py`), Flow estender/corrigir/16:9/
quadro inicial e final.

## Uso rápido

```bash
python -m services.youtube.upload_http <slug> video.mp4 "título" --agendar EPOCH [--capa capa.jpg]
python -m services.youtube.studio_analytics <slug> [--video ID]
python -m services.instagram.web <conta>
python -m services.instagram.postar reel <conta> video.mp4 "legenda"      # ou @legenda.txt
python -m services.instagram.postar story <conta> imagem.jpg
python -m services.google_photos.fotos_http <conta> "painel solar" 50 [--baixar pasta]
python -m services.veo_flow.flow_gerar <conta> imagem "prompt" saida.png [--formato 16:9]
python -m services.tiktok.studio <conta>
python tools\quero.py <conta> --seco
```

Use o python do `D:\veo\venv` (tem curl_cffi, websocket-client, Pillow, filelock). `--maquina <nome>` / `--local`
escolhem onde rodar quando a conta só está logada num notebook (`core/maquinas.py`).

## Regras

- Postagem do YouTube sempre agendada ou privada — o `upload_http` recusa público direto e horário que já passou.
- Cada máquina usa os próprios cookies; nunca copiar `cookies/` entre máquinas.
- Instagram: mesmo PC/IP/UA do Chrome do cofre; conta marcada por spam fica em pausa.
- Endpoint ou id de RPC só entra no código depois de capturado de uma sessão real.

## Testes

Dois cliques em `testar.cmd`, ou de qualquer pasta:

```bash
D:\projeto-navegador-sem-navegador\testar.cmd
```

(`python D:\projeto-navegador-sem-navegador\tests\test_offline.py` também serve: sem as bibliotecas do projeto, ele
relança sozinho com o python do `D:\veo\venv`.)

Sem rede, sem Chrome e sem cookies reais (gravação atômica, trava dos cookies, travas do upload do YouTube, formatos
reais de resposta do Instagram/Flow, paginação do TikTok, robô QUERO, pacote dos notebooks).
