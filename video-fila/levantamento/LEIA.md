# Levantamento de melhorias — noite 24/11

Pedido da dona (24/11 00:20): "dispare os agentes apenas com Opus, sabendo que os tokens podem acabar — esteja pronto
pra não perder o progresso; crie crons pra trabalhar a noite toda até 8h; comece daqui 1h39" (= 01:57).

- Script do workflow: `levantamento.js` (14 áreas -> levantar -> conferir (cético) -> plano). Só Opus (sem agentType).
- Salvaguarda: cada agente grava `areas\levantar_<area>.json` e `areas\conferir_<area>.json`; se o arquivo já existe,
  devolve o salvo sem gastar cota. O plano final vai em `PLANO_MELHORIAS.md`.
- Crons (sessão do VS Code — param se o chat fechar): rodada a cada 20 min de 01:57 até 08:00; cada rodada vê o que
  falta e relança o workflow; com cota esgotada só registra em `noite.log` e espera a próxima.
- Retomar à mão: `Workflow({scriptPath: "D:\\video-fila\\levantamento\\levantamento.js"})` — o que já está salvo não é refeito.
- Áreas: visual-shorts, narracao-shorts-fish, narracao-longos, codigo-morto, arquitetura, postagem-recuperacao,
  tarefas-agendadas, maquinas-render, modelos-ia, vigia-relatorio, redes-tiktok-insta-fb, aprendizado-metricas,
  disco-arquivos, confiabilidade-falhas.
