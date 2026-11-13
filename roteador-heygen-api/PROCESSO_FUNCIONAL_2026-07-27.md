# HeyGen — Processo Funcional (2026-07-27)

Documentação do **fluxo real e funcional** que descarrega vídeos do HeyGen automaticamente via CDP, sem mexer no F12 manualmente.

> **Status:** funcionando ponta-a-ponta em conta paga (Creator). Cada vídeo demora ~60-90s e gera 1 MP4 de ~7MB.

---

## Pré-requisitos

1. **Conta paga HeyGen** (Creator $24/mês ou Pro $41/mês). Avatar III e o render de vídeo exigem assinatura.
2. **Python 3.13+** com `websockets` instalado (já tem no venv em `D:\hipercool-videos\venv`).
3. **Google Chrome** instalado em `C:\Program Files\Google\Chrome\Application\chrome.exe`.
4. Sessão do HeyGen **logada** com cookies salvos no perfil Chrome (evita ter que logar toda vez).

---

## Arquivos-chave (usar sempre estes)

| Arquivo | Função |
|---|---|
| [chrome_cdp.py](chrome_cdp.py) | Abre Chrome com `--remote-debugging-port=9225` e `--user-data-dir` pra guardar cookies |
| [loop_6_videos.py](loop_6_videos.py) | **Pipeline completo** que processa os 6 tópicos de [topics.json](topics.json) |
| [topics.json](topics.json) | Lista de 6 textos PT-BR (claude_code, n8n_automacao, mcp_protocol, agentes_ia, vibe_coding, cursor_ide) |
| [baixa_primeiro.py](baixa_primeiro.py) | Baixa APENAS o vídeo atual que está no DOM (uso manual/teste) |
| [play_e_inspeciona.py](play_e_inspeciona.py) | Diagnóstico: lista videos + URLs + atributos F12 |
| [sniff_render.py](sniff_render.py) | Sniff de rede durante render (alternativo) |

### Scripts legados / debug (NÃO usar)

- [cdp_loop.py](cdp_loop.py), [pega_preview.py](pega_preview.py), [driver_avatar3.py](driver_avatar3.py), [driver_avatar3_v2.py](driver_avatar3_v2.py), [clica_direto.py](clica_direto.py), [fluxo_completo.py](fluxo_completo.py), [fluxo_final.py](fluxo_final.py), [driver_inteligente.py](driver_inteligente.py), [switch_avatar3.py](switch_avatar3.py), [sniff_rede.py](sniff_rede.py), [sniff3.py](sniff3.py), [clica_play.py](clica_play.py), [re_render.py](re_render.py), [click_avatar3_v3.py](click_avatar3_v3.py), [ver_dropdown.py](ver_dropdown.py), [investiga_so_um.py](investiga_so_um.py), [pega_url_dos_videos.py](pega_url_dos_videos.py), [click_render_scene.py](click_render_scene.py), etc.

> A pasta virou um cemitério de tentativas. O **único pipeline confiável** é [loop_6_videos.py](loop_6_videos.py). Apague os legados quando for a hora.

---

## Como rodar

### 1. Abre Chrome com sessão logada
```bash
python D:/roteador-heygen-api/chrome_cdp.py
```

O script:
- Abre Chrome em `https://app.heygen.com/create-v4/draft?vt=l`
- Usa `--remote-debugging-port=9225` (CDP)
- Usa `--user-data-dir=chrome_profile_heygen/` pra guardar cookies entre sessões

**Se for primeira vez**, faça login manualmente em `fabricadeautomacoesia@gmail.com` + senha. Próximas vezes, o Chrome já sobe logado.

### 2. Roda o loop dos 6 vídeos
```bash
python D:/roteador-heygen-api/loop_6_videos.py
```

O pipeline faz, para cada tópico:
1. `Page.navigate` → `https://app.heygen.com/create-v4/draft?vt=l&panel=scene`
2. Aguarda editor carregar
3. Digita texto no campo `[contenteditable=true]` char-por-char via `Input.dispatchKeyEvent` com `type=char`
4. Garante `Avatar III` selecionado (abre dropdown Motion Engine → clica opção "Avatar III" por coordenadas)
5. Clica botão **Render Scene** (NUNCA Generate)
6. Espera aparecer **"Scene rendered"** no DOM (polling 5s, max 180s)
7. Coleta `video.src` de `document.querySelectorAll("video")` — URL S3 com X-Amz-* signed
8. Download via `urllib.request.urlopen` com `User-Agent: Mozilla/5.0`
9. Salva em `D:\roteador-heygen-api\videos\api_jobs\<topic_id>_<hash>.mp4`

Ao final, abre o Explorer na pasta de saída.

---

## Onde cada coisa vive

- **Chrome perfil**: `D:\roteador-heygen-api\chrome_profile_heygen\` (cookies, cache)
- **Vídeos baixados**: `D:\roteador-heygen-api\videos\api_jobs\<topic_id>_*.mp4`
- **Debug screenshots**: `D:\roteador-heygen-api\processos\*.jpg`
- **Logs de processo**: `D:\roteador-heygen-api\processos\log_*.txt`
- **Memória persistente**: `C:\Users\Haylla\.claude\projects\d--hipercool-videos\memory\`

---

## O que mudou (lições aprendidas)

### O que NÃO funciona
1. **Gerar vídeo via API REST direta**: bloqueado, exige cookies + CSRF específico que muda.
2. **Pegar URL via Network sniffing de "scene_preview"**: o URL é dinâmico e vem em outra rota (HeyGen S3 temporário).
3. **Clicar no dropdown por texto + closest()**: a Ant Design quebra o evento. Tem que ser por coordenadas.
4. **Reload do editor (`Page.navigate`) durante o fluxo**: o draft é uma SPA que reseta o estado mas perde o vídeo já renderizado.
5. **Usar Avatar IV**: no plano Free não gera preview; com conta paga Avatar IV só gera clipes próprios (não vídeo final).
6. **Worker pesado no DOM com MutationObserver**: travou a aba e foi cortado pelo Chrome.

### O que FUNCIONA
1. **Manter o dropdown fechado e Avatar III selecionado** desde o começo (clicar Avatar III na lista do dropdown).
2. **Render Scene (não Generate)**: renderiza o vídeo real, custa crédito mas é mais barato que Generate.
3. **Esperar "Scene rendered" aparecer no DOM** (texto visível num `<div>` sem filhos).
4. **Pegar URL de `<video>.src` direto** — vem como URL real S3 da AWS, NÃO blob.
5. **Download via urllib direto com User-Agent** — a URL S3 com X-Amz-Signature já autoriza download.

### A real sobre o HeyGen
- **Avatar III** está no dropdown Motion Engine: Avatar V → IV → III. Não está bloqueado em conta paga. Clicar pelo texto "Avatar III" não funciona (parent DIV dispara o evento errado). Tem que ser por coordenadas exatas.
- **Modal de "Switch to Avatar III"**: aparece quando você clica Render Scene com Avatar IV e está perto do limite. Aceita ilimitado. Se já passou pelo free tier com limite esgotado, precisa aceitar (Switch to Avatar III ou Continue with Avatar IV).
- **Resolução**: 1920x1080 (Full HD).
- **Duração**: proporcional ao texto. ~1000 chars → ~15-20s.
- **Formato**: MP4 com vídeo + áudio multiplexados, ~7MB pra 15s.
- **URL S3**: `https://heygen-resources-prod.s3-accelerate.amazonaws.com/tmp_resource/a2v/<project_id>/<hash>.mp4?X-Amz-*` — válida por 7 dias (`X-Amz-Expires=604800`).

---

## Pipeline detalhado

```
[START] page == draft?vt=l&panel=scene
  ↓
[STATE CHECK]
  - avatar == "Avatar III"?   → se não, abrir dropdown e clicar
  - texto vazio?              → se sim, pular pra digitar
  ↓
[TYPE TEXT]
  - limpa campo (Ctrl+A + Delete)
  - digita char por char com Input.dispatchKeyEvent type="char"
  ↓
[GARANTIR AVATAR III]
  - se já está, skip
  - senão: getBoundingClientRect do botão Motion Engine → click central
  - dormir 1.5s → pegar coordenadas do item Avatar III → click
  ↓
[RENDER SCENE]
  - click() direto via JS
  - checa "Scene rendered" no DOM em loop de 5s (max 180s)
  ↓
[PEGAR URL]
  - varre document.querySelectorAll("video")
  - filtra src que tem ".mp4" e NAO é blob
  ↓
[DOWNLOAD]
  - urllib.request.urlopen com User-Agent: Mozilla/5.0
  - timeout 180s
  - salva como D:\roteador-heygen-api\videos\api_jobs\<id>_<hash>.mp4
  ↓
[PROXIMO TOPICO] → pause 10s e repete
```

---

## Troubleshooting

**Editor não carrega**: a aba tá em URL diferente (ex: home). O script já navega. Espere ~8s e verifique `location.href`.

**Render Scene desabilitado**: ele mostra "Disabled" enquanto processa. Espere ou recarregue.

**"Scene rendered" não aparece**: pode ter excedido limite de minutos. Aparece modal "Switch to Avatar III / Continue with Avatar IV". Clique manualmente se necessário.

**URL é blob:** o vídeo ainda não foi gerado de verdade (só placeholder). Espere mais 30s e re-tente.

**Download falha com erro S3 403:** URL expirou (X-Amz-Expires=604800s). Re-renderize o vídeo.

**Chrome fecha sozinho:** provavelmente CDP foi desconectado. Rode `python chrome_cdp.py` de novo.

---

## Modal de limite mensal (Render Scene)

Quando você clica **Render Scene** com **Avatar IV** ativo e o limite mensal foi atingido, o HeyGen abre um modal com 2 opções:

```
Render Scene
This will go 65s over your 45 min monthly limit for Avatar IV. Choose how you'd like to continue.

┌─ Switch to Avatar III ────────────┐ ┌─ Continue with Avatar IV ─────────┐
│ ✓ Unlimited usage                 │ │ ✓ Moves realistically like you    │
│ ✓ Adds lip sync over real footage │ │ ✓ Face, body and background adapt │
│ ⓘ Body language & background     │ │ ⓘ Free monthly limit: 0 min avail │
│   won't adapt to script           │ │                                    │
│ [Switch to Avatar III]            │ │ [Continue with Avatar IV]          │
└────────────────────────────────────┘ └────────────────────────────────────┘
```

### Limites do plano Creator ($24/mês)

| Avatar | Limite mensal | Custo extra |
|---|---|---|
| **Avatar III** | **Ilimitado** | $0 |
| Avatar IV | 45 min/mês | Cobra do saldo extra |
| Avatar V | ? (não testado) | ? |

### Como automatizar o modal

**Coordenadas úteis do modal (1920x1080):**
- Botão X (canto superior direito): `(1670, 295)` — fecha sem ação
- **"Switch to Avatar III"** CTA azul: `(793, 588)` ← **USE ESTE**
- "Continue with Avatar IV" CTA azul: `(1300, 588)`

**Estratégia recomendada:** SEMPRE garantir Avatar III antes de clicar Render Scene. Se o modal mesmo assim aparecer (caso de race condition), clicar em (793, 588) e re-tentar.

### Teste realizado em 2026-07-27

- Tentamos gerar 30 min de áudio (~21000 chars)
- char-by-char (12ms) só persiste ~50% do texto (1003 chars de 2000 digitados)
- Modal apareceu quando clicamos Render Scene com Avatar IV
- Clicamos "Switch to Avatar III" → modal fechou
- Render Scene re-clicado → **render levou 17 minutos para vídeo de 61s**
- Vídeo final: 27 MB, 1920x1080, MP4 com S3 URL válida

> **Conclusão**: Avatar III é o caminho. Sem limite, sem modal. Único trade-off: body language e background não se adaptam ao script (mas pra vídeos de texto liso isso não importa).

---

## Memória persistente (já escrita)

- [heygen_avatar3_disponivel.md](C:\Users\Haylla\.claude\projects\d--hipercool-videos\memory\heygen_avatar3_disponivel.md): Avatar III está selecionável no dropdown
- [feedback_clicar_coordenadas.md](C:\Users\Haylla\.claude\projects\d--hipercool-videos\memory\feedback_clicar_coordenadas.md): sempre clicar dropdown por coordenadas x,y do item
- [heygen_mp4_renderizado.md](C:\Users\Haylla\.claude\projects\d--hipercool-videos\memory\heygen_mp4_renderizado.md): URL aparece em video.src como S3 X-Amz-*
