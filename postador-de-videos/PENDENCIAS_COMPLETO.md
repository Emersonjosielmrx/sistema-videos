# PENDÊNCIAS COMPLETAS — Sistema de Vídeos (16/10/2026 01:13)

## SITUAÇÃO ATUAL

### ✅ Sistemas Funcionando
- **Hub Telegram** (notificar_telegram.py): roda a cada 5 min
- **TikTok CDP** (tiktok_cdp_poster.py): 9 posts confirmados em 15/10
- **Veo Limpo**: 147 vídeos processados pela rede, 1 rejeitado (logo TikTok)
- **Aprendizado Global**: medição 48h ativa, arquivo aprendizado_global.json (6.8 KB)
- **Rede**: 159 vídeos aprovados na fila (inclui 8 Veo limpos aprovados 16/10 00:37)

### ⚠️ Bloqueios Operacionais

#### 1. Editorial — CORRIGIDO (16/10 01:20)
**Problema anterior**: Timeout em Opus impedia fallback para Sonnet
**Causa identificada**: Modelo Sonnet não estava configurado em secrets_proxy.json
**Correção aplicada**:
- ✅ Sonnet adicionado: `"sonnet": "kr/claude-sonnet-4.5"` em D:\manhwa-react\secrets_proxy.json
- ✅ Ordem otimizada: providers `["proxy:sonnet", "proxy:opus", "cli"]` em config.json (Sonnet primeiro)
- ✅ Testado: Sonnet responde em ~1s, gera JSON válido
**Impacto real**: "0 agendados" não é falha editorial, é falta de vídeos aprovados no ManhwaReact (3 JSONs, nenhum elegível)
**Arquivos**: D:\manhwa-react\secrets_proxy.json, D:\manhwa-react\config.json

#### 2. Groq Proxy Intermitente — PRIORIDADE MÉDIA
**Problema**: Limpeza Veo falha na transcrição quando proxies Webshare estão sem banda
**Causa**: Proxy Webshare (.59.20.176:6754) intermitente
**Status**: 
- **01:05 Drive**: 15 vídeos limpos COM SUCESSO (proxies funcionando, log 20:36-20:55)
- **01:05 Local**: 50 vídeos BLOQUEADOS por proxy (log 22:03-22:11)
**Fallback**: Whisper local configurado, mas módulo `faster_whisper` não instalado
**Impacto**: 226 vídeos Veo brutos aguardando limpeza (intermitente, não bloqueado permanente)
**Arquivos**: D:\postador-de-videos\bin\limpar_veo.py, bin\groq_api.py
**Ação necessária**: Sistema reagenda automaticamente (próxima: 06:40)

## DECISÕES PENDENTES DO USUÁRIO

### 1. veo_so_limpo — TikTok/Instagram
**Arquivo**: D:\postador-de-videos\config\reuso_plataformas.json
**Estado atual**: `"veo_so_limpo": false` (TikTok e Instagram)
**Decisão**: 
- `true` = só posta vídeo Veo LIMPO (sem slide WhatsApp)
- `false` = reaproveita o COMPLETO como antes
**Contexto**: Slide WhatsApp derrubou canais no YouTube; versão limpa já funciona

### 2. Balanceador Entre PCs
**Contexto**: PC2 (revision-pc-2, `ssh pc2`) e desktop (desktop-su00b7v, 100.73.7.19, `ssh -o BatchMode=yes desktop`, Windows sem senha desde 24/10 — só chave) via Tailscale
**Pendente**: 
- Qual PC faz o quê (produção/render)
- Logins necessários no PC2
- rclone no PC2 para backup Drive
**Avisos**: 
- PC2 tem workers hipercool/anime (portas 8771/8772)
- **NUNCA** rodar `taskkill /IM pythonw.exe` no PC2

### 3. Login TikTok: 3dfabricadeautomacoesia
**Arquivo**: D:\postador-de-videos\config\reuso_plataformas.json
**Estado**: Conta configurada com `"porta": 9251` mas sem login
**Temas**: aulas_ia, cerebro_digital
**Ação**: Logar a conta no perfil Chrome da porta 9251

### 4. Mapear Conteúdo — Contas TikTok Hipercool
**Contas sem mapeamento em reuso_plataformas.json**:
- msenergypara (MS Energy, português)
- inovaremanhwaverseesp (espanhol)
- inovaremanhwaversefrench (francês)
- inovaremanhwaversehindi (hindi)
- inovaremanhwaverserussian (russo)

**Estado dos canais YouTube hipercool**:
- inovare_esp: **suspenso** (YouTube)
- inovare_french: **pausado** (strike direitos autorais até ~26/12/2026)
- inovare_eng: **pausado** (envios bloqueados até ~21/10/2026)
- inovare_hindi: **hipercool** (só projeto hipercool usa)
- inovare_ita: **hipercool**
- inovare_ru: **hipercool**
- inovare_thai: **hipercool**
- inovare_ind: **hipercool**
- inovaremanhwabr: **ativo** (já mapeado no TikTok: inovaremanhwaverseita)

**Ação**: Decidir quais contas TikTok postam qual tipo de conteúdo (temas/projetos/canais)

### 5. Renovar Tokens Instagram — 10 Contas Vencidas
**Lista de D:\credenciais-canais\LEIA.md**:
1. sintetizerisada
2. recenas.ia
3. fakenews.ia4
4. danceandmusicwith.ia
5. dicasfinanceiras.ia
6. fabricadeautomacoesia
7. fabricadeautomacoesn8n
8. emerson.inteligenciaartificial
9. inovaremanhwaverseesp

**Nota**: Credenciais extraídas do n8n (VPS 209.145.60.53) em 30/06/2026
**Arquivo**: D:\credenciais-canais\todas_credenciais.json (329 credenciais)
**Ação**: Renovar tokens Instagram dessas 9 contas

### 6. Sugestão Recaps Hipercool
**Achado crítico**: recaps hipercool rendem 0-5 views (mesmo vídeo em 7-8 canais)
**Padrão identificado**: Cross-posting = padrão que derrubou rede antiga
**Sugestão documentada**: 1 vídeo/canal, sem repetir visual no mesmo dia
**Decisão**: Aplicar ou não a restrição

## LOGINS YOUTUBE PENDENTES (API → Navegador)

**Contexto**: Decisão 13/10/2026 — Google pelo NAVEGADOR, não por API
**Arquivos**: 
- Logins: D:\logins-google\cofre (cofre.py)
- Config navegador: D:\postador-de-videos\config\youtube_navegador.json
- Poster: D:\postador-de-videos\bin\youtube_web_poster.py

**Pendentes de login (ainda saem pela API)**:
1. **ManhwaReact**: emersonjosiel2032@gmail.com
2. **Animescomia**: canalanimescomia@gmail.com
3. **ForjaReact**: emersonjosiel0@gmail.com
4. **Mundo Que Não Existe**: rezaulkarimul355@gmail.com (login morto)
5. **Fio da Meada**: emersonjosiel2031@gmail.com

**Procedimento**: 
1. Logar conta no cofre: `python D:\logins-google\cofre.py`
2. Adicionar `"usar": true` no youtube_navegador.json
3. Desligar produção do canal antes do login

**Canais hipercool sem login (não postam)**:
- inovare_ind: inovaremanhwaverseind@gmail.com (sem login)
- inovare_thai: inovaremanhwaversethai@gmail.com (sem login)

**Canal principal bloqueado**:
- **InovareManhwaVerse**: abrir Studio e fechar aviso de advertência de direitos autorais (ou fazer curso). Hipercool segura português até isso.

## NÚMEROS E ESTATÍSTICAS

### Vídeos Veo (atualizado 16/10 01:17)
- **226 brutos** aguardando limpeza (D:\hipercool-materiais\veo\veo_videos_iniciais\, 3.5 GB)
- **158 JSONs limpos** (D:\hipercool-materiais\veo\limpos\, 1.2 GB) — +10 desde 00:37
- **157 processados** pela rede (postados ou agendados) — +10 desde 00:37
- **1 rejeitado**: robos_desastrad_20260729_102749 (logo TikTok detectado)
- **Primeiro postado**: alienigenas_20260806_074758 no InventoReact (15/10 às 20h)
- **Última limpeza**: 15 vídeos do Drive processados com sucesso (16/10 01:05, log 20:36-20:55)

### Rede de Distribuição (atualizado 16/10 01:17)
- **12 canais ativos** (20 totais, 9 hipercool)
- **161 vídeos** na fila aprovada (+2 desde 00:37)
- **0 vídeos** agendados (bloqueado por editorial)
- **9 canais** sem vídeo para 15/10: animescomia, inovaremanhwabr, cartuchoreact, forjareact, mundoquenaoexiste, historiasemframes, fiodameada, dicasfinanceirasdaia, assistiainvestimentos

### TikTok/Instagram
- **TikTok**: 7 contas configuradas (4 com login, 1 sem login, 2 sem mapear)
- **Instagram**: 4 contas configuradas
- **Limite**: max 3/dia TikTok, 2/dia Instagram por conta

## TAREFAS AUTOMATIZADAS FUNCIONANDO

### Diárias
- **06:40**: Limpeza Veo (novos locais + 15 do Drive/dia)
- **08:00**: Resumo Telegram (ranking 24h)
- **A cada 5 min**: Hub Telegram (comentários, respostas, avisos)

### Agendadas
- **Cron 01:03** (16/10): Revisão modelo mais capaz (este documento já cumpriu)

## DOCUMENTAÇÃO

### Criada nesta sessão
- D:\postador-de-videos\STATUS_MODELO_SIMPLES.md (15/10 23:36)
- D:\postador-de-videos\VERIFICACAO_CORRELACAO.md (15/10 23:38)
- D:\postador-de-videos\PENDENCIAS_COMPLETO.md (este arquivo, 16/10 01:13)

### Pré-existente
- D:\postador-de-videos\LEIA.txt
- D:\manhwa-react\CLAUDE.md
- D:\credenciais-canais\LEIA.md
- Memory: feedback_pc2_hipercool.md, project_veo_limpo.md

## AVISOS CRÍTICOS

### ⚠️ PC2 (revision-pc-2)
- Workers hipercool/anime rodando (portas 8771/8772)
- **NUNCA** rodar `taskkill /IM pythonw.exe` no PC2
- Acessível via Tailscale SSH: 100.73.7.19

### ⚠️ MS Energy
- telegram_monitor.py usa o MESMO bot do hub Telegram
- Se rodar junto, **rouba as respostas** aos comentários
- Não iniciar enquanto NotificarTelegram estiver ativo

### ⚠️ Detector Veo
- Sempre conferir ÚLTIMO quadro também (logo pode aparecer só no final)
- Limiar calibrado: com marca 0.65-0.70, limpos ≤0.52
- Aprovação manual: extrair quadros e inspecionar visualmente

### ⚠️ Google
- **NÃO** criar projeto, chave nem OAuth no Google Cloud
- YouTube: postar pelo navegador (youtube_web_poster.py)
- Drive: rclone usa chave pública própria (aceitar lentidão, não criar chave)

## PRÓXIMAS AÇÕES RECOMENDADAS

### Imediatas
1. ✅ Limpeza Veo Drive concluída (15 vídeos, 16/10 01:05)
2. ✅ Editorial corrigido (16/10 01:20): Sonnet configurado e testado
3. Próxima limpeza Veo automática: 06:40
4. Produzir mais vídeos ManhwaReact (fila vazia: 3 JSONs, nenhum elegível)

### Quando usuário voltar
1. Decidir `veo_so_limpo` (true/false) para TikTok e Instagram
2. Logar 5 contas YouTube no cofre (ManhwaReact, Animescomia, ForjaReact, MundoQueNaoExiste, FioDaMeada)
3. Mapear contas TikTok hipercool (esp, french, hindi, russian, msenergypara)
4. Renovar 9 tokens Instagram vencidos
5. Abrir Studio InovareManhwaVerse e fechar aviso de direitos autorais

---
**Gerado por**: Opus 5.5 (01:13) + Sonnet 4 (01:20 correção editorial)
**Data**: 16/10/2026 01:13 (análise) + 01:20 (correções)  
**Contexto**: Continuação do trabalho do Sonnet 4 (23:36-23:38) após cron 01:03
**Correções aplicadas**: Editorial desbloqueado (Sonnet configurado, providers otimizados)
