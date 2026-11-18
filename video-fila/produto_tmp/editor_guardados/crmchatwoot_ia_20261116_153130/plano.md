# Plano de Edição — CRM Chatwoot IA (`crmchatwoot_ia_20261116_153130`)

## Paleta e Identidade
- **Marca / Destaque:** `#1F93FF` (Azul Chatwoot vibrante)
- **Apoio / Fundo Escuro:** `#111827`
- **Texto sobre marca:** `#FFFFFF`
- **Safe Zone estrita:** `x: 60..1020`, `y: 150..1580`
- **Tipografia:** Montserrat (pesos 600, 700, 800, 900) — mínimo absoluto 32px.

---

## Cena 0 — Pergunta / Gancho (`0.00s` a `4.83s`)
- **Composição:** **(a) Texto GIGANTE cinético + card de alerta de dor sobre foto escurecida com zoom-in contínuo (`img_0.jpg`)**
- **Movimento de câmera:** Push-in contínuo no fundo (`scale 1.0 -> 1.10`, `translateY 0 -> -25px`) com vinheta radial e véu escuro na base para contraste absoluto.
- **Sincronia com a fala:** *"Sua equipe atende sem saber se a pessoa já é cliente?"*
  - `0.0s`: Pílula de alerta no topo (`y=190`): `ATENDIMENTO NO ESCURO?` + selo `QUEM É ESSE CLIENTE?` (`gancho_tela`).
  - `0.31s` ("Sua equipe atende"): Bloco principal do título cinético surge com spring (`SUA EQUIPE ATENDE`).
  - `1.30s` ("sem saber"): Destaque em marca-texto vermelho/laranja de alerta (`SEM SABER`).
  - `2.12s` ("se a pessoa já é cliente?"): Linha final (`SE JÁ É CLIENTE?`) em destaque azul `#1F93FF` + card visual central (`y=760..1180`) simulando um chamado chegando com perfil de cliente oculto (`Cliente: ???` / `Histórico: Não identificado` / `Tickets: ?`) que pulsa e gira levemente em 3D ao longo de toda a cena.
- **Transição (`4.48s - 4.83s`):** Desmonte suave em fade + scale-down antes da entrada do Dono.

---

## Cena 1 — O Problema (`4.48s` a `12.20s`)
- **Composição:** **(h) Vídeo tela cheia (`dono_1.mp4`) com câmera em zoom suave (`1.0 -> 1.06`) e elementos gráficos estritamente no topo (`y=165..430`)**
- **Proteção de Rosto/Corpo:** Área central (`y=440..1300`) 100% livre sem nenhum overlay escuro sobre a pele do apresentador (gradiente suave restrito apenas ao topo `y=0..460` e base `y=1350..1920`).
- **Sincronia com a fala:** *"Minha equipe atendia no escuro, sem saber se a pessoa era cliente antiga, mas resolvemos isso."*
  - `4.56s` ("Minha equipe atendia no escuro"): Rótulo `O PROBLEMA` + Card compacto de dor no topo (`y=170..410`): `Atendimento no escuro` com ícone de alerta.
  - `7.30s` ("sem saber se a pessoa era cliente antiga"): Sub-pílula dinâmica acende dentro do header (`Sem histórico da cliente antiga`).
  - `10.06s` ("mas resolvemos isso"): **Desmonte imediato da dor (0.0s de atraso)** — o card vermelho de dor faz scale-out em 0.2s e entra o card positivo azul `#1F93FF` (`Resolvemos isso com CRM + Chatwoot`), mantendo movimento contínuo até `12.20s`.
- **Transição (`11.85s - 12.20s`):** Wipe/slide vertical com transição para a cena do sistema.

---

## Cena 2 — Como Funciona (`11.85s` a `19.45s`)
- **Composição:** **(b) / (d) Interface integrada CRM Chatwoot inclinada em 3D leve (`rotateY`, `rotateX` flutuando continuamente) com conversa de WhatsApp + painel de Histórico e Tickets integrado sobre `img_2.jpg` escurecida**
- **Movimento de câmera:** Fundo `img_2.jpg` com pan e zoom (`1.02 -> 1.10`) e blur; container do CRM surge junto com a 1ª mensagem (sem caixa vazia).
- **Sincronia com a fala:** *"Nosso CRM feito a partir do Chatwoot reúne o histórico e os tickets anteriores junto da conversa."*
  - `11.95s`: Topo (`y=165..320`) com pílula `COMO FUNCIONA` + título `CRM a partir do Chatwoot` e selo `Simulação`.
  - `12.35s`: Surge o card do CRM com a 1ª mensagem do cliente: *"Olá, preciso revisar meu último chamado."*
  - `14.15s` ("Chatwoot reúne"): Indicador "digitando..." e entrada da 2ª mensagem (empresa): *"Olá! Já vi no seu histórico que você é nosso cliente e localizei seu ticket."*
  - `15.20s` ("histórico"): Pílula de destaque `✓ Histórico do cliente` acende no painel superior do CRM + 3ª mensagem (cliente): *"Ótimo, não preciso explicar tudo de novo."*
  - `16.07s` ("tickets anteriores junto da conversa"): Pílula `✓ Tickets anteriores` acende ao lado + 4ª mensagem (empresa): *"Aqui temos todo o seu atendimento registrado em um só lugar. Vamos resolver."*
  - Movimento contínuo de scroll suave nas mensagens e flutuação 3D até `19.45s`.

---

## Cena 3 — O Resultado (`19.10s` a `27.28s`)
- **Composição:** **(h) Vídeo tela cheia (`dono_3.mp4`) com push-in suave (`1.0 -> 1.06`) e painel compacto de ganhos no topo (`y=165..435`), rosto e tronco 100% livres**
- **Sincronia com a fala:** *"Hoje eu vejo quem já é cliente na hora, com dados e chamados centralizados para atender melhor."*
  - `19.20s`: Rótulo `O RESULTADO` no topo.
  - `19.91s` ("Hoje eu vejo quem já é cliente na hora"): Pílula 1 acende sincronizada: `Identificação de quem já é cliente`.
  - `23.15s` ("com dados e chamados centralizados"): Pílula 2 acende sincronizada: `Dados e chamados centralizados`.
  - `26.21s` ("para atender melhor"): Pílula 3 / destaque final no topo: `Atendimento personalizado com IA`.

---

## Cena 4 — Cartão Final / CTA (`26.93s` a `30.88s`)
- **Composição:** **(f) Cartão final de agência sobre `img_4.jpg` desfocada com zoom contínuo + véu escuro `#111827` + card central vivo com pulso contínuo**
- **Elementos (todos dentro de `y=180..1520`, sem Karaoke):**
  - Emblema/ícone animado do `CRM Chatwoot IA` com flutuação contínua.
  - Nome da marca grande em branco (`CRM Chatwoot IA`) — sem repetição em múltiplos cards.
  - Proposta de valor completa dos fatos: *"Um CRM feito para o seu negócio a partir do Chatwoot, com atendimento, tickets e histórico de cada cliente em um só lugar."*
  - Pílulas de síntese dos serviços: `CRM + Helpdesk/Tickets` • `Personalizado com IA`.
  - Botão CTA grande pulsando continuamente (`scale 1.0 -> 1.06` até o último frame) espelhando `convite_voz`: **`CHAME A GENTE NO DIRECT`**.
  - Arroba `@crmchatwoot.ia` em pílula de alto contraste abaixo do botão.
