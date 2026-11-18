# Plano de Edição — VPS Blindada (`vpsblindada_ia_20261116_094759`)

## Fatos e Identidade
- Produto: VPS Blindada
- Cores: Marca `#0EA5E9`, Fundo `#111827`, Destaque `#0EA5E9`, Texto `#FFFFFF`
- Tipografia: Montserrat (Bold / Black / ExtraBold)
- Duração total: 31.55 s (947 frames a 30 fps)
- Zonas Seguras: y=150 a y=1580, margens x=60 a x=1020

---

## Cena 0 — 0.00s a 4.91s (Frames 0 a 147)
- **Tipo**: `pergunta`
- **Fala**: "Seu sistema caiu e você só ficou sabendo pelo cliente?"
- **Composição**: `a` — Texto cinético de alto impacto tela cheia sobre foto escurecida com vinheta e zoom contínuo.
- **Visual**: `img_0.jpg` com push-in de câmera (scale 1.0 -> 1.08).
- **Entradas e Sincronização**:
  - 0.0s: Overlay escuro com vinheta + Barra de progresso no topo (y=155).
  - 0.2s: Badge de alerta no topo (y=180): "⚠️ ALERTA DE INSTABILIDADE".
  - 0.3s - 1.4s (Palavras "Seu sistema caiu"): Título cinético gigante entra com mola forte no centro superior (y=320): "SEU SISTEMA CAIU?". Palavra "CAIU" em vermelho/laranja de alerta pulsante.
  - 1.8s - 3.5s (Palavras "e você só ficou sabendo pelo cliente?"): Card estilo notificação simulada entra com deslize e pop em y=580: "💬 Cliente no WhatsApp: 'O sistema tá fora do ar de novo?'".
  - 3.6s: Selo fixo com `gancho_tela` "Sua VPS está saudável?" surge em y=740.
  - Karaokê ativo na base (y=1560) com palavras sincronizadas.
- **Transição**: Saída rápida com flash/slide aos 4.56s.

---

## Cena 1 — 4.56s a 12.59s (Frames 137 a 378)
- **Tipo**: `dono`
- **Fala**: "Eu olhava para o meu servidor e não sabia dizer se estava tudo certo. Faltavam dados para decidir."
- **Rótulo**: "O problema"
- **Composição**: `h` — Vídeo do dono em tela cheia com câmera em movimento contínuo (scale 1.0 -> 1.05), rosto 100% livre e desimpedido.
- **Visual**: `dono_1.mp4` muted, preenchendo a tela. Rosto entre y=350 e y=1050 preservado.
- **Entradas e Sincronização**:
  - 4.56s: Tag superior "O PROBLEMA" entra em y=180.
  - 4.8s - 9.4s: Card de contexto superior (y=250 a 400): "SERVIDOR NO ESCURO" + "Sem visibilidade real do status".
  - 9.6s (no milissegundo em que a voz diz "Faltavam dados para decidir"): Desmonte suave do card anterior e entrada do novo card superior: "FALTAVAM DADOS PARA DECIDIR" com indicador de falta de métricas.
  - Karaokê sincronizado na base (y=1560), respeitando respiro do tronco.
- **Transição**: Varredura fluida lateral para a cena 2 aos 12.24s.

---

## Cena 2 — 12.24s a 20.12s (Frames 367 a 604)
- **Tipo**: `veo`
- **Fala**: "Junto com a VPS pronta, você recebe relatórios claros e o robô Sentinela vigiando os erros por você."
- **Rótulo**: "Como funciona"
- **Composição**: `e` — Pilha de cards tecnológicos entrando em cascata sobre o b-roll em movimento contínuo.
- **Visual**: `video_2.mp4` muted com push-in de câmera (1.02 -> 1.10).
- **Entradas e Sincronização**:
  - 12.24s: Tag superior "COMO FUNCIONA" em y=180.
  - 13.0s ("VPS pronta"): Card 1 entra em y=260: "🚀 VPS Pronta & Blindada" (Docker • Portainer • Traefik).
  - 15.0s ("relatórios claros"): Card 2 entra em y=430: "📊 Relatórios Claros de Saúde" (Métricas em Tempo Real • Diagnóstico).
  - 16.5s ("o robô Sentinela vigiando os erros por você"): Card 3 entra em y=600: "🤖 Bot Sentinela Ativo" (Vigiando erros por você • Alertas automáticos).
  - Pulso suave de monitoramento em tempo real nos cards até o fim da cena.
  - Karaokê sincronizado na base (y=1560).
- **Transição**: Zoom-through luminoso para a cena 3 aos 19.77s.

---

## Cena 3 — 19.77s a 27.95s (Frames 593 a 839)
- **Tipo**: `dono`
- **Fala**: "Hoje eu leio o relatório e sei a real situação da minha infraestrutura. Decido com segurança."
- **Rótulo**: "O resultado"
- **Composição**: `h` — Vídeo do dono em tela cheia com push-in (1.0 -> 1.05), rosto e expressão de confiança 100% livres.
- **Visual**: `dono_3.mp4` muted, elementos mantidos exclusivamente no topo (y=170 a 420) e karaokê na base (y=1560).
- **Entradas e Sincronização**:
  - 19.77s: Tag superior "O RESULTADO" em y=180 com glow verde/azul.
  - 20.6s ("Hoje eu leio o relatório e sei a real situação..."): Card superior entra em y=250: "Visibilidade Total da Infraestrutura" com status "Status: Saudável e Monitorado".
  - 26.0s ("Decido com segurança"): Badge de reforço de decisão entra em y=370: "🛡️ Decisão com Segurança".
  - Karaokê sincronizado na base (y=1560).
- **Transição**: Corte fluido para o cartão final aos 27.60s.

---

## Cena 4 — 27.60s a 31.55s (Frames 828 a 947)
- **Tipo**: `cartao`
- **Fala**: "Chame a gente no direct."
- **Composição**: Cartão final de alta conversão motion design.
- **Visual**: `img_4.jpg` desfocada (blur 16px) com overlay escuro da marca (`#111827`) e partículas sutis.
- **Sem Karaokê** (apenas CTA em destaque conforme regras).
- **Entradas e Movimento**:
  - 27.6s: Fade-in com escala suave do logotipo: "VPS BLINDADA" em destaque com ícone de escudo cibernético.
  - 28.0s: Frase síntese do produto (fatos permitidos): "Sua VPS pronta, segura e com backup automático."
  - 28.2s: Pílula com stack: "Docker • Portainer • Traefik • Bot Sentinela".
  - 28.4s: Botão CTA pulsante com a exata ação: "CHAME NO DIRECT" com escala de pulso (1.0 a 1.06 contínua até o último frame) e efeito de reflexo/brilho correndo.
  - 28.8s: Handle oficial centralizado: "@vpsblindada.ia".
