# Reanálise: Hypit, GSAP, Three.js e PixiJS — o que serve e o que não serve

Data: 28/10/2026 (reanálise cuidadosa, baseada em código lido)
Origem: Reel do @guilhermepozzatto no Instagram + pedido da dona.

---

## 1. Hypit (github.com/hypit-ai/hypit)

### O que é
Framework TypeScript/Node 22+ que dá a agentes de IA (Claude Code, Codex) uma linguagem declarativa
(SVML) para compor vídeos. "Clone any viral video" = engenharia reversa de um vídeo de referência em
roteiro SVML editável, depois renderização paralela em Chromium headless (64 processos).

### O que tem dentro (lido no repo D:\caches\hypit)
- ~80 pacotes: cli, compiler, executor, runtime, html-video, caption, caption-fine,
  narrative-speech-alignment, whisperx, timeline-author, visual-track, audio-track, ranking,
  interview-emoji-reveal, gpt-image, seedance, fishaudio-speech, etc.
- Skill `/hypit` para Claude Code (skills/hypit/SKILL.md + playbooks detalhados de craft).
- Exemplos funcionais: ranking-football ($1.15), podcast ($1.07), street-interview ($1.09).
- Licença Apache 2.0 modificada: uso comercial próprio OK, multi-tenant pago, redistribuição paga proibida.

### Onde serve nos nossos projetos

#### claude-code-video (Remotion)
- **SIM — engenharia reversa de storytelling.** O playbook `reference-video.md` é ouro: método
  sistemático de ler um vídeo frame a frame, anotar ANALYSIS.md + TIMELINE.md, e transformar em
  composição nova. Podemos adotar esse MÉTODO sem instalar o Hypit — o editor já usa Remotion.
- **SIM — caption-fine e narrative-speech-alignment.** Legendas word-level com WhisperX que o
  Remotion não tem nativamente. O `karaoke.tsx` atual (3.6 KB) é básico; o Hypit faz color-box
  karaoke com tracking de speaker, cue-shapes e animação. Vale **extrair a lógica** ou
  **portar** o alinhamento para o workflow Remotion existente.
- **NÃO — substituir Remotion pelo Hypit inteiro.** O claude-code-video já tem infra Remotion
  com efeitos.tsx (Camera, Parallax, Tremor, Flutuar, Pulsar, Entrar, Mergulho, Flash,
  Particulas), karaoke.tsx, pipeline de renderização. Trocar tudo = reescrever do zero.
  Melhor: pegar ideias e módulos específicos.

#### postador-de-videos\bin\produto (MS Energy)
- **SIM — clonagem de ads.** O caso de uso "clone ad from Meta Ad Library, swap product" é
  exatamente o que o Hypit faz. Para vídeos de PRODUTO (não de manhwa), o Hypit pode ser o
  motor principal. Custo: ~$1/vídeo (modelos de geração de imagem/vídeo).
- **ATENÇÃO:** Requer Node 22.15+ e pnpm 10.33. O PC1 tem Node? Precisa verificar.

#### hipercool-videos (Manhwa Noturno)
- **NÃO SERVE DIRETAMENTE.** O hipercool trabalha com painéis de manhwa reais (não gerados),
  narração TTS+RVC, pipeline Python (hiper-pipeline.py). O Hypit é para vídeos com A-roll +
  B-roll + legendas — formato diferente.
- **TALVEZ:** O módulo whisperx do Hypit pode melhorar o alinhamento de legendas, mas o
  hipercool já usa faster-whisper + words.json. Ganho marginal.

#### hipercool-motionframes
- **NÃO SERVE.** O motionframes faz depth estimation (Depth-Anything-V2-Small) + parallax 2.5D
  em CPU com ffmpeg. É pipeline Python/ffmpeg puro. O Hypit é web-based (Chromium headless).
  Mundos diferentes.

---

## 2. GSAP (GreenSock Animation Platform)

### O que é
Biblioteca JS de animação com timelines, curvas de easing, ScrollTrigger. Padrão da indústria
para web e motion design.

### Onde serve

#### claude-code-video (Remotion)
- **CONFLITO.** O Remotion tem seu próprio sistema de animação: `interpolate()`, `spring()`,
  `Easing.*`. O efeitos.tsx já usa isso extensivamente. GSAP não roda dentro do Remotion sem
  gambiarra (Remotion controla o frame, GSAP controla o tempo — são modelos incompatíveis).
- **PODE SER ÚTIL:** Estudar as curvas de easing do GSAP (power4, expo, elastic, bounce) e
  replicá-las como funções `Easing.*` customizadas no Remotion. Isso é grátis e simples.

#### landings-produtos
- **SIM — caso perfeito.** Páginas de venda estáticas com animações de scroll, reveals, contadores.
  GSAP + ScrollTrigger é exatamente para isso. Instalar via CDN, zero build.

#### hipercool-motionframes / hipercool-videos
- **NÃO SERVE.** Ambos são Python + ffmpeg. GSAP é JavaScript para browser/Node.

---

## 3. Three.js

### O que é
Motor 3D WebGL para browser e Node. O claude-code-video JÁ TEM como dependência (`three` +
`@remotion/three` + `@react-three/fiber` no package.json).

### Onde serve

#### claude-code-video (Remotion)
- **JÁ ESTÁ INSTALADO** mas **não está sendo usado** (nenhum .tsx importa Three.js ainda).
  Oportunidade: títulos 3D flutuantes, fundo procedural com partículas volumétricas, showcase
  de produto rotativo. O `@remotion/three` já faz a ponte Remotion↔Three.js.

#### postador-de-videos (Remotion do produto)
- **IDEM,** já tem three + @remotion/three instalados, não usados. Mesma oportunidade.

#### Demais projetos
- **NÃO SERVE.** São Python + ffmpeg.

---

## 4. PixiJS

### O que é
Renderizador 2D WebGL/WebGPU, 60-120 FPS, filtros via shader.

### Onde serve

#### claude-code-video / postador-de-videos (Remotion)
- **POSSÍVEL mas com ressalvas.** PixiJS e Remotion podem coexistir (o PixiJS renderiza num
  canvas, o Remotion captura o canvas), mas é complexo. A lib efeitos.tsx já cobre os efeitos
  2D comuns (partículas, flash, tremor, pulsar). PixiJS só ganha se precisar de efeitos muito
  pesados (centenas de partículas, shaders customizados).

#### hipercool-motionframes
- **NÃO SERVE.** O motionframes é ffmpeg + depth map + Python. Não há browser envolvido.

#### hipercool-videos (censura/delogo)
- **NÃO SERVE.** A censura usa OpenCV (Python). Substituir por PixiJS (JS) não faz sentido no
  pipeline existente.

---

## Resumo: o que fazer de fato

| Tecnologia | Projeto | Ação concreta | Prioridade |
|---|---|---|---|
| **Hypit** | claude-code-video | Adotar o MÉTODO de engenharia reversa (playbook reference-video.md). Portar caption-fine/alignment para o Karaoke.tsx | Alta |
| **Hypit** | postador\bin\produto | Testar como motor de clonagem de ads de produto (MS Energy). Instalar Node 22 se não tiver | Média |
| **GSAP** | landings-produtos | Instalar via CDN para animações de scroll nas landing pages | Média |
| **GSAP** | claude-code-video | NÃO instalar. Extrair curvas de easing como funções Remotion customizadas | Baixa |
| **Three.js** | claude-code-video + postador | Já instalado. Criar componentes 3D (título rotativo, fundo de partículas, showcase de produto 360°) | Média |
| **PixiJS** | todos | Não instalar agora. Reavaliar se surgir necessidade de efeitos 2D pesados que o efeitos.tsx não cubra | Baixa |

---

## Voz do narrador de Todo Mundo Odeia o Chris

Modelo RVC baixado do HuggingFace (`linnhoAI123/Chrisnarrador`) e instalado em:
`D:\hipercool-materiais\models\rvc\vozes\narrador_chris\`
- `narrador_chris.pth` (55 MB)
- `narrador_chris.index` (19 MB)

Uso: `voz_clonada.py converter narrador_chris <narracao.wav> <saida.wav>`
(Tom será calculado automaticamente no primeiro uso.)

Única versão encontrada na internet (HuggingFace). Weights.gg não tem.
