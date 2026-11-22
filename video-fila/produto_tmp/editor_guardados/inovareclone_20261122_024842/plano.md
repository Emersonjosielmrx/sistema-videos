# Plano de Edição — inovareclone_20261122_024842
Produto: Avatar IA (Inovare Clone) | Duração: 33.11s (994 frames a 30 fps)

## Diretrizes Gerais
- Safe zone rigorosa: conteúdo essencial entre y=150 e y=1580, margens laterais de 60px (x=60 a 1020).
- Tipografia mínima de 32px em todo o vídeo (títulos de 48px a 76px), família Montserrat.
- Movimento contínuo ≥ 4.0% em todas as cenas: zoom contínuo de fundo, animações físicas com spring e interpolação contínua.
- Rostos 100% protegidos nas cenas do dono (cabeça abaixo de y=290; grafismos no topo terminam em y=240, garantindo > 50px de respiro).
- Karaokê oficial (`import {Karaoke} from '../../lib/karaoke'`) com `base={360}` (ancorado em y=1560), destaque roxo `#8B5CF6` com texto `#FFFFFF`, quebras forçadas entre cenas e ausente no cartão final.
- Trilha com ducking inteligente: ~0.10 durante a fala e ~0.22 nas pausas/abertura/cartão final.

---

## Cena 0: Pergunta (0.00s a 4.55s | frames 0 a 136)
- **Composição:** a) Texto GIGANTE tela cheia (palavras cinéticas com destaque marca-texto) sobre fundo escurecido.
- **Fundo:** `img_0.jpg` com push-in (scale 1.05 -> 1.15) e overlay tecnológico gradiente (#0B0D13 a #1F2937).
- **Barra de Progresso:** y=150, altura 6px, largura preenchendo de x=60 a 1020 ao longo do vídeo.
- **Topo (y=165–225):** Selo de gancho `[ VÍDEOS DA SUA EMPRESA ]` com ponto pulsante #8B5CF6.
- **Centro (y=380–1100):**
  - 0.00s–0.30s: Radar pulsante e ícone de relógio/ampulheta com movimento.
  - 0.32s ("Falta tempo"): Título em 76px Montserrat 900 "FALTA TEMPO?" com caixa roxa #8B5CF6 sob a palavra "TEMPO".
  - 1.10s ("para explicar"): Deslize cinético de "PARA EXPLICAR" em 56px.
  - 1.75s ("seus serviços"): "SEUS SERVIÇOS" em 64px com sublinhado gradiente.
  - 2.66s ("em vídeo?"): Badge "EM VÍDEO? 🎬" em 60px com glow e mola.
- **Karaokê:** Palavras 0 a 7, base=360.
- **Transição:** Dissolvência suave e zoom-in entrando no clipe do dono aos 4.2s.

---

## Cena 1: O Dono — O Problema (4.20s a 12.38s | frames 126 a 371)
- **Composição:** h) Vídeo cheio com câmera em movimento lento (scale 1.00 -> 1.05) e rótulo no topo.
- **Vídeo:** `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` tela cheia cover.
- **Proteção do Rosto:** Cabeça do apresentador inicia em y=290. Elementos gráficos ficam exclusivamente na faixa y=155 a y=235 (>50px de respiro).
- **Topo (y=155–235):**
  - 4.30s: Rótulo `[ ETAPA 1 • O PROBLEMA ]` em card translúcido escuro com borda #8B5CF6.
  - 6.00s ("dia atendendo"): Tag flutuante `Agenda Cheia ⏳` desliza com mola.
  - 8.50s ("nunca sobrava tempo para gravar vídeos"): Tag de dor `Sem tempo p/ gravar 📹❌`.
- **Karaokê:** Palavras 8 a 22, base=360 (sobre a camisa preta, bem abaixo do queixo).
- **Transição:** Wipe direcional moderno para a cena de conversa.

---

## Cena 2: Conversa WhatsApp 3D — A Solução (12.03s a 21.69s | frames 361 a 650)
- **Composição:** b) Celular 3D inclinado (rotateY 14°, rotateX 4°, perspectiva 1200px) com conversa de WhatsApp de alta definição.
- **Fundo:** `img_2.jpg` com push-in (scale 1.05 -> 1.15) e vinheta escura da marca.
- **Topo (y=155–230):** Rótulo `[ ETAPA 2 • A SOLUÇÃO ]` com badge "Avatar IA Inovare Clone".
- **Mockup Mobile (y=245 a 1400, largura 840px):**
  - Smartphone com Dynamic Island, status bar e cabeçalho do WhatsApp (Avatar IA, nome "Inovare Clone", selo "Simulação").
  - Balões de conversa sincronizados com a narração (fonte 34px–36px):
    - 12.0s: Mensagem 1 (Cliente): "Como vocês conseguem postar explicando cada serviço todo dia?"
    - 13.0s: Indicador "digitando..." animado com 3 pontos.
    - 13.6s ("avatar IA"): Mensagem 2 (Empresa, roxo #8B5CF6): "Usamos nosso próprio avatar IA falando em português."
    - 16.5s: Mensagem 3 (Cliente): "E as posturas ficam naturais no vídeo?"
    - 17.4s ("automáticas"): Mensagem 4 (Empresa, roxo #8B5CF6): "Sim, as posturas automáticas mantêm a apresentação perfeita."
  - Badges de benefícios sincronizados com a fala:
    - 17.0s: Tag `✓ Posturas automáticas`
    - 18.5s: Tag `✓ Fala em português`
    - 19.5s: Tag `✓ 100% seu`
- **Karaokê:** Palavras 23 a 40, base=360.
- **Transição:** Zoom-in dinâmico conectando com a cena seguinte.

---

## Cena 3: O Dono — O Resultado (21.34s a 29.52s | frames 640 a 885)
- **Composição:** h) Vídeo cheio (`dono_3.mp4`) com câmera em movimento (scale 1.00 -> 1.05) e rótulo no topo.
- **Vídeo:** `<OffthreadVideo src={staticFile('dono_3.mp4')} muted />` tela cheia cover.
- **Proteção do Rosto:** Cabeça do apresentador inicia em y=290. Elementos gráficos ficam exclusivamente na faixa y=155 a y=235 (>50px de respiro).
- **Topo (y=155–235):**
  - 21.50s: Rótulo `[ ETAPA 3 • O RESULTADO ]` em badge luminoso #8B5CF6.
  - 23.50s ("explicações claras"): Tag `Explicações todo dia 🚀` entra com spring.
  - 27.00s ("foco nos atendimentos"): Tag `Foco nos atendimentos 💼✨` entra com spring.
- **Karaokê:** Palavras 41 a 53, base=360.
- **Transição:** Zoom-through suave com fade direcional para o cartão final.

---

## Cena 4: Cartão Final — CTA de Alta Conversão (29.17s a 33.11s | frames 875 a 994)
- **Composição:** Cartão final animado de alta conversão.
- **Fundo:** `img_4.jpg` com blur de 20px + overlay escuro #1F2937/0B0D13 + zoom contínuo (scale 1.05 -> 1.15).
- **Sem Karaokê:** Atenção 100% focada na conversão.
- **Conteúdo (y=260–1460):**
  - Logo estilizado e nome da marca "INOVARE CLONE" em Montserrat Black 72px branco.
  - Frase de valor: "Tenha seu próprio avatar IA postando todo dia nas redes." (38px).
  - Pílulas de benefícios: "Posturas automáticas" • "100% em português" • "100% seu" (32px).
  - Super Botão de CTA: "CHAME NO DIRECT" em 48px bold, fundo roxo #8B5CF6, com pulsação contínua (scale 1.00 a 1.07 em ciclos de 1.2s) e brilho translúcido (shimmer).
  - Perfil oficial visível do frame 0.0s do cartão: `@inovareclone` em 36px bold com ícone do Instagram.
