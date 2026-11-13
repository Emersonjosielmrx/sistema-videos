# Índice da biblioteca de fluxos n8n

Gerado por `ferramentas\centraliza.py` em 30/10/2026 13:01. 78 fluxos atuais + 37 versões antigas (em `_versoes`).

Legenda: **n8n puro** = roda num n8n comum só com credenciais (nada para instalar no servidor). ⚠️ chave = tem chave/token escrito dentro do fluxo (trocar por credencial antes de passar adiante).

## anuncio-video (7)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [Vídeo de Anúncio com IA · ffmpeg na nuvem + voz Google (sem marca d'água) - V3](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20ffmpeg%20na%20nuvem%20+%20voz%20Google%20(sem%20marca%20d'água)%20-%20V3.json) | 116 | Agente de IA, HTTP, IA (OpenAI/roteador), Redis, Very Good FFmpeg, catbox, roteador OmniRoute, voz Google Tradutor, wsrv.nl | **n8n puro** | `D:\hipercool-materiais\fluxo-anuncio-api\v3\fluxo_v3.json` |
| [Vídeo de Anúncio com IA · ffmpeg na nuvem · textos novos - V3b](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20ffmpeg%20na%20nuvem%20·%20textos%20novos%20-%20V3b.json) | 116 | Agente de IA, HTTP, IA (OpenAI/roteador), Redis, Very Good FFmpeg, catbox, roteador OmniRoute, voz Google Tradutor, wsrv.nl | **n8n puro** | `D:\hipercool-materiais\fluxo-anuncio-api\v3b\fluxo_v3b.json` |
| [Vídeo de Anúncio com IA · Fotos → Reels narrado (estratégia, roteiro, revisão, voz) - ok - 07/11](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20Fotos%20Reels%20narrado%20(estratégia,%20roteiro,%20revisão,%20voz)%20-%20ok%20-%2007%2011.json) | 97 | Agente de IA, HTTP, IA (OpenAI/roteador), Redis, roteador OmniRoute | video-oficina (servidor de vídeo próprio) | `D:\hipercool-materiais\fluxo-anuncio-api\original.json` (+1 cópia) |
| [Vídeo de Anúncio com IA · JSON2Video (sem servidor de vídeo) - V1](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20JSON2Video%20(sem%20servidor%20de%20vídeo)%20-%20V1.json) | 112 | Agente de IA, HTTP, IA (OpenAI/roteador), JSON2Video, Redis, catbox, roteador OmniRoute, wsrv.nl | **n8n puro** | `D:\hipercool-materiais\fluxo-anuncio-api\v1\fluxo_v1.json` |
| [Vídeo de Anúncio com IA · JSON2Video · textos novos - V1b](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20JSON2Video%20·%20textos%20novos%20-%20V1b.json) | 112 | Agente de IA, HTTP, IA (OpenAI/roteador), JSON2Video, Redis, catbox, roteador OmniRoute, wsrv.nl | **n8n puro** | `D:\hipercool-materiais\fluxo-anuncio-api\v1b\fluxo_v1b.json` |
| [Vídeo de Anúncio com IA · Shotstack (sem servidor de vídeo) - V2](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20Shotstack%20(sem%20servidor%20de%20vídeo)%20-%20V2.json) | 112 | Agente de IA, ElevenLabs, HTTP, IA (OpenAI/roteador), Redis, Shotstack, catbox, roteador OmniRoute, wsrv.nl | **n8n puro** | `D:\hipercool-materiais\fluxo-anuncio-api\v2\fluxo_v2.json` |
| [Vídeo de Anúncio com IA · Shotstack · textos novos - V2b](biblioteca/anuncio-video/Vídeo%20de%20Anúncio%20com%20IA%20·%20Shotstack%20·%20textos%20novos%20-%20V2b.json) | 112 | Agente de IA, ElevenLabs, HTTP, IA (OpenAI/roteador), Redis, Shotstack, catbox, roteador OmniRoute, wsrv.nl | **n8n puro** | `D:\hipercool-materiais\fluxo-anuncio-api\v2b\fluxo_v2b.json` |

## hermes-ligacoes-telegram (7)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [Hermes - Disparar Ligacao para o 984698653 ⚠️ chave](biblioteca/hermes-ligacoes-telegram/Hermes%20-%20Disparar%20Ligacao%20para%20o%20984698653.json) | 4 | HTTP | **n8n puro** | `D:\hipercool-videos\workspace\N8N_CALL_NEW_WORKFLOW.json` |
| [Hermes - Fazer Ligação para 91984698653 ⚠️ chave](biblioteca/hermes-ligacoes-telegram/Hermes%20-%20Fazer%20Ligação%20para%2091984698653.json) | 4 | HTTP | **n8n puro** | `D:\hipercool-videos\workspace\N8N_CALL_BROADCAST_WORKFLOW.json` |
| [Hermes API - Audio Call Proxy](biblioteca/hermes-ligacoes-telegram/Hermes%20API%20-%20Audio%20Call%20Proxy.json) | 2 | HTTP | **n8n puro** | `D:\hipercool-videos\workspace\audio_injection_workflow.json` |
| [HermesCall V2 All Endpoints copy 2 ⚠️ chave](biblioteca/hermes-ligacoes-telegram/HermesCall%20V2%20All%20Endpoints%20copy%202.json) | 89 | HTTP | **n8n puro** | `D:\hipercool-videos\workspace\workflow_YvcqTFj3qWCkBQhm.json` |
| [hermescall4-brodcast ⚠️ chave](biblioteca/hermes-ligacoes-telegram/hermescall4-brodcast.json) | 7 | HTTP | **n8n puro** | `D:\hermes\hermes-call\_arquivo\2026-09-24_vindo-de-hipercool-videos\dados\wf_original.json` |
| [PromovaWeb-Sexta-Feira: 🤖 Hermes Telegram (Agente IA) ⚠️ chave](biblioteca/hermes-ligacoes-telegram/PromovaWeb-Sexta-Feira%20Hermes%20Telegram%20(Agente%20IA).json) | 14 | HTTP, Telegram API, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxos\PromovaWeb-Sexta-Feira_ 🤖 Hermes Telegram (Agente IA).json` |
| [🚀 Disparo Calls + Massa (com Loop)](biblioteca/hermes-ligacoes-telegram/Disparo%20Calls%20+%20Massa%20(com%20Loop).json) | 27 | HTTP | **n8n puro** | `D:\downloads\fluxos\🚀 Disparo Calls + Massa (com Loop).json` |

## livros (10)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [📚 Revisão de livro · 0 · Leitor (fichas)](biblioteca/livros/Revisão%20de%20livro%20·%200%20·%20Leitor%20(fichas).json) | 27 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\01 - 0 · Leitor (fichas).json` |
| [📚 Revisão de livro · 1 · Arquiteto (carta editorial)](biblioteca/livros/Revisão%20de%20livro%20·%201%20·%20Arquiteto%20(carta%20editorial).json) | 24 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\02 - 1 · Arquiteto (carta editorial).json` |
| [📚 Revisão de livro · 2 · Físico (continuidade)](biblioteca/livros/Revisão%20de%20livro%20·%202%20·%20Físico%20(continuidade).json) | 24 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\03 - 2 · Físico (continuidade).json` |
| [📚 Revisão de livro · 3 · Psicólogo (personagens)](biblioteca/livros/Revisão%20de%20livro%20·%203%20·%20Psicólogo%20(personagens).json) | 24 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\04 - 3 · Psicólogo (personagens).json` |
| [📚 Revisão de livro · 4 · Estilista (linha e voz)](biblioteca/livros/Revisão%20de%20livro%20·%204%20·%20Estilista%20(linha%20e%20voz).json) | 38 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\05 - 4 · Estilista (linha e voz).json` |
| [📚 Revisão de livro · 5 · Relojoeiro (cena a cena)](biblioteca/livros/Revisão%20de%20livro%20·%205%20·%20Relojoeiro%20(cena%20a%20cena).json) | 24 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\06 - 5 · Relojoeiro (cena a cena).json` |
| [📚 Revisão de livro · 6 · Beta (leitores simulados)](biblioteca/livros/Revisão%20de%20livro%20·%206%20·%20Beta%20(leitores%20simulados).json) | 38 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\07 - 6 · Beta (leitores simulados).json` |
| [📚 Revisão de livro · 7 · Guardião (style sheet)](biblioteca/livros/Revisão%20de%20livro%20·%207%20·%20Guardião%20(style%20sheet).json) | 38 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\08 - 7 · Guardião (style sheet).json` |
| [📚 Revisão de livro · 8 · Checklist final (editor-chefe)](biblioteca/livros/Revisão%20de%20livro%20·%208%20·%20Checklist%20final%20(editor-chefe).json) | 22 | Agente de IA, HTTP, IA (OpenAI/roteador), Redis, roteador OmniRoute | video-oficina (servidor de vídeo próprio) | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\09 - 8 · Checklist final (editor-chefe).json` |
| [📚 Revisão de livro · Editor-chefe (comece aqui)](biblioteca/livros/Revisão%20de%20livro%20·%20Editor-chefe%20(comece%20aqui).json) | 92 | HTTP, Redis | **n8n puro** | `D:\downloads\fluxo n8n farael\fluxos n8n (importar)\00 - Editor-chefe (comece aqui).json` |

## paginas-e-apps (10)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [App do Negócio (PWA) com IA + Notificações no Celular - ok](biblioteca/paginas-e-apps/App%20do%20Negócio%20(PWA)%20com%20IA%20+%20Notificações%20no%20Celular%20-%20ok.json) | 87 | Agente de IA, HTTP, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\App do Negócio (PWA) com IA + Notificações no Celular - ok.json` |
| [backend manager-financeiro](biblioteca/paginas-e-apps/backend%20manager-financeiro.json) | 27 | HTTP, Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\backend manager-financeiro.json` |
| [backend-plataforma ⚠️ chave](biblioteca/paginas-e-apps/backend-plataforma.json) | 133 | Agente de IA, Gemini, HTTP, Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\paginas painel\backend-plataforma.json` (+1 cópia) |
| [comunidade pro](biblioteca/paginas-e-apps/comunidade%20pro.json) | 153 | Agente de IA, Gemini, Gemini API, HTTP, Redis, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\comunidade pro.json` |
| [Gerador de Landing Page por IA](biblioteca/paginas-e-apps/Gerador%20de%20Landing%20Page%20por%20IA.json) | 12 | Agente de IA, IA (OpenAI/roteador), roteador OmniRoute | **n8n puro** | `D:\downloads\Gerador de Landing Page por IA.json` |
| [Gerador de Landing Page por IA — PRO (multiagente) - ok](biblioteca/paginas-e-apps/Gerador%20de%20Landing%20Page%20por%20IA%20—%20PRO%20(multiagente)%20-%20ok.json) | 52 | Agente de IA, IA (OpenAI/roteador), Redis, roteador OmniRoute | **n8n puro** | `D:\downloads\Gerador de Landing Page por IA — PRO (multiagente) - ok.json` |
| [KG Estratégico](biblioteca/paginas-e-apps/KG%20Estratégico.json) | 7 | Agente de IA, IA (OpenAI/roteador), Postgres, Supabase | **n8n puro** | `D:\downloads\fluxos\KG Estratégico (1).json` (+1 cópia) |
| [modulo-financeiro](biblioteca/paginas-e-apps/modulo-financeiro.json) | 49 | Agente de IA, Gemini, Gemini API, HTTP, Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\modulo-financeiro.json` |
| [PAINEL financeiro](biblioteca/paginas-e-apps/PAINEL%20financeiro.json) | 14 | Postgres | **n8n puro** | `D:\downloads\fluxos\PAINEL financeiro.json` |
| [site mental](biblioteca/paginas-e-apps/site%20mental.json) | 5 | - | **n8n puro** | `D:\downloads\fluxos\site mental.json` |

## servidor-e-monitoramento (5)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [jarvis-tratamento de erros e aviso ⚠️ chave](biblioteca/servidor-e-monitoramento/jarvis-tratamento%20de%20erros%20e%20aviso.json) | 11 | Agente de IA, Gemini, HTTP, IA (OpenAI/roteador), Redis, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\jarvis-tratamento de erros e aviso.json` |
| [jarvis-tratamento de erros e aviso final ⚠️ chave](biblioteca/servidor-e-monitoramento/jarvis-tratamento%20de%20erros%20e%20aviso%20final.json) | 52 | Agente de IA, Gemini, HTTP, Postgres, Redis, SSH, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\jarvis-tratamento de erros e aviso final (1).json` |
| [PromovaWeb-Sexta-Feira: 📈 Termômetro das VPSs](biblioteca/servidor-e-monitoramento/PromovaWeb-Sexta-Feira%20Termômetro%20das%20VPSs.json) | 6 | SSH | **n8n puro** | `D:\downloads\fluxos\PromovaWeb-Sexta-Feira_ 📈 Termômetro das VPSs.json` |
| [PromovaWeb-Sexta-Feira: 📰 Radar de Notícias v4](biblioteca/servidor-e-monitoramento/PromovaWeb-Sexta-Feira%20Radar%20de%20Notícias%20v4.json) | 28 | Agente de IA, Gemini, HTTP, Redis, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\PromovaWeb-Sexta-Feira_ 📰 Radar de Notícias v4.json` |
| [PromovaWeb-Sexta-Feira: 🤖 Autocura (Limpeza Automática)](biblioteca/servidor-e-monitoramento/PromovaWeb-Sexta-Feira%20Autocura%20(Limpeza%20Automática).json) | 8 | HTTP, SSH, Telegram API | **n8n puro** | `D:\downloads\fluxos\PromovaWeb-Sexta-Feira_ 🤖 Autocura (Limpeza Automática).json` |

## video-e-imagem (17)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [[v1] Youtube Auto Create and Post](biblioteca/video-e-imagem/[v1]%20Youtube%20Auto%20Create%20and%20Post.json) | 60 | ElevenLabs, Google Planilhas, HTTP, IA (OpenAI/roteador), SSH, YouTube (OAuth) | **n8n puro** | `D:\downloads\fluxos\v1YoutubeAutoCreateandPost.json` |
| [[v2] Youtube Auto Create and Post](biblioteca/video-e-imagem/[v2]%20Youtube%20Auto%20Create%20and%20Post.json) | 46 | Agente de IA, Gemini, Gmail, Google Drive, Google Planilhas, HTTP, IA (OpenAI/roteador) | **n8n puro** | `D:\downloads\fluxos\v2YoutubeAutoCreateandPost.json` |
| [aula fabrica viral ⚠️ chave](biblioteca/video-e-imagem/aula%20fabrica%20viral.json) | 30 | Agente de IA, Google Drive, HTTP, IA (OpenAI/roteador), YouTube (OAuth) | **n8n puro** | `D:\downloads\fluxos\aula fabrica viral.json` (+1 cópia) |
| [aula fabrica viral novo 1 copy ⚠️ chave](biblioteca/video-e-imagem/aula%20fabrica%20viral%20novo%201%20copy.json) | 38 | Agente de IA, Gemini, Google Drive, HTTP, IA (OpenAI/roteador), Redis, WhatsApp (Evolution/WuzAPI), YouTube (OAuth) | **n8n puro** | `D:\downloads\fluxos\aula fabrica viral novo 1 copy.json` |
| [calculadora de sensura](biblioteca/video-e-imagem/calculadora%20de%20sensura.json) | 5 | - | **n8n puro** | `D:\downloads\fluxos\calculadora de sensura.json` |
| [cria video de historia youtube ⚠️ chave](biblioteca/video-e-imagem/cria%20video%20de%20historia%20youtube.json) | 195 | Agente de IA, Arquivo no disco do servidor, Comando no servidor, ElevenLabs, Gemini, Gemini API, Google Drive, Google Planilhas, HTTP, IA (OpenAI/roteador), Redis, WhatsApp (Evolution/WuzAPI) | arquivos no disco do servidor, programa no servidor (Execute Command) | `D:\downloads\fluxos\cria video de historia youtube.json` |
| [fabrica de animes-1-funcional copy 2 ⚠️ chave](biblioteca/video-e-imagem/fabrica%20de%20animes-1-funcional%20copy%202.json) | 32 | Arquivo no disco do servidor, Comando no servidor, HTTP, WhatsApp (Evolution/WuzAPI) | arquivos no disco do servidor, programa no servidor (Execute Command) | `D:\downloads\fluxos\fabrica de animes-1-funcional copy 2.json` |
| [fabrica de animes-3-cria video pequeno copy](biblioteca/video-e-imagem/fabrica%20de%20animes-3-cria%20video%20pequeno%20copy.json) | 1 | - | **n8n puro** | `D:\downloads\fluxos\fabrica de animes-3-cria video pequeno copy.json` |
| [fabrica de animes-4-cria videos grandes compilados](biblioteca/video-e-imagem/fabrica%20de%20animes-4-cria%20videos%20grandes%20compilados.json) | 1 | - | **n8n puro** | `D:\downloads\fluxos\fabrica de animes-4-cria videos grandes compilados.json` |
| [Fábrica Viral-1-gera prompt ⚠️ chave](biblioteca/video-e-imagem/Fábrica%20Viral-1-gera%20prompt.json) | 53 | Agente de IA, Gemini, HTTP, Postgres, Redis | **n8n puro** | `D:\downloads\fluxos\Fábrica Viral-1-gera prompt.json` |
| [Fábrica Viral-2-gera imagem copy ⚠️ chave](biblioteca/video-e-imagem/Fábrica%20Viral-2-gera%20imagem%20copy.json) | 30 | Agente de IA, Gemini, Gemini API, HTTP | **n8n puro** | `D:\downloads\fluxos\Fábrica Viral-2-gera imagem copy.json` |
| [maquina de reels ⚠️ chave](biblioteca/video-e-imagem/maquina%20de%20reels.json) | 38 | Agente de IA, Gemini, Google Drive, HTTP, IA (OpenAI/roteador) | nó da comunidade n8n-nodes-instagram-token.instagram | `D:\downloads\fluxos\maquina de reels.json` |
| [RENATA GERA VIDEO E IMAGEM DESING](biblioteca/video-e-imagem/RENATA%20GERA%20VIDEO%20E%20IMAGEM%20DESING.json) | 29 | Agente de IA, Gemini, Gemini API, Google Drive, HTTP, IA (OpenAI/roteador), Redis | **n8n puro** | `D:\downloads\fluxos\RENATA GERA VIDEO E IMAGEM DESING.json` |
| [Sub-workflow - analiza video ⚠️ chave](biblioteca/video-e-imagem/Sub-workflow%20-%20analiza%20video.json) | 12 | Gemini API, HTTP | **n8n puro** | `D:\downloads\fluxos\Sub-workflow - analiza video.json` |
| [Sub-workflow_transcreve_imagem ⚠️ chave](biblioteca/video-e-imagem/Sub-workflow_transcreve_imagem.json) | 5 | Gemini API, HTTP | **n8n puro** | `D:\downloads\fluxos\Sub-workflow_transcreve_imagem.json` |
| [VITRINE-envio de produto com imagem e confirmacao do pedido - wuzapi](biblioteca/video-e-imagem/VITRINE-envio%20de%20produto%20com%20imagem%20e%20confirmacao%20do%20pedido%20-%20wuzapi.json) | 32 | Agente de IA, Gemini, HTTP, IA (OpenAI/roteador), Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\VITRINE-envio de produto com imagem e confirmacao do pedido - wuzapi (1).json` (+1 cópia) |
| [Youtube Auto Create and Post](biblioteca/video-e-imagem/Youtube%20Auto%20Create%20and%20Post.json) | 46 | Agente de IA, Gemini, Gmail, Google Drive, Google Planilhas, HTTP, IA (OpenAI/roteador) | **n8n puro** | `D:\downloads\fluxos\YoutubeAutoCreateandPost (1).json` (+2 cópias) |

## whatsapp-atendimento (22)

| Fluxo | Nós | Precisa | Instalar no servidor | Veio de |
|---|---|---|---|---|
| [advogado trab ⚠️ chave](biblioteca/whatsapp-atendimento/advogado%20trab.json) | 53 | Agente de IA, Gemini, Gemini API, HTTP, IA (OpenAI/roteador), Postgres, Redis, SSH, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\advogado trab.json` |
| [agendamento banco](biblioteca/whatsapp-atendimento/agendamento%20banco.json) | 20 | Agente de IA, Gemini, Postgres | **n8n puro** | `D:\downloads\fluxos\agendamento banco.json` |
| [agente que tras conversas anteriores](biblioteca/whatsapp-atendimento/agente%20que%20tras%20conversas%20anteriores.json) | 49 | Agente de IA, Gemini, HTTP, IA (OpenAI/roteador), Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\agente que tras conversas anteriores (1).json` (+1 cópia) |
| [ajuda humana+treinamento informatica](biblioteca/whatsapp-atendimento/ajuda%20humana+treinamento%20informatica.json) | 19 | Agente de IA, Gemini, HTTP, IA (OpenAI/roteador), Redis, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\ajuda humana+treinamento informatica (1).json` |
| [atendimento 1](biblioteca/whatsapp-atendimento/atendimento%201.json) | 17 | Agente de IA, Gemini, HTTP, Redis | **n8n puro** | `D:\downloads\fluxos\atendimento 1 (1).json` |
| [disparo e folow up remarketing em massa evoluion rei dos cartuchos ⚠️ chave](biblioteca/whatsapp-atendimento/disparo%20e%20folow%20up%20remarketing%20em%20massa%20evoluion%20rei%20dos%20cartuchos.json) | 47 | Agente de IA, Gemini, HTTP, Postgres, Redis, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\disparo e folow up remarketing em massa evoluion rei dos cartuchos.json` |
| [DPS — Atendimento Unificado (Texto + Áudio)](biblioteca/whatsapp-atendimento/DPS%20—%20Atendimento%20Unificado%20(Texto%20+%20Áudio).json) | 43 | Agente de IA, Gemini, HTTP, IA (OpenAI/roteador), Redis | **n8n puro** | `D:\downloads\fluxos\DPS — Atendimento Unificado (Texto + Áudio).json` |
| [edson](biblioteca/whatsapp-atendimento/edson.json) | 5 | Agente de IA, Gemini, IA (OpenAI/roteador) | **n8n puro** | `D:\downloads\fluxos\edson (2).json` |
| [ext-21-folowup remarketing que envia mensgem fixa](biblioteca/whatsapp-atendimento/ext-21-folowup%20remarketing%20que%20envia%20mensgem%20fixa.json) | 66 | HTTP, Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\ext-21-folowup remarketing que envia mensgem fixa.json` |
| [extrai contatos de chats whatsapp](biblioteca/whatsapp-atendimento/extrai%20contatos%20de%20chats%20whatsapp.json) | 36 | Agente de IA, Gemini, HTTP, Postgres, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\extrai contatos de chats whatsapp.json` |
| [Flow Rei do Cartucho (Reparado com Frontend) ⚠️ chave](biblioteca/whatsapp-atendimento/Flow%20Rei%20do%20Cartucho%20(Reparado%20com%20Frontend).json) | 51 | Agente de IA, Gemini, HTTP, Postgres, Redis, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\Fluxo_Corrigido.json` |
| [fluxo sem api de emvio macro](biblioteca/whatsapp-atendimento/fluxo%20sem%20api%20de%20emvio%20macro.json) | 15 | Agente de IA, Gemini, HTTP, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\fluxo sem api de emvio macro.json` |
| [hub-atendimento ⚠️ chave](biblioteca/whatsapp-atendimento/hub-atendimento.json) | 167 | Agente de IA, Gemini, Gemini API, Google Planilhas, HTTP, IA (OpenAI/roteador), Postgres, Redis, SSH, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\hub-atendimento.json` |
| [imoveis ⚠️ chave](biblioteca/whatsapp-atendimento/imoveis.json) | 4 | - | **n8n puro** | `D:\downloads\fluxos\imoveis.json` |
| [jarvis-tratamento de erros e aviso final ⚠️ chave](biblioteca/whatsapp-atendimento/jarvis-tratamento%20de%20erros%20e%20aviso%20final.json) | 53 | Agente de IA, Gemini, HTTP, IA (OpenAI/roteador), Postgres, Redis, SSH, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\VITRINE_EIA_V2\JARVIS_OPS_COMPLETE_V13_20260518_101741\jarvis_ops\jarvis-tratamento de erros e aviso final.json` |
| [memoria de elefante Com gerenciador](biblioteca/whatsapp-atendimento/memoria%20de%20elefante%20Com%20gerenciador.json) | 54 | Agente de IA, IA (OpenAI/roteador), Postgres | **n8n puro** | `D:\downloads\fluxos\memoria de elefante Com gerenciador (1).json` (+1 cópia) |
| [MODELO DE ATENDIMENTO DE TESTE GRATIS ⚠️ chave](biblioteca/whatsapp-atendimento/MODELO%20DE%20ATENDIMENTO%20DE%20TESTE%20GRATIS.json) | 46 | Agente de IA, Gemini, Gemini API, HTTP, IA (OpenAI/roteador), Postgres, Redis, SSH, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\MODELO DE ATENDIMENTO DE TESTE GRATIS.json` |
| [Sub-workflow acionamento do desligamento](biblioteca/whatsapp-atendimento/Sub-workflow%20acionamento%20do%20desligamento.json) | 8 | Redis | **n8n puro** | `D:\downloads\fluxos\Sub-workflow acionamento do desligamento.json` |
| [Sub-workflow de presenca e maracado como lido](biblioteca/whatsapp-atendimento/Sub-workflow%20de%20presenca%20e%20maracado%20como%20lido.json) | 6 | HTTP, WhatsApp (Evolution/WuzAPI) | **n8n puro** | `D:\downloads\fluxos\Sub-workflow de presenca e maracado como lido.json` |
| [Sub-workflow-analiza-pdf](biblioteca/whatsapp-atendimento/Sub-workflow-analiza-pdf.json) | 14 | HTTP | **n8n puro** | `D:\downloads\fluxos\Sub-workflow-analiza-pdf.json` |
| [Sub-workflow-transcreve_audio ⚠️ chave](biblioteca/whatsapp-atendimento/Sub-workflow-transcreve_audio.json) | 8 | Gemini API, HTTP | **n8n puro** | `D:\downloads\fluxos\Sub-workflow-transcreve_audio.json` |
| [SãdentesSecretaria](biblioteca/whatsapp-atendimento/SãdentesSecretaria.json) | 59 | Agente de IA, HTTP, IA (OpenAI/roteador), Postgres, Redis, Supabase, WhatsApp (Evolution/WuzAPI) | nó da comunidade n8n-nodes-evolution-api.evolutionApi | `D:\downloads\fluxos\SãdentesSecretaria (3).json` |
