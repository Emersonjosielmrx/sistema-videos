export const meta = {
  name: 'levantamento-melhorias-noite',
  description: 'Mutirão só-leitura: 14 áreas levantam melhorias com prova, cada área é conferida por um cético, e um agente final monta o plano por impacto',
  phases: [
    { title: 'Levantar', detail: '1 agente por área, só leitura' },
    { title: 'Conferir', detail: '1 cético por área tenta derrubar cada achado' },
    { title: 'Plano', detail: 'consolida, remove repetidos e ordena por impacto' },
  ],
}

const REGRAS = `REGRAS (obrigatórias):
- SÓ LEITURA: não edite, crie, mova nem apague arquivos; não rode nada que mude estado; não reinicie tarefas.
- NÃO fale com nenhum serviço como conta (YouTube, TikTok, Google, Kaggle, Fish, Instagram) e NÃO use ssh (rajada de ssh trava o desktop). Só arquivos locais do PC1 e comandos locais leves (grep/Glob/Read, python -c lendo JSON).
- NÃO varra o D:\\ inteiro com grep/find (estoura o tempo): vá direto nas pastas indicadas.
- Toda afirmação precisa de PROVA: caminho:linha, número tirado de log/JSON (diga qual arquivo) ou trecho de código. Sem prova = não entra.
- Antes de propor, confira se JÁ EXISTE (chave de ambiente, comentário com data, arquivo de decisão). Já feito = não proponha de novo; se está feito mas desligado/quebrado, diga isso.
- Respeite as regras da dona: nunca 2 contas no mesmo IP; postagem sempre agendada (+25 min); 1080p mínimo; nada abre janela (rodar_oculto.vbs); PC1 fica livre pro VS Code (teste pesado fora); pesquisador e melhoradores estão PAUSADOS por decisão dela (não proponha religar).
- Português, direto. Máximo 12 achados, os de MAIOR impacto primeiro.`

const PASTAS = `Mapa (comece por aqui):
- Shorts (produção): D:\\recapd-ambientes\\producao\\bin — anime_auto.py, anime_script.py, anime_tts.py, fx_clips.py, fx_subtitles.py, legenda_mix.py, capar_shorts.py, seo_generator.py, parceiro_diario.py, cortes_juri.py
- Longos: D:\\recapd-ambientes\\producao\\colab (postar_longos.py, postar_xtts_teste.py, motor_voz.json se existir) e D:\\video-fila\\linhas\\LONGOS\\LONGOS_MELHORIAS.md
- Fish Audio (voz PRIMÁRIA dos Shorts, online): D:\\hipercool-materiais\\comum\\fish_audio (fish_http.py, fish_lote.py, creditos.py, creditos.json)
- Postador: D:\\postador-de-videos\\bin (politica.py, youtube_web_poster.py, postar_tiktok_auto.py, rampa_canais.py, catalogo.py, produto\\)
- Orquestração: D:\\video-fila (controlador.py, celulares.py, maquinas.py, relatorio_ronda.py, vigilancia.py, medico_recuperacao.py, gerente_videos.py, estado\\*.json(l))
- Comum: D:\\hipercool-materiais\\comum ; manhwa-react: D:\\manhwa-react ; kit3d: D:\\kit3d-producao
- Aprendizado já registrado: D:\\video-fila\\aprendizado\\PARA_IMPLEMENTAR.md e LEIA_ANTES_DE_MELHORAR.md
- Sinais medidos dos Shorts (o que dá view): D:\\video-fila\\estado\\sinais_shorts.json
- Relatório de hoje: D:\\tmp\\ronda_tarde.txt`

const AREAS = [
  { key: 'visual-shorts', foco: `VISUAL DOS SHORTS: edição, ritmo de cortes, movimento, legenda (estilo MIX), gancho dos primeiros 3 s, capa/thumbnail, delogo/tarja, efeitos. Cruze com estado\\sinais_shorts.json (o que mais rende: hora 21h = 8,9x; legenda lateral; fx raio azul 1,31x; saudação A 1,29x; fala rápida A 1,2x...) e diga quais vencedores medidos NÃO estão ligados por padrão.` },
  { key: 'narracao-shorts-fish', foco: `NARRAÇÃO DOS SHORTS com Fish Audio como voz PRIMÁRIA (online, sobra recurso de CPU/GPU que antes ia pra TTS local). Liste as melhorias de narração JÁ FEITAS NOS LONGOS (narradores por clima/banco de piadas, misto XTTS 8 + S2-Pro, acelerar no clímax, réplicas, pausas, entonação por personagem, abertura com voz humana etc. — leia LONGOS_MELHORIAS.md, anime_tts.py e a memória do motor de voz) e diga, uma a uma, COMO portar para os Shorts usando o Fish (parâmetros do Fish, emoção/prosódia, vozes por personagem, ritmo). Inclua o custo em créditos (8.000/conta/mês, 1 crédito/caractere, 40 contas) e como não estourar.` },
  { key: 'narracao-longos', foco: `NARRAÇÃO DOS LONGOS: estado atual (motor padrão XTTS 8 + S2-Pro misto), o que ainda falha (QA, imagem parada, voz robótica, troca de narrador), e o que dá mais retenção. Use os relatórios/CONFERENCIA.md dos longos em D:\\hipercool-materiais\\animes recap\\na_nuvem\\*\\ e logs do colab.` },
  { key: 'codigo-morto', foco: `CÓDIGO MORTO E LIXO: scripts .py nunca chamados (nem por tarefa agendada, nem import, nem .bat), arquivos .bak_* e cópias, funções duplicadas entre projetos (ex.: duas cópias de vps_central.py, de kaggle_pool.json, de rclone/caminhos fixos), chaves de ambiente que nunca são lidas, módulos com o mesmo nome em pastas diferentes. Dê a lista com prova de que não é usado (grep do nome nos .py/.bat/.vbs das 4 pastas principais e na lista de tarefas: rode 'schtasks /query /fo csv /v' uma vez e procure).` },
  { key: 'arquitetura', foco: `ARQUITETURA E ORGANIZAÇÃO: hoje são vários projetos remendados (recapd, postador, video-fila, hipercool comum, manhwa-react, kit3d) que se importam por sys.path e caminhos fixos D:\\... Mapeie as dependências cruzadas reais (quem importa quem), os pontos frágeis (caminho fixo, config duplicada, dois arquivos de estado pro mesmo dado), e proponha uma organização-alvo INCREMENTAL (passos pequenos, sem big-bang) com o primeiro passo concreto.` },
  { key: 'postagem-recuperacao', foco: `POSTAGEM E RECUPERAÇÃO DOS CANAIS: agendamento (politica.horario_publicacao, so_nobre, rampa, punidos), quantos Shorts por canal/dia vs o que rende, canais restritos (D:\\video-fila\\MEDICO.md), uploads que falham (envios_por_maquina.jsonl, uploads_ledger.jsonl), fila de celular. O que mais acelera a recuperação com base nos números.` },
  { key: 'tarefas-agendadas', foco: `TAREFAS AGENDADAS DO WINDOWS: rode 'schtasks /query /fo csv /v' UMA vez. Liste tarefas desabilitadas há muito tempo, tarefas que apontam pra script que não existe, tarefas que falham sempre (Último resultado != 0), duplicadas (mesmo script em 2 tarefas), e tarefas pesadas no horário errado (colidindo com render no PC1).` },
  { key: 'maquinas-render', foco: `MÁQUINAS E RENDER: PC1 em 100%, celulares S20/S20 Ultra/G20 ~5% de uso (estado\\uso_maquinas.jsonl, celulares_stats.json), desktop e PC2. Onde o tempo de CPU do PC1 vai por Short (fx_subtitles queima legenda = encode inteiro; fx_clips junta-trechos já vai pro celular via celulares.rodar_ffmpeg, que recusa arquivo não-'-i' como .ass/fontes). Proponha o desenho exato pra levar a queima de legenda aos celulares (mandar .ass e fontes junto) e outros offloads, com risco e como testar fora do PC1.` },
  { key: 'modelos-ia', foco: `USO DE MODELOS DE IA: quem chama o quê (Gemini Flash, Opus, Sonnet web, Kiro, Argon, Hydrogen), desperdício (testes repetidos, chamadas que sempre falham, retentativas), roteiro/título/QA que podiam usar modelo mais barato ou cache. Fontes: D:\\video-fila\\estado\\placar_modelos.jsonl, logs das caixas de conserto, código que chama painel_ia/ia_reserva/OmniRoute.` },
  { key: 'vigia-relatorio', foco: `VIGIA, ALERTAS E RELATÓRIO: vigilancia.py (detecção Gemini, conserto Argon→Hydrogen→Sonnet→Kiro), avisos/Telegram, relatorio_ronda.py. Alarmes falsos, lacunas (o que quebrou hoje e ninguém avisou: carrossel MS Energy 66 h com checkpoint, acúmulo de vídeos no disco, longos que nunca terminavam de subir, fila de celular parada recebendo vídeo), e seções do relatório que mentem ou faltam.` },
  { key: 'redes-tiktok-insta-fb', foco: `TIKTOK, INSTAGRAM E FACEBOOK: postar_tiktok_auto.py (teto 4/conta, 27 de 58 contas pausadas, 640 vídeos disponíveis parados), Instagram, Reels do Facebook (fb_views.jsonl mede só 1-6 reels visíveis). O que destrava volume com segurança (sem dividir IP) e o que medir melhor.` },
  { key: 'aprendizado-metricas', foco: `CICLO DE APRENDIZADO E MÉTRICAS: o que já é medido (sinais_shorts, views por canal, retenção dos longos, médico da recuperação) e o que falta pra decidir com dado (A/B que nunca fecha por falta de amostra, views dos posts de celular sem ID, experimentos sem grupo controle). Proponha o loop mínimo que transforma medição em decisão automática.` },
  { key: 'disco-arquivos', foco: `DISCO E ARQUIVOS: gerente_videos.py (regras R1-R8, INVENTARIO_VIDEOS.md), pastas que ainda crescem sem dono (D:\\tmp com 3 GB de testes, D:\\veo\\beta 5,6 GB, D:\\caches 18 GB, estudo_voz 2,5 GB), logs gigantes (*.log e *.jsonl acima de 100 MB nas pastas do mapa), arquivos .partial esquecidos.` },
  { key: 'confiabilidade-falhas', foco: `CONFIABILIDADE: pontos únicos de falha e falhas silenciosas vistas hoje — upload de longo morto por timeout sem registro, processo pai/filho órfão, travas .lock que ficam, Drive com erro 401 intermitente, OmniRoute com 429. Procure try/except que engole erro sem logar nos arquivos do mapa e timeouts fixos curtos demais pra arquivos grandes.` },
]

const ACHADOS = {
  type: 'object',
  properties: {
    resumo_area: { type: 'string' },
    achados: { type: 'array', items: { type: 'object', properties: {
      titulo: { type: 'string' },
      problema: { type: 'string' },
      evidencia: { type: 'string' },
      proposta: { type: 'string' },
      impacto: { type: 'string', enum: ['alto', 'medio', 'baixo'] },
      esforco: { type: 'string', enum: ['baixo', 'medio', 'alto'] },
      risco: { type: 'string', enum: ['baixo', 'medio', 'alto'] },
      ja_existe: { type: 'string' },
    }, required: ['titulo', 'problema', 'evidencia', 'proposta', 'impacto', 'esforco', 'risco'] } },
  },
  required: ['resumo_area', 'achados'],
}

const VEREDITOS = {
  type: 'object',
  properties: {
    vereditos: { type: 'array', items: { type: 'object', properties: {
      titulo: { type: 'string' },
      valido: { type: 'boolean' },
      motivo: { type: 'string' },
      correcao: { type: 'string' },
    }, required: ['titulo', 'valido', 'motivo'] } },
  },
  required: ['vereditos'],
}

// 24/11 dona: "disparar agentes apenas com Opus; os tokens podem acabar — não perder o progresso". Cada agente grava o
// próprio resultado em D:\video-fila\levantamento\areas\<etapa>_<area>.json e, se o arquivo já existe, devolve o salvo
// sem refazer (a rodada seguinte do cron só gasta cota no que faltou).
const DIR = 'D:\\video-fila\\levantamento\\areas'
function salvar(nome, quando) {
  return `\n\nSALVAGUARDA (obrigatória — a cota de tokens pode acabar a qualquer momento):
- ANTES de começar: se o arquivo ${DIR}\\${nome}.json JÁ EXISTE e tem conteúdo válido, NÃO refaça: leia-o e devolva exatamente o que está nele como sua resposta.
- ${quando}: grave o resultado COMPLETO em ${DIR}\\${nome}.json (JSON, UTF-8) com a ferramenta Write ANTES de responder. É o único jeito de não perder o trabalho se a cota acabar.`
}

phase('Levantar')
const porArea = await pipeline(
  AREAS,
  a => agent(`Você é um auditor sênior olhando UMA área do sistema de produção de vídeos da dona.\n\nÁREA: ${a.foco}\n\n${PASTAS}\n\n${REGRAS}${salvar('levantar_' + a.key, 'Ao terminar o levantamento')}`,
    { label: `levantar:${a.key}`, phase: 'Levantar', schema: ACHADOS }),
  (r, a) => {
    if (!r || !r.achados || !r.achados.length) return { area: a.key, resumo: r ? r.resumo_area : 'sem resposta', achados: [] }
    return agent(`Você é um revisor CÉTICO. Outro agente levantou estes achados na área "${a.key}". Para CADA um, tente DERRUBAR: (1) a prova existe mesmo? abra o arquivo/linha ou o JSON citado; (2) já está implementado ou ligado (procure a chave/função)? (3) a proposta quebra alguma regra da dona (IP, agendamento, 1080p, PC1 livre, pesquisador pausado)? (4) o impacto está exagerado? Marque valido=false se qualquer um falhar e diga por quê; se for válido mas a proposta tiver erro, escreva a correção. Na dúvida sem prova, valido=false.\n\n${REGRAS}${salvar('conferir_' + a.key, 'Ao terminar a conferência')}\n\nACHADOS:\n${JSON.stringify(r.achados, null, 1)}`,
      { label: `conferir:${a.key}`, phase: 'Conferir', schema: VEREDITOS })
      .then(v => {
        const vs = (v && v.vereditos) || []
        const ok = r.achados.filter(x => { const m = vs.find(y => y.titulo === x.titulo); return !m || m.valido })
          .map(x => { const m = vs.find(y => y.titulo === x.titulo); return m && m.correcao ? { ...x, proposta: x.proposta + ' | CORREÇÃO DO REVISOR: ' + m.correcao } : x })
        const derrubados = vs.filter(y => !y.valido).map(y => ({ titulo: y.titulo, motivo: y.motivo }))
        return { area: a.key, resumo: r.resumo_area, achados: ok, derrubados }
      })
  },
)

const validos = porArea.filter(Boolean)
const total = validos.reduce((s, a) => s + a.achados.length, 0)
const caidos = validos.reduce((s, a) => s + ((a.derrubados || []).length), 0)
log(`${total} achados confirmados, ${caidos} derrubados pelos revisores, em ${validos.length} áreas`)

phase('Plano')
const plano = await agent(`Você recebeu os achados JÁ CONFERIDOS de ${validos.length} áreas do sistema de vídeos da dona. Monte o PLANO FINAL em português:
1. Remova repetidos entre áreas (mesmo problema visto de dois lados = 1 item, cite as duas áreas).
2. Classifique cada item em: (A) FAZER AGORA — impacto alto/médio, esforço baixo, risco baixo, dá pra fazer com chave que desliga; (B) PROJETO — impacto alto mas esforço/risco médio-alto (precisa teste fora do PC1); (C) DECISÃO DA DONA — muda regra dela ou mexe em conta/cliente; (D) LIMPEZA — código morto/lixo seguro de remover (sempre com backup).
3. Para cada item: título, áreas, problema em 1 linha, prova (caminho:linha ou número), o que fazer exatamente (arquivo/função), chave pra desligar sugerida, ganho esperado.
4. No topo: os 10 itens de MAIOR ganho para views/recuperação, e as 3 melhorias de NARRAÇÃO dos longos que mais valem portar para os Shorts com Fish (com custo em créditos/dia).
5. No fim: o que ficou sem verificar (área sem resposta, prova não encontrada).
Seja concreto; nada de conselho genérico.
Ao terminar, grave o plano INTEIRO em D:\\video-fila\\levantamento\\PLANO_MELHORIAS.md com a ferramenta Write (é o entregável da dona) antes de responder.

ACHADOS:\n${JSON.stringify(validos, null, 1)}`, { label: 'plano-final', phase: 'Plano' })

return { plano, por_area: validos }
