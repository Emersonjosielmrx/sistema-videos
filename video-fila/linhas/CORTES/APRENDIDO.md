# Regras aprendidas — CORTES (atualizado 17/11 19:51; a sessão da linha aplica no pipeline)
1. Manter rosto, olhos, boca e ponto focal da ação física 100% desobstruídos, banindo legendas, tarjas, stickers ou textos sobre a área principal do rosto.
2. Confinar títulos, tarjas superiores, @ oficial e cards estritamente entre x=60 e x=1020 e entre y=150 e y=1580, garantindo margem lateral e evitando cortes.
3. Renderizar títulos superiores, @ oficial e cards como camadas estáticas desacopladas, eliminando herança de pan, zoom ou punch-in.
4. Cobrir integralmente legendas, manchetes e textos nativos da fonte com tarja preta semitransparente ou fundo sólido para apagar qualquer texto residual.
5. Eliminar 100% de marcas d'água, textos em inglês ao fundo, arrobas (@), logotipos e stickers da fonte via reenquadramento limpo ou cobertura sólida.
6. Fixar a legenda dinâmica na zona segura inferior centralizada (respeitando y entre 150 e 1580), garantindo respiro adequado acima do rodapé para evitar sobreposição com a interface.
7. Exibir rigorosamente uma única palavra ou expressão ativa por vez sincronizada à locução, sem sobreposição física, fragmentação ou duplicação de blocos de texto.
8. Formatar legendas com preenchimento sólido em amarelo (#FFFF00) ou branco (#FFFFFF) com contorno preto espesso (mínimo de 3px a 12px) e sombra projetada forte, com tamanho mínimo de 32px.
9. Manter a mesma família tipográfica em CAIXA ALTA uniforme do frame 0.0s ao último milissegundo, com corpo >= 32px e destaques de 50 a 70px.
10. Garantir que a primeira palavra da legenda no q01 traga exatamente a primeira palavra falada pela narração, acompanhada de tarja ou elemento de impacto visual imediato nos primeiros 2s.
11. Renovar o estímulo visual a cada 1.5s a 3.5s com novos planos contextuais, B-rolls ou reenquadramentos dinâmicos com transição acentuada (> 20% de movimento real por corte) e zoom-in progressivo/ken burns em takes estáticos.
12. Exibir tomadas que ilustrem com precisão exata o protagonista, os personagens corretos da obra e a ação física da locução, mantendo estrita coerência temática.
13. Agrupar e sequenciar os takes de forma fluida, banindo o efeito ping-pong (vaivém repetitivo), planos duplicados e quebras abruptas na transição de ritmo.
14. Respeitar a cronologia estrita dos acontecimentos e a sincronia exata da narração, evitando spoilers visuais antecipados de palavras-chave antes de serem pronunciadas.
15. Cortar para a nova tomada no milissegundo exato em que o novo assunto, sujeito ou elemento for introduzido na locução, garantindo que o início da cena coincida com o movimento da ação.
16. Executar 100% das transições estritamente por corte seco limpo ou corte seco dinâmico/punch-in na revelação, banindo clarões brancos, névoa, falhas, linhas diagonais/artefatos de overlay ou efeitos de distorção óptica excessivos (como glitch pesado).
17. Manter a geometria original das imagens e textos, banindo efeitos de distorção esférica ou estiramento.
18. Preencher 100% do quadro na resolução 1080x1920 sem bordas pretas, tarjas pretas borradas ou artefatos no rodapé, mantendo o sujeito centralizado com headroom adequado.
19. Validar 100% das palavras da legenda dinâmica contra o roteiro, corrigindo rigorosamente erros de grafia, digitação, duplicação ou sincronia antes da renderização e eliminando termos sem sentido ou truncados.
20. Manter movimento ativo e legenda ativa até o último frame, cortando a seco na última sílaba falada para emendar perfeitamente na primeira frase do loop, focando o enquadramento final no rosto expressivo.
21. Fixar o identificador oficial (@) exclusivamente no topo seguro (y entre 150 e 220, x entre 60 e 250), estático, contínuo, sem redundâncias e distante de tarjas e botões.
22. Banir rabiscos desenhados à mão, figurinhas ou stickers desconexos, cards HUD/arcade, balões de mangá, marcas d'água de plataformas, tarjas de chat verde e ícones de engajamento sobrepostos.
23. Importar e renderizar overlays, ícones e ilustrações exclusivamente em PNG com canal alfa limpo e recorte nítido, banindo fundos sólidos que bloqueiem o vídeo.
24. Estruturar camadas na ordem estrita: vídeo base < tarjas < cards/B-rolls/selos < legenda dinâmica < tarja de gancho e @ oficial, sem competição vertical ou sobreposição caótica de elementos visuais.
25. Aplicar tarja preta semi-transparente ou fundo sólido por trás de legendas secundárias ou inferiores sobre fundos claros ou complexos para garantir leitura instantânea em telas pequenas.
