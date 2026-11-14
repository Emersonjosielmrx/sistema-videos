# Plano de Edição — inovarecom_ia_20261113_135029
Produto: Hermes Call | Duração: 30.46s (914 frames a 30 fps) | Resolução: 1080x1920

## Identidade Visual e Safe Zone
- Cores: Primária #25D366 (Verde WhatsApp / Hermes Call), Apoio #075E54, Fundo Escuro #082E16, Destaque #25D366, Texto #FFFFFF / #121216.
- Tipografia: Montserrat (Black / Bold / SemiBold), todos os textos ≥ 32px.
- Safe zone rigorosa: 60px ≤ x ≤ 1020px; 150px ≤ y ≤ 1580px.
- Barra de progresso: y=150, altura 6px, preenchimento dinâmico 0% → 100% em #25D366.
- Karaokê: `Karaoke` da lib padrão, base=360 (y=1560), destaque #25D366, texto #121216, quebras por fala, oculto no cartão final.

---

## Cena 0 (0.00s a 4.71s | frames 0 a 141) — Tipo: Pergunta
- **Composição**: (a) Texto GIGANTE cinético + Tag de impacto sobre b-roll escurecido.
- **Background**: `img_0.jpg` com push-in sutil (scale 1.00 → 1.07) e vinheta escura suave.
- **Elementos Visuais**:
  - y=210: Badge pílula de abertura "DOR COMERCIAL" ou "PERGUNTA FREQUENTE" com ícone de alerta sonoro.
  - y=360 a 700: Título cinético escalonado em 3 linhas:
    - Linha 1: "SUA EQUIPE" (surge aos 0.3s com mola)
    - Linha 2: "NÃO DÁ CONTA" (surge aos 0.9s com destaque em vermelho/branco)
    - Linha 3: "DE LIGAR?" (surge aos 1.6s em marca-texto verde #25D366 e letras #121216)
  - y=850 a 1150: Card ilustrativo de alerta comercial: "Fila de espera acumulada" com ícone de telefone tocando e pulso de onda sonora.
- **Movimento**: Animação contínua de ondas de som e zoom no fundo.
- **Transição**: Wipe suave para a esquerda (0.3s).

---

## Cena 1 (4.36s a 10.83s | frames 131 a 325) — Tipo: Imagem / Gargalo
- **Composição**: (e) Pilha de cards de gargalo / notificações dinâmicas sobre foto em movimento.
- **Background**: `img_1.jpg` com pan horizontal suave e zoom (scale 1.02 → 1.08).
- **Elementos Visuais**:
  - y=210: Tag de contexto: "O GARGALO COMERCIAL".
  - y=340 a 460: Título da cena: "CENTENAS DE INTERESSADOS".
  - y=540 a 1180: Pilha de cards de chamadas não atendidas que entram sequencialmente:
    - Card 1 (entra aos 4.8s na fala "centenas"): "Lead Interessado #184 — Aguardando ligação há 3h" (status vermelho)
    - Card 2 (entra aos 6.8s na fala "meu time"): "Lead Interessado #185 — Aguardando ligação há 4h"
    - Card 3 (entra aos 7.8s na fala "não conseguia discar"): "Discar manualmente ❌ Tempo esgotado"
- **Movimento**: Cada card entra com spring e deslize lateral; contador de fila acumulando visualmente.
- **Transição**: Fade cruzado com zoom-in rápido (0.3s).

---

## Cena 2 (10.48s a 19.25s | frames 314 a 578) — Tipo: Veo / A Solução
- **Composição**: (b) Interface tech com chamadas ativas em grande escala + b-roll da equipe.
- **Background**: `video_2.mp4` em loop/reprodução fluida com overlay translúcido verde escuro (#082E16 a 75%).
- **Elementos Visuais**:
  - y=200: Tag de topo: "A SOLUÇÃO IA • HERMES CALL".
  - y=320 a 430: Título: "LIGAÇÕES WHATSAPP EM GRANDE ESCALA".
  - y=520 a 1220: Painel de controle Hermes Call:
    - Topo do painel: Status "DISPAROS AUTOMÁTICOS ATIVOS" com luz verde pulsante.
    - Bloco 1 (entra aos 11.8s na fala "dispara"): "Chamadas simultâneas via WhatsApp" com badge "Voz Real & Clonada".
    - Bloco 2 (entra aos 14.4s na fala "grande escala"): Gráfico de ondas de áudio ativas e contador dinâmico de conexões.
    - Bloco 3 (entra aos 15.5s na fala "atendimento inteligente 24h"): Card com selo "Atendimento Inteligente 24h" e ícone de IA.
- **Movimento**: Barras de onda de áudio animadas com Math.sin, indicador de chamadas ativas piscando.
- **Transição**: Slide lateral dinâmico.

---

## Cena 3 (18.90s a 26.92s | frames 567 a 808) — Tipo: Dono / O Resultado
- **Composição**: (h) Vídeo real do Dono em tela cheia com grafismos exclusivamente na faixa superior (y=160 a 440).
- **Background**: `dono_3.mp4` em tela cheia (objectFit cover), muted, sincronizado com a narração oficial.
- **Proteção do apresentador**:
  - Cabeça do apresentador inicia em y≈480. NENHUM elemento gráfico entre y=450 e y=1300.
  - Rosto e mãos 100% livres de cards ou divisórias.
- **Elementos Visuais (Apenas no topo, y=160 a 430)**:
  - y=190: Tag de autoridade: "CASO REAL • O RESULTADO".
  - y=270: Card moderno e compacto com fundo fosco escuro:
    - "ESCALA TOTAL NO WHATSAPP"
    - Subtítulo: "Sem sobrecarregar a equipe comercial"
- **Base (y=1400 a 1560)**:
  - Legenda Karaokê perfeitamente posicionada abaixo do peito do apresentador.
- **Movimento**: Push sutil de câmera (1.00 → 1.05) no vídeo do apresentador.
- **Transição**: Zoom-through limpo para o cartão final.

---

## Cena 4 (26.57s a 30.46s | frames 797 a 914) — Tipo: Cartão Final / CTA
- **Composição**: Cartão final vivo, minimalista e de alto impacto de conversão.
- **Background**: `img_4.jpg` com desfoque elegante (blur 18px), gradiente escuro da marca (#082E16 a 90%) e zoom contínuo.
- **Elementos Visuais**:
  - y=380: Logo / Nome da marca em destaque: "HERMES CALL" (fonte 76px, branco + verde neon #25D366).
  - y=510: Tag de proposta de valor: "Ligações WhatsApp com IA 24h".
  - y=620: Frase síntese do produto: "Atenda, ligue e venda sem parar."
  - y=880 a 1040: Botão de Ação CTA Principal (Pulsando continuamente 1.00 → 1.05):
    - Texto exato da locução: "CHAME NO DIRECT"
    - Ícone de direct / mensagem.
    - Efeito de brilho (sheen) percorrendo o botão a cada 1.5s.
  - y=1180: Identificador oficial: "@inovarecom.ia".
- **Sem karaokê**: O karaokê não é exibido no cartão final conforme regras de agência.
