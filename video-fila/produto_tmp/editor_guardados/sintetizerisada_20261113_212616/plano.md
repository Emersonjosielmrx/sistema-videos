# Plano de Edição — sintetizerisada_20261113_212616
Produto: Agenda IA
Duração: 32.10s (963 frames a 30fps)
Cores: Marca/Destaque #FFA94D | Fundo/Apoio #1F2937 | Texto Claro #F9FAFB | Fundo Dark #111827

## Safe Zone & Regras Gerais
- Altura útil: y = 150 a y = 1580 (largura útil: x = 60 a x = 1020).
- Barra de progresso: y = 152, altura 5px, cor #FFA94D.
- Karaoke: `<Karaoke />` oficial com base 360 (base em y = 1560), destaque #FFA94D. Oculto no cartão final.
- Tipografia: Montserrat (Black/Bold), títulos >= 50px, textos e balões >= 32px.
- Movimento contínuo em todas as cenas: zoom suave 1.0 -> 1.07 no fundo, transições com mola e interpolação.

---

## Cena 0: Pergunta & Gancho (0.0s – 5.94s | frames 0 – 178)
- **Tipo / Composição:** a) Texto GIGANTE tela cheia sobre foto com máscara escurecida + selo de gancho.
- **Visual:** Foto `img_0.jpg` (recepção do salão) com zoom lento (1.0 -> 1.08) e vinheta escura com gradiente #1F2937 (opacidade 85%).
- **Layout & Elementos:**
  - y = 180–260: Selo com mola (entra aos 0.3s): `[ IA NO WHATSAPP ]` com ponto pulsante.
  - y = 300–620: Texto Cinético Grande em 3 linhas com quebra balanceada:
    - Linha 1: "UMA IA REALMENTE" (entra aos 0.4s)
    - Linha 2: "DÁ CONTA DE ORGANIZAR" (entra aos 2.2s com destaque "DÁ CONTA")
    - Linha 3: "A SUA AGENDA?" (entra aos 3.5s com background highlight #FFA94D)
  - y = 720–1180: Card central elegante translúcido (Glassmorphism dark #1F2937ee) ilustrando a dor: "Horários cheios, mensagens acumuladas e risco de confusão".
  - y = 1320–1560: Karaoke oficial das palavras da pergunta.
- **Transição de saída:** Fade e push-out suave para a cena 1.

---

## Cena 1: O Problema & Comparativo de Custo (5.59s – 12.22s | frames 168 – 367)
- **Tipo / Composição:** c) Tela dividida / Comparativo Antes x Depois com cards sobrepostos.
- **Fala:** "Eu achava que só uma pessoa na recepção conseguia organizar nossos horários sem confusão."
- **Visual:** Foto `img_1.jpg` com pan horizontal sutil e overlay escuro.
- **Layout & Elementos:**
  - y = 175–250: Badge de Etapa `[ O PROBLEMA ]` em pill cinza com borda âmbar.
  - y = 260–420: Título forte: "SÓ UMA RECEPÇÃO DÁ CONTA?"
  - y = 480–1260: Dois cards comparativos dinâmicos (revelação escalonada):
    - Card 1 (topo, entra aos 6.5s na palavra "pessoa"): "Recepção Convencional"
      - Custo alto: R$ 2.500 / mês (fato oficial do briefing)
      - Atendimento com horário comercial limitado
      - Risco de conflito e mensagens perdidas
    - Card 2 (base, entra aos 9.2s na palavra "organizar"): "Agenda IA"
      - A partir de R$ 199 / mês
      - 24 horas por dia, 7 dias por semana
      - Zero confusão no WhatsApp
  - y = 1320–1560: Karaoke oficial sincronizado.
- **Transição de saída:** Deslize vertical suave (wipe) para o mockup de conversa.

---

## Cena 2: Como Funciona — Conversa WhatsApp no Celular 3D (11.87s – 20.79s | frames 356 – 624)
- **Tipo / Composição:** b) Celular 3D (rotateY sutil 12°, mockup largura 840px) com chat nativo animado balão a balão + selo "Simulação".
- **Fala:** "A tecnologia faz agendamentos automáticos 24 horas, confirmando e reagendando horários direto no WhatsApp."
- **Visual:** Fundo `img_2.jpg` com desfoque de 8px e véu #1F2937 a 80%.
- **Layout & Elementos:**
  - y = 170–240: Badge `[ COMO FUNCIONA ]` + Selo discreto `[ SIMULAÇÃO ]`
  - y = 250–380: Título: "AGENDAMENTO AUTOMÁTICO 24H"
  - y = 430–1280: Mockup de Celular iPhone / WhatsApp com fonte >= 32px e alto contraste:
    - Header do WhatsApp com avatar e nome "Agenda IA ✓"
    - Balão 1 (Cliente, entra aos 12.4s): "Olá, consigo remarcar meu corte de hoje para amanhã?"
    - Balão 2 (Agenda IA, entra aos 14.2s com 'digitando...'): "Olá! Tenho às 14h ou 16h amanhã. Qual prefere?"
    - Balão 3 (Cliente, entra aos 16.5s): "Pode ser às 14h."
    - Balão 4 (Agenda IA, entra aos 18.2s com 'digitando...'): "Perfeito! Horário reagendado para amanhã às 14h, sem conflito."
  - y = 1320–1560: Karaoke oficial sincronizado.
- **Transição de saída:** Zoom-through imersivo conectando ao dono da empresa.

---

## Cena 3: O Dono & Prova Real (20.44s – 28.45s | frames 613 – 853)
- **Tipo / Composição:** h) Vídeo real em tela cheia com câmera em movimento e texto exclusivo na faixa superior (y 150–420).
- **Fala:** "Minha recepção atende dia e noite sem conflito e sem duplo agendamento no WhatsApp."
- **Visual:** `<OffthreadVideo src={staticFile('dono_3.mp4')} muted />` com leve escala contínua (1.0 -> 1.05).
- **Regra Rosto Livre:** Apresentador ocupa o centro/base (cabeça em y ~450–1200). Zona y=150–420 100% livre para títulos.
- **Layout & Elementos:**
  - y = 180–250: Pill `[ O RESULTADO ]` em destaque #FFA94D.
  - y = 270–410: Título cinético animado sincronizado com a fala:
    - Aos 20.5s: "RECEPÇÃO DIA E NOITE"
    - Aos 24.0s (na fala "sem conflito e sem duplo agendamento"): "ZERO DUPLO AGENDAMENTO"
  - y = 1320–1560: Karaoke oficial sincronizado (posicionado sobre o peito/base y=1560, sem cobrir o rosto).
- **Transição de saída:** Cross-dissolve dinâmico para o cartão final.

---

## Cena 4: Cartão Final & CTA (28.10s – 32.10s | frames 843 – 963)
- **Tipo / Composição:** Cartão final profissional de alta conversão. Fundo `img_4.jpg` desfocado com véu escuro premium.
- **Fala:** "Chame a gente no direct." (Karaoke NÃO é exibido aqui).
- **Layout & Elementos:**
  - y = 300–450: Logo / Marca grande "AGENDA IA" com badge de verificação e glow âmbar.
  - y = 500–680: Frase de proposta de valor:
    - "Sua agenda organizada 24h no WhatsApp sem conflitos e sem confusão."
  - y = 740–860: Destaque de investimento oficial:
    - "A partir de R$ 199 / mês" (Planos acessíveis)
  - y = 960–1100: Botão pulsante contínuo (scale 1.0 -> 1.06 a cada 1.2s):
    - Background #FFA94D, texto #1F2937 extra bold: "CHAME NO DIRECT"
    - Efeito de brilho/shimmer passando ciclicamente.
  - y = 1180–1260: Identificador oficial: `@sintetizerisada`
- **Movimento:** Push contínuo da câmera até frame 963 sem congelar.
