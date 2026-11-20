# Plano de Edição Corrigido — agentesdeia_ia_20261118_210725

## Informações Gerais
- **Produto**: Agente Pessoal IA (Marca: Agentes de IA)
- **Duração**: 31.52 s (946 frames a 30 fps)
- **Cores**: Marca/Destaque: `#10B981`, Apoio/Fundo: `#111827`, Texto: `#FFFFFF`
- **Arroba**: `@agentesdeia.ia`
- **Áudio**: Narração completa em `narracao.mp3` + Trilha em `trilha.mp3`

---

## Safe Zones e Regras Visuais
- **Zona Segura Vertical**: y = 150 a y = 1580
- **Margens Laterais**: x = 60 a x = 1020 (respiro lateral ≥ 60 px; botão CTA com 820 px tem 130 px de respiro de cada lado)
- **Zona Superior (Títulos / Badges)**: y = 150 a y = 410 (com headroom de ~110-130 px até a cabeça do apresentador graças ao enquadramento rebaixado)
- **Zona Central**: y = 450 a y = 1380 (rosto do apresentador nas cenas de fala; overlay de mockup de chat em Cena 2 e conversão no cartão final)
- **Zona Inferior (Karaokê)**: base = 445 px do fundo da tela (base da caixa em y = 1475 px, 100% dentro da safe zone do Reels e ≥ 65 px acima de y=1540)
- **Piso Tipográfico**: Todos os textos ≥ 28–32 px (títulos 44–56 px, mensagens de chat 32 px, subtítulos 28 px semibold)
- **Movimento Contínuo**: Microanimações (shimmer sweep contínuo, pulso de escala suave 1.00 a 1.03 no botão final, áudio wave e pulso radial em Cena 0)

---

## Estrutura das Cenas e Correções Aplicadas

### Cena 0: Pergunta do Cliente (0.0s – 5.03s | frames 0 – 151)
- **Tipo**: `pergunta` | **Composição**: a / d (Notificação de Dúvida de Cliente + Apresentador visível no fundo)
- **Fala**: "Dá para receber a pesquisa pronta enquanto cuido do meu negócio?"
- **Fundo**: Apresentador visível desde o segundo 0 com iluminação radial pulsante esmeralda e push-in cinematográfico.
- **Pergunta Completa**: Exibida logo no frame 0 diagramada como card de pergunta real com pop elástico de overshoot no termo "PESQUISA PRONTA?".
- **Transição de Retenção**: Aos 1.6s (frame 48), o card central sobe suavemente para a barra superior e o apresentador é revelado com total nitidez, eliminando o aspecto de slide estático.
- **Paleta**: Card complementar amarelo removido para foco exclusivo na dúvida com a paleta institucional verde/petróleo.
- **Chunking da Legenda**: Segmentação otimizada ("DÁ PARA RECEBER A PESQUISA PRONTA" / "ENQUANTO CUIDO DO MEU NEGÓCIO") eliminando termos órfãos.

### Cena 1: O Dono — O Problema (4.68s – 12.86s | frames 140 – 386)
- **Tipo**: `dono` | **Composição**: h (Vídeo real com plano médio + Headroom generoso)
- **Vídeo**: `dono_1.mp4` muted com push-in suave (1.02x -> 1.06x) e enquadramento rebaixado em 45 px para garantir headroom confortável de ~110 px abaixo dos cards.
- **Top Cards**: 01 • O PROBLEMA com subtítulos em 28 px semibold de alto contraste.
- **Legenda Karaokê**: Base em y=1475 px e chunking preservando "FICAVA PARADO ESPERANDO." sem omissão da locução final.

### Cena 2: O Dono — Como Funciona (12.51s – 20.09s | frames 375 – 603)
- **Tipo**: `dono` | **Composição**: h + Mockup Dinâmico de Demonstração (celular 880 px)
- **Vídeo**: `dono_2.mp4` muted com punch-in de escala (1.14x -> 1.18x) para quebra do monólogo e plano fechado dinâmico.
- **Demonstração do Produto**: Ao pronunciar "ao Agente Pessoal IA, e ele pesquisa por mim", entra overlay de mockup de smartphone com simulação visual de chat estilo WhatsApp (selo obrigatório "Simulação"):
  - Mensagem do usuário solicitando a pesquisa de mercado;
  - Resposta instantânea estruturada do Agente Pessoal IA entregando as fontes verificadas e o relatório pronto.
- **Headroom**: Apresentador rebaixado em 48 px.

### Cena 3: O Dono — O Resultado (19.74s – 27.92s | frames 592 – 838)
- **Tipo**: `dono` | **Composição**: h (Vídeo real alternando para plano médio 1.06x -> 1.10x)
- **Vídeo**: `dono_3.mp4` com corte inicial ajustado para `startFrom={6}` (0.2s), garantindo apresentador com olhos 100% abertos e olhar firme e confiante para a lente.
- **Top Cards**: 03 • O RESULTADO ("Tarefa Concluída" / "Foco no Crescimento") com subtítulos em 28 px semibold.
- **Legenda Karaokê**: Chunking rebalanceado ("E USO A MANHÃ PARA CUIDAR" / "DO QUE FAZ A EMPRESA CRESCER.") sem viúva órfã.

### Cena 4: Cartão Final / CTA (27.57s – 31.52s | frames 827 – 946)
- **Tipo**: `cartao` | **Composição**: Conversão Mobile Escalonada
- **Hierarquia Escalonada**: Entrada em stagger — Topo/Marca (f0) -> Card de tarefas (f8) -> Tags Pesquisa/Agendamento/Follow-up (f16, f23, f30) -> Botão CTA com bounce (f38) -> @agentesdeia.ia (f46).
- **Largura do Botão**: 820 px (garantindo 130 px de respiro de cada margem lateral, respeitando com folga a safe zone).
- **Microanimação Contínua**:
  - Pulso suave contínuo de escala no botão (1.00 a 1.03 em loop suave);
  - Shimmer sweep contínuo correndo da esquerda para a direita ao longo de todo o botão;
  - Respiração contínua dos cards e zoom do fundo.
- **Safe Zone**: Terço inferior perfeitamente limpo para interface de Reels.
