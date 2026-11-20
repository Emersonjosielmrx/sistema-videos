# Plano de Edição — disparoemmassa_ia_20261118_102227
Produto: Disparo em Massa IA | Duração: 31.53 s (946 frames @ 30 fps)

## Visão Geral de Estilo e Motion Design
- Linha visual: Dark tech premium (fundo escuro #111827, verde WhatsApp #22C55E de destaque, branco puro #FFFFFF).
- Tipografia: Montserrat (Black 900 para títulos e karaokê, Bold 700 para tags e botões, SemiBold 600 para textos secundários). Tamanho mínimo >= 32px em todos os textos.
- Movimento contínuo: câmera em drift/zoom suave em 100% dos frames (0.0s a 31.53s).
- Zonas seguras: todos os elementos essenciais entre y=150 e y=1580, margens laterais de 60px.
- Legenda Karaokê: componente oficial `Karaoke` com base=360 (y=1560), quebra por cena garantida, ausente no cartão final.

---

## Cena 0 (0.00s – 4.21s / frames 0 – 126) — A Pergunta (Dor)
- **Tipo:** `pergunta`
- **Composição:** a) Texto GIGANTE tela cheia sobre fundo vivo escurecido com grafismos e partículas.
- **Fala:** "Seu cliente compra uma vez e some da loja?"
- **Fundo:** `img_0.jpg` com push-in suave (scale 1.05 → 1.15) + vinheta radial escura + partículas verdes flutuantes.
- **Elementos Visuais:**
  - Tag superior (y=170): `[ RETENÇÃO DE CLIENTES ]` em cápsula escura translúcida com ponto pulsante.
  - Texto Cinético Principal (y=520 a 900):
    - 0.0s – 1.6s (palavras 0.32s a 1.73s): "SEU CLIENTE COMPRA" em branco + destaque "UMA VEZ" em marca-texto verde `#22C55E`.
    - 1.7s – 4.2s (palavras 1.75s a 2.75s): "...E SOME DA LOJA?" com a palavra "SOME" em badge vermelho vibrante `#EF4444` animado com mola e efeito de desaparecimento/fantasma.
  - Ícone Central/Dor: Avatar de cliente com sacola de compras que se desvanece no ar aos 1.87s (sincronizado com "some").
- **Transição para Cena 1:** Fade-out rápido dos textos (frames 116-126) com corte contínuo para o apresentador.

---

## Cena 1 (3.86s – 11.89s / frames 116 – 357) — O Problema (Dono)
- **Tipo:** `dono`
- **Composição:** h) Vídeo cheio do apresentador (`dono_1.mp4`) com texto de apoio exclusivamente no topo alto (y=160 a 270).
- **Fala:** "Eu esquecia de manter contato no pós-venda e muitos clientes deixavam de comprar novamente."
- **Vídeo:** `<OffthreadVideo src={staticFile('dono_1.mp4')} muted />` com enquadramento protegido (transform: translateY(70px) scale(1.05)) para garantir respiro >= 40px acima da cabeça do apresentador (cabeça abaixo de y=280).
- **Elementos no Topo:**
  - y=165: Tag de contexto `[ O PROBLEMA ]` em cápsula com indicador âmbar `#F59E0B`.
  - Manchete cinética sincronizada com a fala:
    - 5.5s – 8.4s ("Eu esquecia de manter contato no pós-venda"): "ESQUECIA DO CONTATO" em tipografia bold 44px com realce sutil.
    - 8.5s – 11.8s ("muitos clientes deixavam de comprar novamente"): "CLIENTES NÃO VOLTAVAM" em alerta suave.
  - Karaokê: ativo na base (y=1560) sobre a faixa da bancada inferior.
- **Transição para Cena 2:** Wipe suave / zoom perspective para a tela de conversa.

---

## Cena 2 (11.54s – 20.50s / frames 346 – 615) — Como Funciona (WhatsApp em Ação)
- **Tipo:** `conversa`
- **Composição:** b) Celular moderno em perspectiva 3D leve (rotateY -8° a +4°, rotateX 3°) ocupando o centro focal (y=380 a 1400) com conversa real animada.
- **Fala:** "A ferramenta programa mensagens personalizadas e envia cartão de aniversário automático direto no WhatsApp de cada cliente."
- **Fundo:** `img_2.jpg` com pan lento e círculos concêntricos de sinal WhatsApp em baixa opacidade.
- **Top Bar (y=165):** Tag `[ COMO FUNCIONA ]` + "DISPARO EM MASSA IA" em verde neon.
- **Mockup do Smartphone (largura 840px, design mobile nativo):**
  - Barra de status WhatsApp: Nome "Marcelo Santos (Cliente)", status "online", avatar e ícones de chamada.
  - Selo obrigatório discreto: "Simulação" (font-size 32px, contraste adequado).
  - Balão 1 (Empresa, entra aos 12.3s após 'digitando...'): "Olá, Marcelo! Passando para checar se deu tudo certo com o seu pedido."
  - Balão 2 (Cliente, entra aos 14.2s): "Chegou perfeito, estou usando bastante! 👏"
  - Balão 3 (Empresa com Cartão de Aniversário, entra aos 15.6s na palavra 'aniversário'):
    - Texto: "Que ótimo! Feliz aniversário adiantado, enviamos um cartão especial para comemorar. 🎁"
    - Card interno ilustrado: "VOUCHER ESPECIAL DE ANIVERSÁRIO" com selo dourado e código de desconto.
  - Badge flutuante lateral (entra aos 17.5s em 'WhatsApp de cada cliente'): "✓ Envio Automático" com ícone de disparo.
  - Todas as fontes dentro do celular >= 32px.
- **Transição para Cena 3:** Deslize elegante para a esquerda revelando o apresentador.

---

## Cena 3 (20.15s – 27.93s / frames 604 – 838) — O Resultado (Dono)
- **Tipo:** `dono`
- **Composição:** h) Vídeo do apresentador (`dono_3.mp4`) com enquadramento natural (apresentador atrás do balcão, cabeça em y=550).
- **Fala:** "Hoje cuido do relacionamento com envio automático e mantenho meus contatos sempre próximos."
- **Vídeo:** `<OffthreadVideo src={staticFile('dono_3.mp4')} muted />` com câmera em push-in constante (scale 1.0 → 1.05).
- **Elementos no Topo Livre (y=160 a 480):**
  - y=165: Tag `[ O RESULTADO ]` em cápsula verde `#22C55E`.
  - Título Principal Dinâmico:
    - 20.2s – 23.3s: "RELACIONAMENTO ATIVO"
    - 23.4s – 27.5s: "ENVIO AUTOMÁTICO NO WHATSAPP"
  - Cards de Benefícios dos Fatos (entrando aos 23.5s e 25.0s nas laterais superiores):
    - Card 1: "✓ Rotação de números"
    - Card 2: "✓ Mensagens personalizadas"
    - Sem inventar dados, respeitando 100% o briefing.
- **Transição para Cena 4:** Transição de impacto com zoom e blur para o encerramento.

---

## Cena 4 (27.58s – 31.53s / frames 827 – 946) — Cartão Final (CTA Vivo)
- **Tipo:** `cartao`
- **Composição:** Encerramento premium de alta conversão, sem Karaokê.
- **Fala:** "Chame a gente no direct."
- **Fundo:** `img_4.jpg` desfocada + véu escuro degradê em `#111827`.
- **Elementos Visuais:**
  - Topo (y=320): Ícone de disparo com balão WhatsApp + Faísca IA em verde `#22C55E` com leve flutuação.
  - Marca Principal (y=440): "Disparo em Massa IA" em tipografia imponente 64px branco e verde.
  - Frase de Valor (y=570): "Disparo inteligente no WhatsApp com mensagens personalizadas." (fatos reais).
  - Botão CTA Pulsante (y=840 a 980):
    - Texto: "CHAME NO DIRECT" (corresponde a 100% da fala `convite_voz` e `convite`).
    - Animação: pulso contínuo (scale 1.00 → 1.07 em loop suave) + efeito shimmer/brilho que varre o botão a cada 1.5s.
  - Identificador da Marca (y=1120): Arroba oficial `@disparoemmassa.ia` com ícone de Instagram/Direct.
  - Selo de Confiança (y=1220): "Envio inteligente • Rotação de instâncias".
