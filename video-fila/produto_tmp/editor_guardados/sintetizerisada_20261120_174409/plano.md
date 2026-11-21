# Plano de Edição — sintetizerisada_20261120_174409
Produto: Agenda IA
Duração: 35.43s (1063 frames a 30 fps)

## Identidade Visual e Regras Gerais
- Paleta:
  - Marca / Destaque: `#FFA94D` (laranja vibrante acolhedor)
  - Apoio / Fundo Escuro: `#1F2937` (slate escuro elegante)
  - Branco Puro: `#FFFFFF`
  - Verde Sucesso: `#22C55E`
- Safe Zone: x=60 a 1020, y=150 a 1580.
- Tipografia: Montserrat (pesos 700 a 900), tamanho mínimo 32px para qualquer texto/rótulo (títulos 40–64px).
- Legenda Karaokê: `import {Karaoke} from '../../lib/karaoke'` nas cenas 0 a 3; base=460 (y=1460 <= 1520), maxLetras=48 com quebras manuais para frases completas sem órfãos. Cartão final sem karaokê.
- Áudio: `narracao.mp3` no volume total, `trilha.mp3` com volume moderado e fade in/out.

---

## Cena 0 (0.00s – 5.24s | Frames 0 – 157)
- **Tipo:** Pergunta
- **Composição:** (a) Texto Cinético Gigante de Impacto + Card de Notificação Noturna sobre foto viva em zoom push-in.
- **Background:** `img_0.jpg` com escala contínua 1.05 -> 1.15 e vinheta escura progressiva para contraste ≥ 4.5:1.
- **Layout & Elementos:**
  - y=160–230: Badge pill "🚨 CANCELAMENTO DE MADRUGADA" com ícone pulsante.
  - y=270–500: Título cinético sincronizado com a locução:
    - 0.32s ("Cliente cancela"): Surge "CLIENTE CANCELA" em destaque bold.
    - 1.28s ("de madrugada"): Marca-texto animado `#FFA94D` sob "DE MADRUGADA".
    - 2.28s ("e você acorda..."): Completa com "HORÁRIO VAGO?".
  - y=560–880: Card de simulação de alerta noturno mobile (02:47 AM) com mensagem de cancelamento e status "Vaga ociosa ⚠️".
- **Movimento:** Push-in contínuo da foto (1.05 a 1.15), mola no badge aos 0.25s, pop do card aos 1.5s, brilho constante no texto.
- **Transição para Cena 1:** Fade cruzado suave (0.3s) com a entrada do vídeo do dono.

---

## Cena 1 (4.89s – 12.91s | Frames 147 – 387)
- **Tipo:** Dono
- **Composição:** (h) Vídeo cheio (`dono_1.mp4`) com câmera em movimento contínuo (scale 1.0 -> 1.06) + elementos ESTRITAMENTE na faixa superior (y=150 a 420).
- **Proteção ao Dono:** Rosto e tronco (y=480 a y=1400) 100% livres de qualquer elemento. Karaokê na base (y=1560).
- **Layout & Elementos (y=160–410):**
  - y=160–220: Badge pill `#FFA94D` com texto `#1F2937`: "O PROBLEMA • RELATO REAL".
  - y=240–390: Headline card superior dinâmico que alterna conforme as palavras:
    - 4.89s – 8.70s ("mensagens de cancelamento"): "MENSAGENS NA MADRUGADA"
    - 8.70s – 10.65s ("horário já estava perdido"): "HORÁRIO JÁ PERDIDO ❌"
    - 10.97s – 12.91s ("ninguém para ocupar a vaga"): "SEM NINGUÉM PRA VAGA 📉"
- **Movimento:** Zoom contínuo no vídeo (1.00 -> 1.06), micro-flutuação dos cards superiores, transições suaves de texto.
- **Transição para Cena 2:** Slide lateral com wipe dinâmico.

---

## Cena 2 (12.56s – 23.13s | Frames 377 – 694)
- **Tipo:** Conversa
- **Composição:** (b) Celular inclinado em 3D (perspective 1200px, rotateY -12°, largura 860px) + Chat WhatsApp animado mensagem a mensagem com digitação + Chips de garantia "Sem Conflito".
- **Background:** `img_2.jpg` com desfoque elegante e camada escura da marca + grid tecnológico sutil.
- **Layout & Elementos:**
  - y=160–230: Rótulo "COMO FUNCIONA • IA NO WHATSAPP" + selo "Simulação".
  - y=250–1260: Mockup de smartphone vertical com interface de WhatsApp nativo:
    - Top bar: Avatar Agenda IA, "Agenda IA 🤖", "Online 24h".
    - 13.0s: Cliente balão 1 entra: "Não vou conseguir ir amanhã cedo."
    - 14.9s ("A Agenda IA responde..."): Indicador "Digitando..." pulsa por 0.8s, entra balão IA 1: "Tudo bem! Posso reagendar para quinta às 10h ou sexta às 15h."
    - 17.4s ("reagenda sozinha..."): Cliente balão 2: "Quinta às 10h, por favor."
    - 19.1s ("oferece o horário livre..."): Balão IA 2 confirma: "Pronto, reagendado! Horário confirmado para você."
  - y=1270–1360: Chips flutuantes animados que entram sincronizados:
    - 19.8s ("sem conflito"): Chip verde "✓ Sem conflito de agenda"
    - 20.8s ("sem duplo agendamento"): Chip verde "✓ Sem duplo agendamento"
- **Movimento:** Câmera 3D com rotação lenta (rotateY -14° a -9°), scroll suave das mensagens para manter todas visíveis e legíveis (fontes 32px a 36px), chips entrando com escala e mola.
- **Transição para Cena 3:** Zoom-through com escala expansiva.

---

## Cena 3 (22.78s – 31.79s | Frames 683 – 954)
- **Tipo:** Imagem (Resultado)
- **Composição:** (g) Painel de Gestão Automatizada & Grade de Horários Preenchidos sobre foto viva do mascote.
- **Background:** `img_3.jpg` com push-in 1.05 -> 1.15 e iluminação quente da marca.
- **Layout & Elementos:**
  - y=160–230: Badge "O RESULTADO • AGENDA ORGANIZADA".
  - y=260–420: Headline dinâmico:
    - 23.2s – 27.9s: "CANCELOU? A IA REAGENDE SOZINHA"
    - 28.2s – 31.7s: "VOCÊ ACORDA COM O DIA ORGANIZADO"
  - y=450–1240: Painel de agendamentos em tempo real mostrando slots do dia:
    - Slot 09:00: Status "Reagendado IA" com badge verde.
    - Slot 10:30: Status "Confirmado" com badge verde.
    - Slot 14:00: Status "Confirmado" com badge verde.
    - Slot 16:00: Status "Reagendado IA" com badge verde.
    - Card inferior: "Recepção 24h a partir de R$ 199" (fato permitido do briefing!).
- **Movimento:** Entrada escalonada dos slots de agenda com delay de 0.2s, checkmarks animados, pulso de atividade no mascote e brilho suave.
- **Transição para Cena 4:** Deslize elegante com abertura de véu para o cartão final.

---

## Cena 4 (31.44s – 35.43s | Frames 943 – 1063)
- **Tipo:** Cartão Final
- **Composição:** Cartão de Alta Conversão de Agência (sem karaokê, foco total em CTA e marca).
- **Background:** `img_4.jpg` com desfoque moderado (blur 12px) + véu escuro (#1F2937 com 88% opacidade) + gradiente radial quente `#FFA94D`.
- **Layout & Elementos:**
  - y=320–540: Logo e Nome da Marca:
    - Ícone de IA / Agenda brilhante.
    - "AGENDA IA" em caixa alta com Montserrat Black (tamanho 76px, branco com contorno fino de destaque).
    - Subtítulo (y=500): "Agendamentos automáticos com IA 24h" (Montserrat Bold 36px).
  - y=660–840: Proposta de Valor / Fato Destacado:
    - Box elegante: "Trabalha 24 horas por dia • A partir de R$ 199/mês"
  - y=980–1140: Botão de Ação CTA:
    - Box sólido `#FFA94D` com texto `#1F2937` em caixa alta: "CHAME NO DIRECT"
    - Pulso contínuo (scale 1.00 a 1.08 em loop até o último frame) + raio de brilho passando.
  - y=1240–1340: Perfil Oficial:
    - "@sintetizerisada" com ícone do Instagram e badge verificado.
- **Movimento:** Fundo em zoom suave contínuo, partículas de brilho em ascensão, pulso constante do botão até o frame 1063, glow no logo. Movimento ≥ 4.0% garantido em 100% da cena.
