// Grava o resultado: os 2 vídeos, a capa, a página do anúncio, a estratégia, a revisão e os textos para postar.
const v = $('🧩 Confere o pedido').first().json;
const st = $('🧩 Atualiza o andamento').first().json;
const ed = $('🧩 Junta tudo').first().json;
const rev = $('🧩 Aplica a revisão').first().json;
const est = $('🧩 Lê a estratégia').first().json;
let pg = null;
try { pg = $('🧩 Prepara a página').first().json; } catch (e) {}
if (st.estado !== 'pronto') {
  return [{ json: { status: JSON.stringify({ job: v.job, etapa: 'erro', op: v.op, erro: 'A montagem falhou: ' + String(st.erro || 'sem detalhe').slice(-220) }) } }];
}
const arq = (pg && pg.arquivos) || { video: st.video, video_musica: st.video_musica, capa: st.capa };
return [{ json: { status: JSON.stringify({
  job: v.job, etapa: 'pronto', op: v.op, dados: { titulo: v.dados.titulo, tipo: v.dados.tipo_txt, preco: v.dados.preco },
  video: arq.video, video_musica: arq.video_musica || '', capa: arq.capa || '',
  duracao: st.duracao, tamanho_mb: st.tamanho_mb, segundos: Math.round((Date.now() - v.criado_em) / 1000),
  pagina: pg && pg.ok ? v.pagina : '', anuncio: v.anuncio, redes: ed.redes, clima: ed.clima, cor: ed.cor,
  revisao: { problemas: rev.problemas, trocas: rev.trocas, revisou: rev.revisou, problemas_textos: ed.problemas_textos, textos_revisados: ed.textos_revisados },
  estrategia: { publico: est.publico, angulo: est.angulo, gancho: est.gancho, beneficios: est.beneficios, objecao: est.objecao },
  roteiro: ed.segmentos.map(s => ({ n: s.n, foto: s.foto, texto: s.texto, texto_tela: s.texto_tela, movimento: s.movimento, transicao: s.transicao, selo_preco: s.selo_preco })),
}) } }];
