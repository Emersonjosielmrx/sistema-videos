# Plano de Edição — disparoemmassa_ia_20261111_135247

## Produto & Marca
- **Marca / Produto:** Disparo em Massa IA (`@disparoemmassa.ia`)
- **Cores:** Marca/Destaque `#22C55E` | Apoio/Fundo Escuro `#111827` | Texto sobre marca `#121216`
- **Duração:** 29.90s (897 frames @ 30fps)
- **Fatos permitidos:**
  1. Disparo em massa inteligente, rotação de instâncias, cartão de aniversário e envio de Pix
  2. Disparo em massa inteligente no WhatsApp
  3. Envie campanhas para milhares de contatos no WhatsApp com rotação de números, mensagens personalizadas e envio automático.

---

## Estrutura de Cenas (4+ composições diferentes, zero repetição seguida)

### Cena 0 — Pergunta (0.00s a 4.76s)
- **Composição:** **(a) Texto GIGANTE cinético + Foto viva com foco preservado**
- **Foto (`img_0.jpg`):** Mulher sorrindo em loja (rosto em y=200..580). Zoom suave contínuo (1.0 -> 1.08) + leve pan.
- **Posicionamento (Safe Zone 150–1580, Rosto livre):**
  - Topo (`y=165`): Pílula de marca `DISPARO EM MASSA IA` + indicador de áudio/status.
  - Abaixo do peito (`y=700..1240`): Card glassmorphism escuro (`rgba(17,24,39,0.92)`) com borda `#22C55E`, contendo a pergunta exata da fala: **"Consigo falar com toda a minha base sem mandar um por um?"** com palavras acendendo sincronizadas:
    - `0.31s`: "Consigo falar"
    - `1.34s`: "com toda a minha base" (destaque verde `#22C55E`)
    - `2.24s`: "sem mandar um por um?" (pílula alerta)
  - Aos `2.45s`: entra o selo fixo do `gancho_tela`: **"Sem copiar e colar mensagens"** logo abaixo (`y=1150`).
- **Transição:** Wipe diagonal energético para a Cena 1.

### Cena 1 — O Problema (4.41s a 10.78s)
- **Composição:** **(c) Tela dividida Antes x Depois / Painel de Dor vs Automação + Foto em movimento**
- **Foto (`img_1.jpg`):** Homem de perfil à esquerda digitando no notebook à direita. Pan contínuo e zoom.
- **Sincronia com a fala:** *"Eu cansava de passar horas copiando e colando avisos para cada cliente no WhatsApp."*
  - `4.41s`: Rótulo no topo (`y=165`): `O PROBLEMA` + título forte `HORAS COPIANDO E COLANDO` (`y=235`).
  - `5.01s` ("cansava" / "horas"): Card superior esquerdo/centro (`y=820..1040`, deixando o rosto do homem em y=250..680 100% livre): Mostra o trabalho manual repetitivo (`Ctrl+C / Ctrl+V` + fila manual `Cliente 1... Cliente 2...` travada em vermelho `#EF4444`).
  - `6.29s` ("copiando e colando avisos"): Linha divisória varre e empilha janelas de "Aviso copiado" repetidas.
  - `8.00s` ("para cada cliente no WhatsApp"): Card comparativo à direita (`Envio Manual: Um por um` vs `Disparo em Massa IA: Base inteira`) pulsando.
- **Transição:** Zoom-through / slide 3D para o celular da Cena 2.

### Cena 2 — Como Funciona (10.43s a 19.27s)
- **Composição:** **(b) Celular inclinado em 3D de um lado + Etapas 1-2-3 sincronizadas**
- **Foto (`img_2.jpg`):** Mulher em cafeteria, enquadrada e deslocada para preservar ambiência viva com zoom contínuo.
- **Sincronia com a fala:** *"Com o Disparo em Massa IA, eu configuro mensagens personalizadas com envio automático e rotação de números."*
  - Topo (`y=160..310`): Rótulo `COMO FUNCIONA` + 3 pílulas de etapas que acendem **uma por uma** no milissegundo da fala:
    1. `13.45s` ("configuro mensagens personalizadas"): Etapa 1 **Mensagens Personalizadas** acende em `#22C55E`.
    2. `15.73s` ("envio automático"): Etapa 2 **Envio Automático** acende em `#22C55E`.
    3. `16.84s` ("rotação de números"): Etapa 3 **Rotação de Números** acende em `#22C55E`.
  - Centro (`y=340..1240`): Mockup grande de smartphone (`width: 900px`, leve inclinação 3D dinâmica) com cabeçalho WhatsApp + selo `Simulação` (>= 32px) e indicador de instância alternando (`Instância #01 -> #02 -> #03`).
  - Balões da `conversa` do briefing entrando um a um (todas as fontes >= 32px):
    - `11.2s`: Empresa (esquerda): *"Olá, Mariana! Preparamos uma novidade especial para você hoje na loja."*
    - `14.2s`: Cliente (direita): *"Oi! Que ótimo, quero ver as opções disponíveis."*
    - `16.2s`: Indicador *"digitando..."* -> `16.8s`: Empresa (esquerda): *"Vou te mostrar o catálogo e também enviamos a chave Pix por aqui."*
- **Transição:** Slide vertical com máscara para a Cena 3.

### Cena 3 — O Resultado (18.92s a 26.30s)
- **Composição:** **(f) + (g) Foto recortada em janela estilizada + Grade/Checklist de escala e benefícios com ✓ animado**
- **Foto (`img_3.jpg`):** Como `img_3.jpg` é o mesmo arquivo de `img_0.jpg`, aplicamos enquadramento em card/arco superior + fundo escuro técnico animado em grid da marca, criando um cenário visualmente inédito e dinâmico.
- **Sincronia com a fala:** *"Hoje eu envio campanhas para milhares de contatos no WhatsApp através do disparo em massa inteligente."*
  - Topo (`y=165`): Rótulo `O RESULTADO` + Título `ALCANCE MILHARES DE CONTATOS`.
  - `20.15s` ("campanhas para milhares de contatos"): Barra de disparo em massa preenchendo continuamente + fluxo de avatares de contatos recebendo campanha (`✓ Enviado`).
  - `22.16s` a `25.00s`: Grade de 4 recursos oficiais do briefing com ✓ animado acendendo em sequência:
    1. **Disparo em Massa Inteligente**
    2. **Rotação de Instâncias**
    3. **Envio de Pix no WhatsApp**
    4. **Cartão de Aniversário**
- **Transição:** Fade + scale punch para o Cartão Final.

### Cena 4 — Cartão Final / CTA (25.95s a 29.90s)
- **Composição:** Cartão final de conversão vivo (sem Karaoke)
- **Fundo (`img_4.jpg`):** Desfocado com zoom contínuo + véu escuro `#111827` + partículas/auras `#22C55E` em movimento até o último frame.
- **Elementos (Safe Zone 150–1580):**
  - Badge + Nome da marca grande em branco e verde: **DISPARO EM MASSA IA** (`y=320`).
  - Frase do produto (`y=580`): *"Disparo em massa inteligente com envio automático e rotação de números no WhatsApp"*.
  - Botão CTA principal pulsando com brilho passando (`y=940`): **"CHAME A GENTE NO DIRECT"** (espelhando `convite_voz`).
  - Handle (`y=1180`): **`@disparoemmassa.ia`** grande e legível.
