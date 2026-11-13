# Plano de Edição — inovareclone_20261112_210030

**Produto:** Avatar IA (Inovare Clone)
**Duração:** 27.88s (837 frames a 30 fps)
**Cores da marca:** Marca/Destaque `#8B5CF6`, Apoio/Fundo `#1F2937`, Texto `#FFFFFF`

## Diagnóstico das Imagens Fornecidas
- `img_0.jpg`, `img_1.jpg`, `img_4.jpg` possuem exatamente o mesmo arquivo base (302197 bytes) e contêm uma banana sobre o caderno na parte inferior central (`img_2.jpg` também contém um gadget em formato de banana no centro-inferior).
- `img_3.jpg` é uma recepção/sala corporativa moderna limpa (sem banana).
- **Estratégia Visual Anti-Repetição e Anti-Objeto Estranho (Regras 2, 4, 22 do APRENDIDO.md):**
  - Nas cenas 0, 1, 2 e 4, faremos enquadramentos diferenciados focando na parte superior/arquitetura corporativa (janelas panorâmicas, sala executiva, plantas, iluminação) com crops e máscaras geométricas que deixam a parte inferior (onde está a banana) 100% fora do quadro visível, combinados com motion graphics ricos de agência e composições totalmente distintas em cada cena.

---

## Cenas e Composições

### Cena 0 — Pergunta (0.00s a 5.29s)
- **Composição:** **(a) Texto GIGANTE tela cheia + (f) Recorte/Enquadramento superior corporativo com HUD de gravação**
- **Fala:** "Falta tempo na rotina corrida para gravar vídeos toda semana?"
- **Visual & Movimento:**
  - Fundo: Parte superior da sala executiva (`img_0.jpg` com `objectPosition: '50% 12%'`, zoom contínuo 1.15 -> 1.32 e pan horizontal) escurecida com gradiente na cor `#1F2937`.
  - 0.0s–0.3s: Pop imediato do selo `Sem tempo de gravar?` (`gancho_tela`) e visor de câmera REC pausado/agenda lotada.
  - Sincronizado palavra a palavra com a fala:
    - `0.31s` ("Falta tempo"): Título cinético principal parte 1 `FALTA TEMPO NA ROTINA CORRIDA`
    - `2.19s` ("gravar vídeos"): Destaque em pílula roxa `#8B5CF6` `PARA GRAVAR VÍDEOS`
    - `2.99s` ("toda semana?"): Fechamento `TODA SEMANA?` + medidor visual de agenda/semana preenchendo de Seg a Sex mostrando a correria.
  - Transição: Wipe/Slide dinâmico às 4.94s.

### Cena 1 — O Problema (4.94s a 11.09s)
- **Composição:** **(c) Tela dividida / Antes x Depois (Rotina Corrida vs. Gravação Travada)**
- **Fala:** "A rotina corrida da empresa me impedia de sentar e gravar conteúdo com frequência."
- **Visual & Movimento:**
  - Topo (y=160): Pílula de rótulo `O PROBLEMA`.
  - Divisão vertical/diagonal animada com linha varrendo o quadro e cards comparativos dinâmicos sobre fundo arquitetônico em movimento (`img_1.jpg` crop superior direito + overlay escuro):
    - Lado 1 (`5.43s` - "A rotina corrida da empresa"): Card `ROTINA DA EMPRESA` com barra de tarefas/demandas subindo continuamente.
    - Lado 2 (`6.99s` - "me impedia de sentar e gravar"): Card `GRAVAR CONTEÚDO` que acende aos 7.0s mostrando câmera em pausa / frequência travada (`8.47s` "conteúdo com frequência").

### Cena 2 — Como Funciona (10.74s a 18.31s)
- **Composição:** **(b) Celular inclinado em 3D (rotateY) + Etapas sincronizadas (1-2-3)**
- **Fala:** "A tecnologia cria uma versão digital da pessoa, gerando posturas automáticas para falar em português."
- **Visual & Movimento:**
  - Fundo: `img_2.jpg` com recorte focado no ambiente de escritório superior e luz natural (ocultando a mesa inferior) + grade tecnológica roxa `#8B5CF6` em movimento.
  - Topo (y=160): Pílula `COMO FUNCIONA — AVATAR IA`.
  - Esquerda: Mockup de smartphone grande (altura 840px, inclinado em 3D `rotateY(16deg)`) exibindo o estúdio "Inovare Clone — Avatar IA" com silhueta/avatar digital falando, ondas de voz em português e indicador de postura ativa.
  - Direita: 3 etapas cronológicas que acendem exatamente na palavra falada:
    - Passo 1 (`12.51s` - "versão digital da pessoa"): `1. Versão digital sua`
    - Passo 2 (`14.55s` - "posturas automáticas"): `2. Posturas automáticas`
    - Passo 3 (`15.94s` - "falar em português"): `3. Fala em português`

### Cena 3 — O Resultado (17.96s a 24.29s)
- **Composição:** **(h) Foto cheia em movimento forte (`img_3.jpg`) + (g) Painel/Checklist de presença diária nas redes**
- **Fala:** "Hoje coloco meu clone digital ativo nas redes todo dia, sem pausar o negócio."
- **Visual & Movimento:**
  - Fundo: `img_3.jpg` (recepção corporativa moderna, 100% limpa e inédita) ocupando a tela toda com pan e zoom cinematográfico (1.02 -> 1.14), mais de 65% da fotografia visível.
  - Topo (y=165): Pílula `O RESULTADO` + Título enxuto `CLONE DIGITAL ATIVO TODO DIA`.
  - Centro-baixo (acima da legenda, em pílulas horizontais translúcidas de alto contraste): Calendário semanal de postagens (`SEG`, `TER`, `QUA`, `QUI`, `SEX`, `SÁB`, `DOM`) acendendo ticks `✓` um a um conforme fala "ativo nas redes todo dia" (`20.12s`–`21.69s`), seguido da pílula de destaque `✓ Sem pausar o negócio` aos `21.99s`.

### Cena 4 — Cartão Final / CTA (23.94s a 27.88s)
- **Composição:** **Cartão Final Vivo de Agência**
- **Fala:** "Chame a gente no direct."
- **Visual & Movimento:**
  - Fundo: `img_3.jpg` / `img_4.jpg` (crop superior desfocado) + véu escuro `#1F2937` com luzes roxas `#8B5CF6` em movimento contínuo.
  - Card central unificado (y=360 a 1380): Identidade **INOVARE CLONE**, subtítulo **Avatar IA**, frase de fatos `Seu próprio avatar IA postando todo dia nas redes, com posturas automáticas e fala em português.`
  - Botão CTA grande pulsando continuamente (scale 1.0 -> 1.06) com brilho varrendo: `CHAME NO DIRECT` + `@inovareclone`.
  - Sem legenda Karaokê no cartão final.
