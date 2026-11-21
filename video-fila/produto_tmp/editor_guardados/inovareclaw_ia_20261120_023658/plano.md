# Plano de Edição — inovareclaw_ia_20261120_023658
Produto: Inovare Claw | Duração: 32.44s (974 frames a 30 fps) | Dimensões: 1080x1920

## Paleta e Estilo Visual
- Cor Primária/Marca: #7C3AED (Roxo Tech Vibrante)
- Cor Fundo/Apoio: #111827 (Dark Navy/Slate escuro)
- Acentos: #A78BFA (Lavanda neon), #10B981 (Verde status execução)
- Tipografia: Montserrat (Black 900, Bold 700, Medium 500)
- Piso tipográfico: Mínimo 32px para todo e qualquer texto. Títulos entre 52px e 76px.
- Safe Zone: y = 150 até y = 1580; margens laterais x = 60 até x = 1020.
- Karaokê: src/lib/karaoke.tsx ancorado com base=360 (base da caixa em y=1560), isolado estritamente por cena/fala.

---

## Cena 0: Pergunta (0.00s a 5.19s | frames 0 a 155)
- **Fala:** "Isso só responde perguntas ou realmente faz o trabalho por mim?"
- **Composição:** a) Texto cinético GIGANTE em camadas com suporte de alto contraste sobre fundo escuro da marca.
- **Movimento de Câmera:** Fundo (img_0.jpg) com push-in constante de 1.00x para 1.12x e rotação sutil (0.5deg).
- **Entrada de Elementos:**
  - 0.0s - 0.4s: Tarja diagonal no topo (y=180) "DÚVIDA FREQUENTE" com badge de alerta.
  - 0.3s - 1.8s: Primeiro bloco na palavra "responde perguntas" (y=620) — Card escuro com destaque vermelho/laranja "SÓ RESPONDE PERGUNTAS?".
  - 1.8s - 3.7s: Segundo bloco na palavra "realmente faz o trabalho" (y=920) — Card com borda iluminada roxa #7C3AED "OU REALMENTE FAZ O TRABALHO?".
  - 3.7s - 5.19s: Transição de saída com fade e scale para a próxima cena.
- **Transição para Cena 1:** Wipe angular/zoom-through com fade cruzado de 0.3s.

---

## Cena 1: O Problema - Dono (4.84s a 13.03s | frames 145 a 391)
- **Fala:** "Eu achava que toda inteligência artificial só escrevia texto. Eu pedia, ela respondia, e o trabalho continuava comigo."
- **Rótulo:** "O problema"
- **Composição:** h) Vídeo do apresentador (dono_1.mp4) em tela cheia (objectFit: cover).
- **Proteção do Apresentador:** Rosto e tronco livres (cabeça y=380..1250 protegida com respiro > 50px).
- **Movimento de Câmera:** Push-in contínuo do vídeo de 1.00x para 1.06x.
- **Entrada de Elementos (Topo Livre: y=160 a 350):**
  - 4.84s: Tarja horizontal com corte diagonal #7C3AED (clip-path chanfrado) com texto "01 • O PROBLEMA" (implementação aprendizado 7f4d41fc / 79c80bb8).
  - 5.66s - 9.26s: Na fala "achava que toda IA só escrevia texto", card superior translúcido (opacidade 90%) com texto "IA QUE SÓ ESCREVE TEXTO".
  - 9.76s - 12.82s: Na fala "o trabalho continuava comigo", o card superior transiciona para "O TRABALHO CONTINUAVA COMIGO" com destaque em alerta.
- **Karaokê:** Ativo no rodapé (y=1560) com destaque roxo #7C3AED.
- **Transição para Cena 2:** Slide lateral suave com fade.

---

## Cena 2: Como Funciona - Conversa Interativa (12.68s a 21.02s | frames 380 a 630)
- **Fala:** "O Inovare Claw é um agente autônomo. Você passa a tarefa, e ele executa de verdade, sem ficar só na conversa."
- **Rótulo:** "Como funciona"
- **Composição:** b) Interface de smartphone moderno em perspectiva 3D (rotateY ~12° e levitação suave) exibindo conversa em tempo real.
- **Movimento de Câmera:** Fundo (img_2.jpg) em pan horizontal lento (translateX -30px a +30px) e escala 1.05x. Smartphone com levitação senoidal de 6px.
- **Entrada de Elementos:**
  - 12.68s: Tarja chanfrada no topo "02 • COMO FUNCIONA" + chip "AGENTE AUTÔNOMO".
  - 13.17s: Aparelho entra com spring suave. Header com "Inovare Claw • Agente Ativo" e selo "Simulação" visível.
  - 13.5s: Balão 1 (Cliente): "Preciso organizar essa tarefa para hoje."
  - 15.0s: Indicador "Digitando..." / "Iniciando agente...".
  - 16.0s: Balão 2 (Empresa): "Certo. Já comecei a executar." com badge verde [EXECUÇÃO INICIADA].
  - 17.5s: Balão 3 (Cliente): "Mas você só me diz como fazer?"
  - 18.5s: Balão 4 (Empresa): "Não. Eu faço a tarefa por você e aviso quando terminar."
  - 19.8s: Balão 5 (Cliente): "Perfeito, obrigado."
  - Todos os textos com tamanho >= 32px (perfeitamente legíveis).
- **Karaokê:** Ativo no rodapé (y=1560).
- **Transição para Cena 3:** Zoom rápido para corte com desfoque de movimento.

---

## Cena 3: O Resultado - Dono (20.67s a 28.85s | frames 620 a 865)
- **Fala:** "Hoje eu delego a tarefa e sigo cuidando do meu negócio. Meu agente de IA trabalha sozinho."
- **Rótulo:** "O resultado"
- **Composição:** h) Vídeo do apresentador (dono_3.mp4) em tela cheia com push-in de 1.00x para 1.06x.
- **Proteção do Apresentador:** Cabeça e tronco 100% desobstruídos.
- **Entrada de Elementos (Topo Livre: y=160 a 350):**
  - 20.67s: Tarja chanfrada "03 • O RESULTADO" com acento verde/roxo de conquista.
  - 21.48s - 25.62s: Card superior com "DELEGO A TAREFA E CUIDO DO NEGÓCIO" + micro-ícone de autonomia.
  - 26.88s - 28.85s: Card superior muda para "MEU AGENTE DE IA TRABALHA SOZINHO" com badge pulsante "AUTÔNOMO".
- **Karaokê:** Ativo no rodapé (y=1560).
- **Transição para Cena 4:** Transição de revelação circular / blur para a tela final.

---

## Cena 4: Cartão Final (28.50s a 32.44s | frames 855 a 974)
- **Fala:** "Chame a gente no direct."
- **Composição:** f) Cartão de conversão com branding Inovare Claw, grafismos de luz, botão com pulso contínuo e @ da marca.
- **Movimento:** Fundo (img_4.jpg) com escala contínua de 1.00x para 1.08x. Glows circulares orbitando suavemente.
- **Elementos (Centralizados e Seguros):**
  - Topo (y=380): Ícone de agente IA com borda gradiente neon roxo.
  - Marca (y=560): "INOVARE CLAW" em fonte 72px bold branco com sombra de impacto.
  - Descrição oficial (y=670): "Seu agente de IA que trabalha sozinho" (fato do briefing).
  - Botão CTA (y=840): "CHAME NO DIRECT" (fundo roxo #7C3AED, texto branco 48px, cantos arredondados, pulso scale 1.0 a 1.07 até o último frame, shimmer de luz).
  - Perfil oficial (y=1040): Badge cápsula "@inovareclaw.ia" com ícone de direct.
- **Karaokê:** DESATIVADO (proibido no cartão final).
