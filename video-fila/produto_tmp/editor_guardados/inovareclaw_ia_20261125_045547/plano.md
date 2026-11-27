# Plano de Edição — Inovare Claw (ID: inovareclaw_ia_20261125_045547) — Versão Corrigida

**Duração:** 29.54s (887 frames a 30 fps)  
**Marca:** Inovare Claw (`#7C3AED`)  
**Cores:** Marca `#7C3AED`, Destaque `#8B5CF6`, Fundo `#0F172A`/`#111827`, Texto `#FFFFFF`  
**Safe Zone:** y=150 a y=1580, margens laterais x=60 a 1020 (largura útil 960px).  
**Tipografia:** Montserrat (pesos 700 e 900), piso mínimo absoluto >= 32px.  
**Karaoke:** Pronto de `src/lib/karaoke.tsx`, ativo em todas as cenas com quebras naturais e sem palavras órfãs.

---

## Cena 0 — Pergunta (0.00s a 5.58s | frames 0 a 167)
- **Fala:** "Passo as rotinas chatas da empresa para a IA executar?"
- **Composição:** (a) Texto GIGANTE tela cheia com palavras-chave em marca-texto e câmera com Ken Burns contínuo.
- **Fundo:** `img_0.jpg` com Ken Burns contínuo (scale 1.02 -> 1.15, translateY 0 -> -35px) + feixe de luz dinâmico e vinheta escura.
- **Elementos Visuais:**
  - y=175: Badge no topo pop imediato no frame 1: "ROTINA CHATA? DELEGUE" (gancho_tela) em pílula escura com borda `#7C3AED` e ponto pulsante.
  - HUD IA com cantoneiras ativas que respiram e pulsam em brilho neon (`scale` e `drop-shadow`), mais scanner dinâmico.
  - y=380 a 960: Texto cinético escalonado sincronizado com as palavras:
    - 0.3s: "PASSO AS" (48px, bold, branco)
    - 0.7s: "ROTINAS CHATAS" (74px, black 900, em caixa marca-texto roxa viva `#7C3AED`)
    - 1.6s: "DA EMPRESA" (52px, bold, branco)
    - 2.3s: "PARA A IA EXECUTAR?" (62px, extra bold, destaque violeta neon)
  - Microdinâmica: Floating idle constante em todo o texto para evitar congelamento entre q02 e q03.
- **Transição:** Fade suave cruzado com Cena 1.

---

## Cena 1 — O Problema / Dono (5.23s a 13.26s | frames 157 a 398)
- **Fala:** "Eu via a equipe gastar horas do expediente em tarefa repetitiva. Era tempo que não voltava para o negócio."
- **Composição:** (h) Vídeo do dono em tela cheia (`dono_1.mp4`) com punch-in dinâmico (1.02x -> 1.15x aos 10.4s) e compensação vertical de headroom.
- **Elementos Visuais:**
  - y=165: Badge "01 • O PROBLEMA" (pílula escura, borda roxa).
  - y=228 a 340: Card superior compacto (padding reduzido) garantindo >190px de respiro (headroom) acima do cabelo do apresentador.
  - Virada da fala aos 10.4s (frame 156):
    - Punch-in digital para 1.15x com rebaixamento Y (+115px) para não cortar o cabelo.
    - Transição do card com slide vertical e blur fade de "HORAS EM TAREFAS REPETITIVAS" para "TEMPO QUE NÃO VOLTAVA PARA O NEGÓCIO" (norma culta correta).
  - Karaoke: "DO EXPEDIENTE EM TAREFA REPETITIVA." totalmente agrupado; "ERA TEMPO QUE NÃO VOLTAVA" e "PARA O NEGÓCIO." sem preposição órfã.
- **Transição:** Motion zoom blur fluido conectando à Cena 2.

---

## Cena 2 — Como Funciona / Conversa (12.91s a 19.76s | frames 387 a 593)
- **Fala:** "Você passa a tarefa para o Inovare Claw. Ele executa de forma independente, do começo ao fim."
- **Composição:** (b) Mockup de celular mobile nativo (largura 880px, altura 940px) com perspectiva 3D suave (rotateY) e diálogo corporativo verossímil.
- **Elementos Visuais:**
  - y=165: Badge "02 • COMO FUNCIONA".
  - Chat corporativo verossímil:
    - 13.4s: Mensagem 1 (Gestor): "Emita os relatórios de fechamento da semana e envie o resumo no canal da diretoria."
    - 15.0s: Indicador de digitação (3 pontos pulsando com spring) "Agente processando".
    - 15.6s: Mensagem 2 (Agente): "Entendido. Coletando dados dos sistemas e compilando o fechamento de forma autônoma."
    - 16.8s: Indicador de digitação "Concluindo envio".
    - 17.5s: Mensagem 3 (Agente): "Relatórios gerados e resumo enviado no canal da diretoria. ✓"
    - 18.0s: Painel ativo inferior "Autonomia do início ao fim • Executado ✓" eliminando a área preta vazia.
  - Karaoke: Bloco 1 exibe "VOCÊ PASSA A TAREFA PARA O INOVARE CLAW." (com nome da marca preservado); Bloco 2 divide em "ELE EXECUTA DE FORMA INDEPENDENTE," e Bloco 3 "DO COMEÇO AO FIM.".
- **Transição:** Transição de aproximação conectando à Cena 3.

---

## Cena 3 — O Resultado (19.41s a 25.95s | frames 582 a 778)
- **Fala:** "Hoje a rotina chata fica com o agente, e minha equipe usa o expediente no que importa."
- **Composição:** (c / motion graphic) Fundo tecnológico estilizado representando automação e fluxos de dados em vez de foto de reunião repetida.
- **Elementos Visuais:**
  - y=165: Badge "03 • O RESULTADO".
  - y=245 a 360: Frase imponente, curta e imponente em destaque: "SUA EQUIPE LIVRE PARA O QUE IMPORTA".
  - y=410 a 1150: Cards de transformação limpos, sem excesso de texto e sem porcentagem inventada:
    - Card 1: "Agente assume as tarefas • Executa de forma independente pelo dono".
    - Conector dinâmico com fluxo de dados ativo.
    - Card 2: "Equipe focada no negócio • Tempo dedicado ao crescimento real".
  - Microdinâmica: Floating idle suave contínuo e brilho neon oscilante em bordas.
- **Transição:** Push suave para o Cartão Final.

---

## Cena 4 — Cartão Final / CTA (25.60s a 29.54s | frames 768 a 887)
- **Fala:** "Chame a gente no direct."
- **Composição:** Encerramento harmônico, centralizado e distribuído por toda a safe zone (y=260 a y=1560) com zoom push-in contínuo (1.00 a 1.05).
- **Elementos Visuais:**
  - y=270: Ícone com anel neon giratório contínuo.
  - y=420: Marca "INOVARE CLAW" (72px, bold).
  - y=515: Slogan "Seu agente de IA que trabalha sozinho".
  - y=620: Botão de CTA "CHAME NO DIRECT" com pulso heartbeat e brilho metálico contínuo.
  - y=780: Badge limpa sem arroba duplicada: "@inovareclaw.ia".
  - y=880: Texto de apoio com alto contraste (#DDD6FE): "Tarefas de verdade executadas por IA".
  - y=970: Selo de credibilidade: "Automação no nível do Hermes e OpenClaw".
  - y=1560 (base 360): Legenda karaokê "CHAME A GENTE NO DIRECT." sincronizada com a locução.
