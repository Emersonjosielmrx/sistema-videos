# Plano de Edição — sintetizerisada_20261118_075946
Produto: Agenda IA
Duração: 29.36 s (881 frames @ 30 fps)
Cores: Marca #FFA94D | Apoio/Escuro #1F2937 | Destaque #FFA94D | Texto sobre marca #1F2937

## Safe Zone e Diretrizes Rígidas
- Área segura vertical: y = 150 a 1580 (margens x = 60 a 1020).
- Nenhum texto menor que 32px (piso absoluto em todo o projeto, inclusive mockups).
- Respiro vertical >= 30px entre divisores/barras e textos.
- Movimento contínuo de 0.0s até o final (zoom/pan de câmera e microanimações contínuas, sem nada estático por mais de 0.8s).
- Rostos do dono estritamente desobstruídos (faixa y=500 a 1250 livre nos vídeos dono_1 e dono_3).
- Karaokê oficial de `../../lib/karaoke.tsx` centralizado com base em y=1560 (base=360), ausente no cartão final.
- Somente fatos do briefing: sem números ou prazos inventados.

---

## Cena 0 (0.00s – 5.43s | Frames 0 – 163)
- **Tipo**: pergunta
- **Composição**: a) Texto cinético tela cheia com palavras-chave em destaque sobre fundo fotográfico em movimento + card de alerta da dor + gancho fixo.
- **Áudio/Fala**: "Preciso parar meus atendimentos para aprovar cada horário marcado?"
- **Câmera**: Push-in contínuo na foto img_0.jpg (scale 1.05 -> 1.15) com vinheta escura profunda.
- **Elementos Visuais**:
  - Barra de progresso no topo (y=160, h=6px).
  - Badge no topo (y=210): "DÚVIDA FREQUENTE" com ícone de interrogação pulsando.
  - Título cinético central (y=300 a 620): "Preciso parar meus atendimentos para aprovar cada horário marcado?" com entrada sincronizada nas palavras faladas e destaque em #FFA94D.
  - Card de dor (y=720): Alerta animado "Interrupção constante no atendimento" com ícone de notificação vermelha pulsando e contorno suave.
  - Aos ~4.0s: entra badge "A IA faz tudo sozinha?" (gancho_tela).
- **Transição**: Transição de saída suave em slide/wipe para a câmera do dono.

---

## Cena 1 (5.08s – 12.81s | Frames 152 – 384)
- **Tipo**: dono
- **Composição**: h) Vídeo real do dono em tela cheia com push-in sutil (scale 1.00 -> 1.06) e motion graphics exclusivos no topo.
- **Áudio/Fala**: "Eu interrompia atendimentos no estúdio o dia inteiro só para validar mensagens de horário."
- **Vídeo**: dono_1.mp4 (inicia em 5.08s, muted, rosto preservado entre y=500 e y=1250).
- **Elementos Visuais**:
  - Barra de progresso contínua (y=160).
  - Badge no topo (y=200): "A ROTINA PRESA" em cápsula contrastante (#1F2937 com borda #FFA94D).
  - Título dinâmico no topo (y=270 a 440): "Interrompia atendimentos só para validar horários" com animação de palavras sincronizadas.
  - Mini card lateral sutil (y=430) com contador de mensagens acumuladas não respondidas ("Validação Manual").
  - Karaokê na base (y=1560), sem cobrir o peito/rosto do dono.
- **Transição**: Zoom-through sutil / slide para o mockup 3D de celular.

---

## Cena 2 (12.46s – 18.21s | Frames 374 – 546)
- **Tipo**: conversa
- **Composição**: b) Celular moderno desenhado em React em perspectiva 3D (rotateY -12°, rotateX 4°) + balões de WhatsApp grandes entrando um a um.
- **Áudio/Fala**: "O cliente escolhe a vaga e o sistema finaliza o processo ponta a ponta."
- **Fundo**: img_2.jpg com pan horizontal e blur estilizado.
- **Elementos Visuais**:
  - Celular grande (w=860px) com cabeçalho WhatsApp da "Agenda IA", status "Online 24h" e selo "Simulação".
  - Balões escalonados rigorosamente sincronizados:
    1. Cliente (12.6s): "Oi, tem vaga para quinta às 15h?"
    2. Empresa digitando... (13.5s) -> Balão (14.2s): "Tenho sim! Deseja confirmar para quinta às 15h?"
    3. Cliente (15.2s): "Sim, pode marcar."
    4. Empresa digitando... (15.8s) -> Balão (16.4s): "Perfeito! Horário reservado com sucesso na agenda." + checkmark verde animado.
  - Todas as fontes do mockup >= 34px, alto contraste (balão verde WhatsApp #005D4B / #1F2937 / fundo cinza claro).
  - Badge superior (y=210): "AUTONOMIA TOTAL • 24 HORAS".
  - Karaokê ativo na base.
- **Transição**: Transição fluida de desmonte para o dono final.

---

## Cena 3 (17.86s – 25.72s | Frames 536 – 771)
- **Tipo**: dono
- **Composição**: h) Vídeo real do dono em tela cheia (dono_3.mp4) com push-in (scale 1.00 -> 1.06) e gráficos de autonomia no topo.
- **Áudio/Fala**: "Agora minha atenção fica inteira no cliente presencial enquanto os agendamentos automáticos rodam."
- **Vídeo**: dono_3.mp4 (inicia em 17.86s, muted, rosto preservado entre y=500 e y=1250).
- **Elementos Visuais**:
  - Barra de progresso contínua (y=160).
  - Badge no topo (y=200): "FOCO NO SERVIÇO" em verde esmeralda / âmbar.
  - Título dinâmico no topo (y=270 a 410): "Atenção inteira no cliente presencial" animado com mola.
  - Aos ~22.7s ("enquanto os agendamentos automáticos rodam"): card flutuante elegante (y=420) com tag "Agendamentos Automáticos Rodando" + indicador de pulso verde vivo e engrenagem sutil.
  - Karaokê na base (y=1560).
- **Transição**: Transição elegante em zoom/fade para o cartão final de conversão.

---

## Cena 4 (25.37s – 29.36s | Frames 761 – 881)
- **Tipo**: cartao (CTA final de alta conversão)
- **Composição**: Encerramento de agência de alta retenção, vivo até o último frame.
- **Áudio/Fala**: "Chame a gente no direct."
- **Fundo**: img_4.jpg com push-in lento (scale 1.05 -> 1.15) e véu gradiente escuro da marca.
- **Elementos Visuais**:
  - Barra de progresso finalizando em 100% (y=160).
  - Logo / Marca grande "AGENDA IA" (y=420) com ícone de calendário inteligente e brilho radial em #FFA94D.
  - Proposta de valor oficial (y=620): "Agendamentos automáticos com IA no WhatsApp".
  - Selos de confiança autorizados (y=780): "24 HORAS" • "SEM CONFLITO DE HORÁRIO".
  - BOTÃO PRINCIPAL DE AÇÃO (y=1040): "CHAME NO DIRECT"
    - Animação contínua de pulso (scale 1.00 a 1.08) até o frame 881.
    - Efeito de brilho/shimmer cruzando o botão.
  - Arroba oficial (y=1240): "@sintetizerisada" com tipografia encorpada e ícone elegante.
  - SEM Karaokê nesta cena (respeito estrito às regras).
