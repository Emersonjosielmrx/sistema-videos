# TAREFA 16 — Agente PRÉ-DIRETOR de efeitos (análise de imagem → efeito ideal por painel)

STATUS: [ ] pendente (ideia da usuária 2026-07-01)
PRIORIDADE: ALTA — resolve qualidade do roteamento de efeitos (T15) e usa o PC2 ocioso.

## A IDEIA (palavras da usuária)
Em vez de decidir o efeito na HORA do render (por keyword, rápido mas cego), ter um AGENTE que
analisa a IMAGEM de cada painel PREVIAMENTE e determina a combinação IDEAL de efeito/movimento —
igual ao agente que hoje pré-gera os depths de movimento. Roda em pequenos LOTES (1 por vez, com
calma/qualidade), usa Gemini Vision + Haiku (flash) pra escolher, e grava a decisão num cache.
Quando o script do vídeo rodar, a decisão JÁ ESTÁ PRONTA (não decide no momento).
- Rodar no PC2 (worker 192.168.18.7) quando ligado; nesta máquina quando PC2 desligado.
- Se o efeito escolhido ainda não existe, o próprio agente pode criá-lo (via COMANDOS_PROTOTIPOS
  já tem 126). Já são efeitos SUFICIENTES — o outro agente começou a REPETIR, então parar de criar
  novos e focar em ROTEAR bem os que existem.

## POR QUE (problema que resolve)
- Roteamento por keyword (T15 pick_effect) é raso: "olhou"→facezoom serve, mas a imagem pode pedir
  outra coisa (ex: 2 personagens, plano aberto, close de objeto). Visão real decide melhor.
- Decidir no render gasta tempo/quota na hora. Pré-computar em lote = render fica rápido e keyless.
- Aproveita o PC2 ocioso + cache compartilhado (mesma cultura do depth/narração/TTS).

## O QUE FAZER
1. `bin/fx_director.py` (novo agente pré-diretor):
   - `decidir_efeito(img_path, texto_narrado)` → escolhe efeito de panel_effects (+ elemental) pela
     IMAGEM (Gemini Vision: "que movimento/efeito combina? há 1 ou 2 personagens? close/plano aberto?
     objeto de destaque? +18?") + texto. Haiku (flash) pra classificar barato/rápido.
   - Grava decisão em cache: `workspace/fx_decisions/<md5_painel>.json` = {efeito, encaixe, foco:{x,y}, +18}.
   - Lotes: processa N painéis por vez, 1 chamada por painel, com backoff (não estourar quota).
   - Fallback: sem Gemini/erro → cai no pick_effect por keyword (T15). Nunca trava.
2. Consumo no pipeline: panel_effects.pick_effect passa a LER fx_decisions/<md5>.json primeiro;
   se existe, usa a decisão pré-computada (visão); senão, keyword. (mesma lógica do depth cache).
3. Prefetch/worker: script que roda em background (cron ou no PC2) pré-processando os painéis das
   obras pendentes. Ver worker_client.py / workers.json (PC2 192.168.18.7:8771) e o padrão do
   MotionFrames depth_prefetch. Rodar local só quando PC2 offline.
4. O foco:{x,y} que o Gemini der alimenta o posicionamento CAT3a (Passo C do IMPLEMENTAR_TUDO — pointer/
   zoomdetail/objectglow no lugar certo). Fecha aquela pendência de brinde.

## REGRAS
- Persistir decisão (cara: Gemini Vision) — nunca re-decidir o mesmo painel (cache md5).
- NÃO competir por chaves Gemini com geração de vídeo ativa (regra #8: 1 obra por vez no Gemini).
  Rodar quando o pipeline de vídeo NÃO estiver usando Gemini (ou usar chave/máquina separada = PC2).
- Efeitos JÁ SÃO SUFICIENTES (126). Parar de criar novos; foco em ROTEAR bem. M/Q (luz/glitch)
  mexem em cor/brilho → só com aprovação da usuária.
- Respeitar salvaguardas do pick_effect: +18 e texto-plano nunca recebem efeito.

## VALIDAR
- Self-test: decidir_efeito em 3-5 painéis variados (1 personagem / 2 personagens / objeto / +18 /
  texto) e conferir se a escolha faz sentido + grava o cache. Rodar 2x = 2ª lê cache (zero Gemini).
- Integração: pick_effect lê a decisão pré-computada quando existe.

## ⚡ PRÉ-FILTRO BARATO OBRIGATÓRIO (antes de chamar Gemini — regra da usuária)
Antes de gastar QUALQUER chamada de visão (mesmo no PC2), passar cada painel por filtros de
CÓDIGO locais (grátis, já existem) e DESCARTAR os que não vão receber efeito:
- **+18** (censura): usar detecção existente (Sightengine score / is_visual_nsfw). Painel +18 →
  pula (não vai ter efeito, vai ser censurado). NÃO mandar pro Gemini.
- **texto/plano**: panel_classifier.vale_parallax()==False → pula (só texto/onomatopeia).
- **capa/crédito**: is_cover_or_credit (haiku_helpers) ou heurística → pula.
- **painel sem narração** (texto vazio): pula.
Só o que SOBRA desse coador vai pro Gemini decidir o efeito. Economiza quota e tempo do PC2 —
o worker que fica rodando não desperdiça em painel que já sabemos que não recebe efeito.
Ordem: filtros locais (ms) → Gemini só nos candidatos reais.
