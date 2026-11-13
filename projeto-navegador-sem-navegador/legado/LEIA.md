# legado/ — primeira versão do projeto (27–28/10), fora de uso

Movido para cá em 30/10. Nada da produção (postador, Veo, gera_imagem, maquina_remota, painel) importava estes
arquivos; só os testes antigos daqui. A auditoria de 28/10 (PLANO_00h40.md) já mostrava que boa parte era chute:
IDs de RPC inventados no Fotos (`E1C6fd`, `v3IMjd`), "transferência" que só listava, Story/carrossel nunca testados,
teste que dava "SUCESSO TOTAL" com dado inventado.

O que vale hoje (testado em conta real):

| Assunto | Módulo |
|---|---|
| YouTube: upload, capa, playlist, selo | `services/youtube/upload_http.py` |
| YouTube: analytics do Studio | `services/youtube/studio_analytics.py` |
| Instagram: leitura | `services/instagram/web.py` |
| Instagram: Reel, Story, carrossel, bio, DM, comentário, destaque | `services/instagram/postar.py` |
| Google Fotos: busca, álbuns | `services/google_photos/fotos_http.py` |
| Flow/Veo: gerar imagem/vídeo, estender, corrigir | `services/veo_flow/flow_gerar.py` + `flow_http.py` |
| TikTok: analytics | `services/tiktok/studio.py` |
| Cookies | `core/cofre_cookies.py` (não o `auth.py` daqui) |

Para rodar algo daqui seria preciso devolver o arquivo à pasta original — não faça sem motivo.
