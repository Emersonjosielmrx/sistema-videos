# Motor contínuo do Pesquisador — análise (Opus, 04/11 03:00)

Pedido da dona: "funcione como o melhorador: apertou um botão, aciona; o Argon fica buscando coisas externas que possam
melhorar os projetos de vídeo constantemente enquanto houver tokens, sem repetir, cada vez mais específico; ele NÃO
implementa, só verifica se já existe no código e documenta."

## Veredito: faz sentido, com 5 correções obrigatórias
1. **Argon sozinho não basta.** Na rodada medida (COMPARACAO_MODELOS.md 03/11) o Argon errou licença (F5-TTS "comercial")
   e no resumo dele apareceram 4 repositórios que NÃO existem. Motor = Argon busca -> verificador da API derruba 404 ->
   Sonnet (sonnet-ajudante, não gasta Opus) revisa licença e números de cada lote. Sem isso o catálogo enche de lixo.
2. **Cota do Argon é dividida com a produção** (argon_zelador, melhorador, classificar_pro). O motor só roda quando
   sobra: confere que a resposta veio do "4 Argon" de verdade (sem cota ele vira Flash-Lite calado) e PARA se a fila
   de produção estiver usando. Prioridade sempre da produção.
3. **Precisa de GITHUB_TOKEN só leitura.** Sem token a API dá 60 consultas/h e a busca 10/min; na madrugada de 04/11
   estourou duas vezes. Com token: 5.000/h. (Token pessoal, escopo público, sem nenhuma permissão de escrita.)
4. **"Já existe no código" por grep de nome é fraco.** Procurar o nome do repo, o nome do pacote pip/npm e o import
   (ex.: `torchfcpe`, `onnxruntime`, `remotion`) nas pastas dos projetos; resultado em 3 níveis: USA / CITADO EM DOC /
   INÉDITO. Nunca afirmar "já temos" sem o arquivo:linha.
5. **Não gravar só no fim.** Cada lote grava a resposta bruta, a conferência e o histórico antes do próximo (o pedido
   da dona de não perder dados se os tokens acabarem). Retomada lê o rodada.json e pula o que já tem arquivo.

## Como fica (sem implementar nada nos projetos)
- `pesquisador.py motor ligar|desligar|status` + botão no painel :8790 (mesmo padrão do melhorador), estado em
  estado_motor.json, processo oculto (rodar_oculto.vbs).
- Cada volta: pega a área/projeto pesquisada há mais tempo -> pedido com ja_conhecidos + historico_areas (não repetir)
  -> Argon -> conferir na API -> Sonnet revisa -> grep nos projetos -> grava CATALOGO_DESCOBERTAS.md -> AREAS_NOVAS
  viram subáreas (fica mais específico a cada volta).
- Obstáculo técnico: o Argon com WEB vem do agente argon-pesquisa do Claude Code (ferramenta WebFetch). Um processo de
  fundo precisa chamar `claude -p --agent argon-pesquisa` (headless) ou o Argon com busca embutida pelo OmniRoute.
  Testar qual dos dois traz links reais antes de ligar o motor.

## Áreas novas a incluir já
- skills_agentes: skills/plugins/MCP para os agentes que trabalham nos vídeos (rodada 2026-11-04_skills).
- vc_mean_flow, roteiro_anotado_voz, tts_edicao_acustica, rvc_onnx_kaggle_linux, longform_tts_blocos (Opus 04/11).
