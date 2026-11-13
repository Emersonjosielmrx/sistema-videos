Projeto: Veo/Flow (todos os projetos que geram vídeo/imagem no Flow: veo\beta, ms-energy/solares, foto_na_hora,
claude-code-video, cadeia_veo)

# Fila central do Flow + créditos rígidos (pedido da dona 01/11)

Pedido completo, diagnóstico, o que foi feito e o que falta: **`D:\veo\docs\CREDITOS_E_FILA_CENTRAL.md`**.

## Onde preciso de você (o que passou do meu limite)
1. **Arquitetura da fila central**: hoje 5+ projetos chamam o `gera_auto` por conta própria, coordenados só por trava de
   porta e reserva de notebook. Desenhar a fila única (serviço sempre ligado, prioridade chat > clientes > produtos >
   reserva, paralelismo 1..N que cresce com sucesso e encolhe com falha, nunca 0) e o caminho de migração sem parar
   a produção. Arquivos: `veo\beta\cron_gerar_video_llm.py` (escolher_sessao, gerar_video, marcar_conta_fora),
   `veo\beta\cadeia_veo.py`, `postador-de-videos\bin\maquina_remota.py`, `ms-energy\bin\gerar_short_veo.py`,
   `veo\beta\foto_na_hora.py`.
2. **Por que o exit 3 ("login caiu") acontece em conta logada?** Em 01/11 ~50 contas castigadas 6 h com o painel
   lendo-as logadas com 1050 créditos. Uma causa vista: conta tentada numa máquina onde não está logada (PC1). Há outras?
   (token reCAPTCHA? cookie diferente por máquina?) Log: `ms-energy\logs\reel_globo.log` 09:34–10:25 de 01/11.
3. **Saldo diferente da mesma conta por máquina** (pc2 1020 x notebooks 50): é outro login do Google no mesmo perfil?
   Gerar na máquina errada gasta a conta errada.

MVP já no ar (01/11): `veo\beta\flow_saldo_real.py`, `creditos_contas.real/ordenar/fora`, `_castigo_desmentido`.
