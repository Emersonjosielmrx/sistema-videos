# Plano de Edição — Inovare CRM (`inovarecrm_20261122_052621`)

## Dados Gerais
- **Produto**: CRM Chatwoot IA (Inovare CRM)
- **Duração**: 30.69 s (921 frames @ 30 fps)
- **Paleta de Cores**:
  - Marca / Destaque: `#0284C7` (Azul Tecnológico)
  - Apoio / Fundo Escuro: `#0F172A` (Slate Navy Profundo)
  - Alerta / Dor: `#EF4444` (Vermelho vivo)
  - Sucesso / Validação: `#10B981` (Verde esmeralda)
  - Texto Claro: `#FFFFFF` / `#F8FAFC`
- **Áudio**:
  - `narracao.mp3`: volume 1.0 contínuo
  - `trilha.mp3`: volume 0.10 com fala, fade in 0.5s no início, fade out 1.5s no encerramento

---

## Estrutura de Cenas & Composições

### Cena 0: Pergunta & Gancho da Dor (0.00s a 4.79s — frames 0 a 144)
- **Tipo**: `pergunta`
- **Composição**: **(a) Texto GIGANTE tela cheia sobre foto com câmera dinâmica**
- **Mídia**: `img_0.jpg` (homem em frente ao notebook, câmera em push-in 1.05 -> 1.15, dimming suave com gradiente escuro protetor)
- **Elementos Visuais**:
  - y=152: Barra de progresso contínua.
  - y=180: Badge "ATENÇÃO EMPREENDEDOR" com pulso sutil e ponto vermelho pulsante.
  - y=270: Gancho em destaque no topo: *"Seu CRM parece engessado?"* (0.3s a 4.79s).
  - y=420–780: Título cinético escalonado sincronizado com as palavras da fala:
    - 0.3s ("Cansado de adaptar seu trabalho"): Surge bloco tipográfico bold 54px.
    - 2.0s ("a ferramentas"): Destaque em caixa cinza/vermelha.
    - 2.6s ("travadas?"): Efeito impacto / shake sutil com pílula vermelha `#EF4444` e ícone de cadeado/bloqueio.
  - y=1320–1560: Legenda Karaokê pronta (`base={360}`).
- **Transição para Cena 1**: Flash/Wipe suave aos ~4.4s.

### Cena 1: O Dono Fala — O Problema (4.44s a 12.45s — frames 133 a 374)
- **Tipo**: `dono`
- **Composição**: **(h) Vídeo cheio com câmera em movimento e texto exclusivo no alto**
- **Mídia**: `dono_1.mp4` via `<OffthreadVideo muted />` com zoom contínuo 1.0 -> 1.06.
- **Proteção do Rosto**:
  - O apresentador tem a cabeça entre y=500 e y=1300.
  - Todos os elementos gráficos ficam estritamente restritos à faixa superior: y=150 a y=440 (respiro > 60px acima da cabeça).
- **Elementos Visuais**:
  - y=180: Tag numerada animada: `01 • O PROBLEMA` (azul escuro + borda `#0284C7`).
  - y=250–390: Cards dinâmicos no topo sincronizados com a fala:
    - 4.4s–8.2s: *"SISTEMAS PRONTOS NÃO SE ENCAIXAM"* com badge de alerta "ENGESSADO".
    - 8.5s–12.0s: *"NENHUM SE ENCAIXAVA NO MEU PROCESSO"* destacando a frustração operacional.
  - y=1560: Legenda Karaokê sincronizada sobre o peito/camisa do dono.
- **Transição para Cena 2**: Zoom-in com fade sutil aos ~12.1s.

### Cena 2: B-Roll & A Solução Técnica (12.10s a 19.27s — frames 363 a 578)
- **Tipo**: `veo`
- **Composição**: **(e) Vídeo b-roll em movimento + pilha de cards de solução técnica na lateral**
- **Mídia**: `video_2.mp4` via `<OffthreadVideo muted />` (profissional trabalhando ao laptop, push-in contínuo 1.03 -> 1.12).
- **Elementos Visuais**:
  - y=180: Tag de etapa: `02 • COMO FUNCIONA` (verde/ciano).
  - y=240: Título de solução: *"SOLUÇÃO SOB MEDIDA"* (branco bold 50px).
  - y=340–1150: Pilha de cards técnicos entrando progressivamente na lateral direita (x=480 a 1000):
    - 12.6s: Card 1 — *"Solução Sob Medida"* com ícone de engrenagem/ajuste.
    - 14.9s ("Chatwoot"): Card 2 — *"Base Chatwoot Integrada"* (badge de tickets & atendimento).
    - 15.7s ("Inteligência Artificial"): Card 3 — *"Automação com IA"* com chip de tecnologia ativo.
    - 17.4s ("Sua rotina"): Badge verde *"100% Adaptado à Sua Rotina"*.
  - y=1560: Legenda Karaokê sincronizada.
- **Transição para Cena 3**: Deslize dinâmico aos ~18.9s.

### Cena 3: O Dono Fala — O Resultado Real (18.92s a 27.10s — frames 568 a 813)
- **Tipo**: `dono`
- **Composição**: **(h) Vídeo cheio com câmera em movimento e métricas/resultado no alto**
- **Mídia**: `dono_3.mp4` via `<OffthreadVideo muted />` com zoom contínuo 1.0 -> 1.06.
- **Proteção do Rosto**:
  - Cabeça do apresentador entre y=550 e y=1350.
  - Elementos estritamente entre y=150 e y=450.
- **Elementos Visuais**:
  - y=180: Tag numerada: `03 • O RESULTADO` (fundo slate, borda verde).
  - y=250–420: Destaques animados de sucesso:
    - 19.6s–21.7s: *"HISTÓRICO COMPLETO"* (ícone de arquivo/base centralizada + check verde).
    - 22.1s–23.6s: *"SUPORTE INTEGRADO"* (ícone de atendimento + sincronia).
    - 24.5s–26.5s: *"NO FORMATO QUE O TIME PRECISA"* (card comemorativo de produtividade).
  - y=1560: Legenda Karaokê sincronizada.
- **Transição para Cena 4**: Fade escuro com foco de luz para o cartão final.

### Cena 4: Cartão Final de Conversão (26.75s a 30.69s — frames 803 a 921)
- **Tipo**: `cartao`
- **Composição**: **Cartão Final de Alta Conversão (Agência)**
- **Mídia**: `img_4.jpg` com desfoque forte (blur 24px) + véu escuro gradiente `#0F172A` (92% de opacidade) e iluminação ciano central.
- **Elementos Visuais**:
  - Sem karaokê (regra expressa do EDITOR.md).
  - y=380: Logo/Identidade *"INOVARE CRM"* (68px, peso 900, branco + ciano `#0284C7`) com micro-brilho e flutuação.
  - y=510: Tag de produto: *"CRM Chatwoot com Inteligência Artificial"* (36px, cor ciano suave).
  - y=620: Proposta de valor: *"Feito sob medida para o seu negócio."* (38px, cor cinza claro `#E2E8F0`).
  - y=880–1040: Botão de Ação CTA:
    - Texto: **"CHAME NO DIRECT"** (44px, bold, caixa alta, exatamente a fala do locutor).
    - Estilo: Pílula azul royal / ciano com sombra volumétrica, ícone de mensagem / seta e **pulso contínuo (scale 1.00 a 1.08 em ciclo de 1.2s)**.
  - y=1180: Perfil oficial: `@inovarecrm` (38px bold) com ícone estilizado.
  - Todos os elementos rigorosamente contidos entre y=150 e y=1580.
