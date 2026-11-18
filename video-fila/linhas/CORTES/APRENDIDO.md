# Regras aprendidas — CORTES (atualizado 18/11 16:02; a sessão da linha aplica no pipeline)
1. Manter rosto, olhos, boca e ponto focal da ação física 100% desobstruídos, banindo legendas, tarjas e textos sobre a área principal do rosto.
2. Confinar títulos, tarjas superiores, @ oficial e cards estritamente na zona segura (x entre 60 e 1020, y entre 150 e 1580), garantindo respiro e evitando sobreposição.
3. Renderizar títulos superiores, @ oficial e cards como camadas estáticas desacopladas, eliminando herança de pan, zoom ou punch-in.
4. Cobrir integralmente legendas, manchetes e textos nativos da fonte com tarja preta semitransparente ou fundo sólido para apagar qualquer texto residual, marcas d'água e legendas queimadas.
5. Fixar a legenda dinâmica estritamente na zona segura inferior (respeitando y entre 150 e 1580, com limite inferior garantindo que a legenda nunca ultrapasse y=1580), margens laterais mínimas de 60px e contorno/sombra fortes.
6. Exibir rigorosamente uma única palavra ou expressão ativa por vez sincronizada à locução exata no milissegundo de fala, sem sobreposição física, fragmentação excessiva, duplicação ou acúmulo de legendas fantasmas.
7. Formatar legendas com preenchimento sólido em amarelo (#FFFF00) ou branco (#FFFFFF) com contorno preto espesso e sombra projetada forte, corpo mínimo de 34px e alinhamento centralizado.
8. Garantir impacto imediato, curiosidade ou pergunta direta no gancho inicial a partir do frame 0 para travar o scroll, utilizando imagens contextuais limpas correspondentes ao áudio, evitando inícios genéricos ou estáticos.
9. Renovar o estímulo visual a cada 1.5s a 3.5s com novos planos contextuais, B-rolls ou reenquadramentos dinâmicos com transição acentuada (> 25% de movimento real) e zoom-in progressivo, banindo cenas estáticas ou de baixo movimento (<20%).
10. Exibir tomadas que ilustrem com precisão exata o protagonista, os personagens corretos da obra e a ação física da locução, mantendo rigor na correspondência visual.
11. Agrupar e sequenciar os takes de forma fluida, banindo o efeito ping-pong, planos duplicados e quebras abruptas na transição de ritmo.
12. Respeitar a cronologia estrita dos acontecimentos e a sincronia exata da narração, garantindo que o texto exibido e os takes correspondam rigorosamente ao roteiro fornecido desde o gancho inicial.
13. Cortar para a nova tomada no milissegundo exato em que o novo assunto, sujeito ou elemento for introduzido na locução, garantindo sincronia com o movimento da ação e alinhamento perfeito do timing da cena.
14. Executar 100% das transições estritamente por corte seco limpo ou corte seco dinâmico/punch-in na revelação, banindo clarões, efeito fade para branco excessivo, névoa, falhas, artefatos de overlay ou ghosting.
15. Manter a geometria original das imagens e textos, banindo efeitos de distorção esférica ou estiramento.
16. Preencher 100% do quadro na resolução 1080x1920 sem bordas pretas, tarjas pretas opacas pesadas no rodapé ou áreas mortas, mantendo o sujeito centralizado com headroom adequado.
17. Validar 100% das palavras da legenda dinâmica contra o roteiro, corrigindo rigorosamente erros de grafia, digitação, duplicação, termos aleatórios ou sincronia antes da renderização e evitando preposições isoladas ou truncadas.
18. Manter movimento ativo e legenda ativa até o último frame, cortando a seco na última sílaba falada para emendar perfeitamente na primeira frase do loop, destacando a última palavra com cor contrastante e garantindo fluidez sem cortes abruptos.
19. Fixar o identificador oficial (@) exclusivamente no topo seguro (y entre 150 e 220, x entre 60 e 250), estático, contínuo, sem redundâncias e distante de tarjas e botões.
20. Banir rabiscos desenhados à mão, figurinhas ou stickers desconexos, cards HUD/arcade, balões de mangá/chat intrusivos, prints de mensagens, contagens numéricas incorretas e marcas d'água.
21. Importar e renderizar overlays, ícones e ilustrações exclusivamente em PNG com canal alfa limpo e recorte nítido, banindo fundos sólidos ou tarjas brancas irregulares que bloqueiem o vídeo ou elementos centrais.
22. Estruturar camadas na ordem estrita: vídeo base < tarjas de cobertura de legenda queimada < cards/B-rolls/selos < legenda dinâmica < tarja de gancho e @ oficial, sem competição vertical ou sobreposição de texto no topo.
23. Aplicar tarja preta semi-transparente ou fundo sólido por trás de legendas secundárias, HUDs ou elementos textuais sobre fundos complexos para garantir leitura instantânea, mantendo respiro adequado em relação às margens.
24. Remover rigorosamente artefatos de quebra de linha crus, tags, códigos de texto corrompidos, textos duplicados no topo ou artigos isolados no encerramento ou em qualquer ponto do vídeo.
