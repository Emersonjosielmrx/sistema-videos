# Regras aprendidas — CORTES (atualizado 18/11 19:51; a sessão da linha aplica no pipeline)
1. Manter rosto, olhos, boca e ponto focal da ação física 100% desobstruídos, banindo legendas, tarjas e textos sobre a área principal do rosto.
2. Confinar títulos, tarjas superiores, @ oficial e cards estritamente na zona segura (x entre 60 e 1020, y entre 150 e 1580), garantindo respiro e afastamento total das bordas.
3. Renderizar títulos superiores, @ oficial e cards como camadas estáticas desacopladas, eliminando herança de pan, zoom ou punch-in.
4. Cobrir integralmente legendas, manchetes e textos nativos da fonte com tarja preta semitransparente ou fundo sólido para apagar qualquer texto residual, marcas d'água e legendas queimadas.
5. Fixar a legenda dinâmica estritamente na zona segura inferior (respeitando y entre 150 e 1580, com limite inferior elevado e margens laterais mínimas de 60px) com contorno/sombra fortes e tamanho mínimo de 32px.
6. Exibir rigorosamente uma única palavra ou expressão ativa por vez sincronizada à locução exata no milissegundo de fala, sem sobreposição física, fragmentação excessiva, duplicação ou acúmulo de legendas fantasmas.
7. Garantir impacto imediato com corte dinâmico de zoom-in ou introdução de ação real logo no primeiro quadro (0.8s) do gancho inicial para travar o scroll imediatamente.
8. Renovar o estímulo visual a cada 1.5s a 3.5s com novos planos contextuais, B-rolls ou reenquadramentos dinâmicos com transição acentuada (> 25% de movimento real) e zoom-in/out progressivo para eliminar estagnação.
9. Exibir tomadas que ilustrem com precisão exata o protagonista, os personagens corretos da obra e a ação física da locução, mantendo rigor na correspondência visual.
10. Agrupar e sequenciar os takes de forma fluida, banindo o efeito ping-pong, planos duplicados e quebras abruptas na transição de ritmo.
11. Respeitar a cronologia estrita dos acontecimentos e a sincronia exata da narração, garantindo que o texto exibido e os takes correspondam rigorosamente ao roteiro fornecido desde o gancho inicial.
12. Cortar para a nova tomada no milissegundo exato em que o novo assunto, sujeito ou elemento for introduzido na locução, garantindo sincronia com o movimento da ação e alinhamento perfeito do timing da cena.
13. Executar 100% das transições estritamente por corte seco limpo ou corte seco dinâmico/punch-in na revelação, banindo clarões, efeito fade para branco excessivo, névoa, falhas, artefatos de overlay ou ghosting.
14. Manter a geometria original das imagens e textos, banindo efeitos de distorção esférica ou estiramento.
15. Preencher 100% do quadro na resolução 1080x1920 sem bordas pretas, tarjas pretas opacas pesadas no rodapé ou áreas mortas, mantendo o sujeito centralizado com headroom adequado.
16. Validar 100% das palavras da legenda dinâmica contra o roteiro, corrigindo rigorosamente erros de grafia, digitação, duplicação, termos aleatórios ou sincronia antes da renderização e evitando preposições isoladas ou truncadas.
17. Manter movimento ativo e legenda ativa até o último frame, cortando a seco na última sílaba falada para emendar perfeitamente na primeira frase do loop, destacando a última palavra com cor contrastante e garantindo fluidez sem cortes abruptos.
18. Fixar o identificador oficial (@) exclusivamente no topo seguro (y entre 150 e 220, x entre 60 e 250), estático, contínuo, sem redundâncias e distante de tarjas e botões.
19. Banir rabiscos desenhados à mão, figurinhas ou stickers desconexos, cards HUD/arcade, balões de mangá/chat intrusivos, prints de mensagens, contagens numéricas incorretas e marcas d'água.
20. Importar e renderizar overlays, ícones e ilustrações exclusivamente em PNG com canal alfa limpo e recorte nítido, banindo fundos sólidos ou tarjas brancas irregulares que bloqueiem o vídeo ou elementos centrais.
21. Estruturar camadas na ordem estrita: vídeo base < tarjas de cobertura de legenda queimada < cards/B-rolls/selos < legenda dinâmica < tarja de gancho e @ oficial, sem competição vertical ou sobreposição de texto no topo.
22. Aplicar tarja preta semi-transparente uniforme por trás de textos fixos inferiores e legendas secundárias estritamente dentro da zona segura (y entre 150 e 1580), garantindo legibilidade sem poluir o centro da cena.
23. Garantir que a quebra de palavras nas legendas evite sobreposição ou corte de artefatos de interface, centralizando o destaque da palavra isolada na zona segura e sem fragmentar em excesso.
24. Aplicar efeitos de movimento dinâmico ou tremor de câmera (shake) em takes estáticos de baixo movimento para manter o limiar mínimo de atividade visual exigido para alta retenção.
