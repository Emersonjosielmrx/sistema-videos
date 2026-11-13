# Plano de Edição — Follow-up IA (`followupia_ia_20261111_203720`)

## Identidade & Regras
- **Produto / Marca:** Follow-up IA (`#4ECDC4` turquesa destaque, `#111827` azul-escuro apoio/fundo, `#121216` texto sobre marca).
- **Duração total:** 33.41 s (1003 frames a 30 fps).
- **Zonas seguras:** `y = 150..1580`, `x = 60..1020` (margens mínimas de 60 px). Legenda Karaokê ancorada em `base = 360` (`y_base = 1560`).
- **Tipografia:** Montserrat (`@remotion/google-fonts/Montserrat`), todas as letras `>= 32 px` (títulos `>= 48 px`).

---

## Cenas e Composições

### Cena 0 — Pergunta (`0.00s` a `4.74s` | frames `0` a `142`)
- **Composição escolhida:** **(a) Texto GIGANTE tela cheia + card de alerta de orçamento sem resposta** sobre `img_0.jpg` escurecida com câmera viva (push-in 1.0 -> 1.08 + leve pan).
- **Posição dos elementos:**
  - Topo (`y = 175`): Pílula de gancho `Vendas perdidas por esquecimento?` (entra após `1.8s` como selo de contexto, e antes disso no frame 0-9 um alerta pulsante `ORÇAMENTO ENVIADO` para impacto imediato em 0.3s).
  - Centro-alto (`y = 260..680`): Título cinético gigante com a pergunta exata da fala: `"Esquece de cobrar quem pediu orçamento e não respondeu?"` — palavras acendem e ganham marca-texto `#4ECDC4` / alerta coral conforme faladas (`Esquece` 0.32s, `cobrar` 0.85s, `orçamento` 1.80s, `não respondeu?` 2.49s).
  - Centro-baixo (`y = 740..1120`): Mini-card vidro escuro simulando um orçamento de WhatsApp no vácuo (`Orçamento_Proposta.pdf` + `Visualizado` + relógio girando e status mudando de `Aguardando retorno...` para `Cliente sumiu`), com flutuação contínua.
- **Transição:** Wipe/slide dinâmico para a Cena 1.

### Cena 1 — Dono / O Problema (`4.39s` a `12.41s` | frames `132` a `372`)
- **Composição escolhida:** **(h) Vídeo cheio do dono (`dono_1.mp4`) com câmera em zoom suave (1.0 -> 1.06) e elementos só na faixa superior (`y = 155..410`)**, deixando o rosto do dono 100% livre.
- **Posição dos elementos:**
  - `y = 160`: Rótulo `O PROBLEMA` + título superior em card glassmorphism escuro (x=60..1020, altura até y=405).
  - Sincronizado com a fala:
    - Fase 1 (`4.39s` a `6.84s` — *"Eu atendia tantos clientes..."*): Card mostra `Muitos atendimentos` + fila de avatares/conversas acumulando.
    - Fase 2 (`6.84s` a `9.54s` — *"...que esquecia de cobrar quem sumia"*): Transição rápida (0.2s) no card superior para `Esquecia de cobrar quem sumia` com ícone de silêncio/vácuo.
    - Fase 3 (`9.54s` a `12.41s` — *"...perdendo vendas todo dia."*): Destaque vermelho/coral `Perdendo vendas todo dia` com indicador pulsante.

### Cena 2 — Veo / Como Funciona (`12.06s` a `22.15s` | frames `362` a `664`)
- **Composição escolhida:** **(b) + (g) Mockup de celular WhatsApp inclinado em 3D à esquerda + Checklist/Etapas de benefícios à direita** sobre `video_2.mp4` com filtro escuro elegante para contraste total e sem cobrir o dinamismo de fundo.
- **Posição dos elementos:**
  - Topo (`y = 160..240`): Pílula `COMO FUNCIONA` + badge `Follow-up IA` (`12.55s`).
  - Centro (`y = 265..1240`):
    - Celular grande (`width: 880px` centralizado/levemente angulado ou layout vertical integrado `x = 80..1000`) com selo `Simulação`, mostrando conversa real de WhatsApp onde a IA faz o follow-up automático:
      - Balão 1 (`12.7s`): Orçamento enviado antes.
      - Digitando + Balão IA (`15.1s` — *"acompanhamento automático no WhatsApp"*): `"Oi! Conseguiu avaliar o orçamento? Posso ajustar pra fecharmos hoje?"`
      - Balão Cliente (`18.5s` — *"recupera leads inativos sozinha"*): `"Oi! Correria aqui, vamos fechar sim!"`
    - Abaixo do chat (`y = 950..1240`), 3 pílulas de benefícios com ✓ animado que acendem na hora exata da fala:
      1. `16.14s`: `Acompanhamento automático no WhatsApp`
      2. `18.51s`: `Recupera leads inativos sozinha`
      3. `20.55s`: `Nunca desiste (a partir de R$ 199)`

### Cena 3 — Dono / O Resultado (`21.80s` a `29.81s` | frames `654` a `894`)
- **Composição escolhida:** **(h) Vídeo cheio do dono (`dono_3.mp4`) com zoom progressivo (1.0 -> 1.06) e barra/card de resultado no topo (`y = 155..410`)**, preservando o rosto e gesto do dono totalmente livres.
- **Posição dos elementos:**
  - `y = 160..405`: Card glassmorphism escuro com rótulo `O RESULTADO` e 3 estados sincronizados com a voz:
    - `21.88s` (*"Hoje eu não perco vendas por esquecimento"*): `Zero vendas perdidas por esquecimento` com check turquesa `#4ECDC4`.
    - `25.53s` (*"e converto pelo WhatsApp"*): `Conversão automática pelo WhatsApp`.
    - `27.21s` (*"sem depender de lembretes."*): `Sem depender de lembretes`.

### Cena 4 — Cartão Final (`29.46s` a `33.41s` | frames `884` a `1003`)
- **Composição escolhida:** **(f) Cartão final vivo de agência** com fundo em zoom/pan + recorte estilizado e véu escuro `#111827`, brilho em movimento, marca grande em branco + destaque `#4ECDC4`, proposta de valor dos fatos, botão pulsante `CHAME NO DIRECT` e `@followupia.ia`.
- **Posição dos elementos (dentro de `y = 180..1450`, sem Karaokê):**
  - Topo/Centro (`y = 220..780`): Badge `FOLLOW-UP AUTOMÁTICO QUE VENDE`, logo/título grande `Follow-up IA`, subtítulo curto `Recupera leads inativos e converte no WhatsApp sozinha` + pílula de fato `A partir de R$ 199 · Nunca desiste`.
  - Base (`y = 920..1380`): Botão principal grande pulsante `CHAME NO DIRECT` (com brilho varrendo a superfície) + `@followupia.ia` logo abaixo.
