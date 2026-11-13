# Mudanças no Telegram pedidas pela dona (31/10/2026)

Progresso gravado na hora (tokens podem acabar). [x] = feito e testado.

## Frentes
1. [x] Bot geral: ROTA nova no avisos.py (argon/sonnet/troca-modelo -> opus; melhorador/eng.reversa/máquinas/longo
       -> producao; banimento/nsn/telão/vigia desktop/instagram login/credenciais -> pendencias_humanas); SO_RESUMO
       (rotina que se resolve sozinha) e SO_REGISTRO (proxy/túnel religado, "voltou") só no avisos.jsonl.
       Desktop: vigia_desktop.py avisa só com 1 h fora sem voltar (ssh_fora_desde) + "✅ voltou" se tinha avisado.
2. [x] Comentários: notificar_telegram.py manda no bot de comentários (chave "com:<id>" no mapa_respostas) e lê as
       respostas lá (_responder_bot). Confirmação/auto-resposta respondem no mesmo bot.
3. [x] Filtro por @: config/comentarios_proprios.json (@Fabricadeautomacoesia) + handles da rede; vale no
       notificar_telegram (aviso, retroativo, auto-resposta) e no sem_token.py. @ciano001ofc (11) = perguntar à dona
4. [~] Contas "deslogadas": YouTube 13/30 "mortos" = só a CÓPIA dos cookies vencida (vídeos saindo normal).
       manter_cookies.py: relogar() recopia do Chrome do cofre (3 por rodada, rodízio) e só avisa pendências se o
       cofre estiver sem login em 2 rodadas. saude.py (nsn): sem CAIU/VOLTOU; só conta morta > 24 h, 1 vez, resumo.
       Teste em animescomia: "sem SAPISID", mas a pasta estava ocupada (cofre checar: porta não abriu) -> 1 aviso
       de teste saiu em pendências humanas às ~23:20 (pode ser falso). Flow: 68/215 mortos nas máquinas — não mexi.
5. [x] ritmo de postagem / rampa de canais = MUDO no avisos.py
6. [ ] Aviso de postagem destacando os LONGOS
7. [ ] Bot do Opus: também as voltas do Argon e do Sonnet web
8. [ ] Erros de produção (item cortado na mensagem da dona) -> bot de produção
9. [ ] Produção: curto x longo; longo com previsão, onde posta, quanto demorou, atualizações que entraram e as que
       ficam pro próximo
10. [ ] Painel: Shorts mais vistos faltando vídeos de 1,4/1,5/1,8 mi; conferir com total do canal no Studio
11. [ ] Aprendizado: qual IA? auto-aprovar e dizer a IA (dá pra desligar)
12. [ ] Interessados no produto: só mandar o prompt
13. [ ] Bot do Studio: muito aviso de vídeo duplicado — por quê?

## Achados
- Origens que caem no bot geral (4 dias): argon 161 (resumo), melhorador central 81, banimento 52+25, nsn 41,
  telao 37+9, vigia desktop 26+7, troca-modelo 39, sonnet-web 23, instagram login 17, engenharia_reversa 18,
  longo 5, recap-longo 4, desktop-vigia 4, credenciais-kaggle 4, maquinas-24h 3, supervisor_melhorador 2.
- Comentários: notificar_comentario() usa enviar() = bot geral; o bot de comentários só recebe os do sem_token.py.
