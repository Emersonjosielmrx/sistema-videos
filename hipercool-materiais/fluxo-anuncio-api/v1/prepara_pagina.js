// Monta o que a página pública do anúncio mostra (fica no ar 30 dias). Os vídeos são os links da JSON2Video (7 dias);
// as fotos e a capa ficam no Redis por 30 dias e o próprio n8n entrega.
const v = $('🧩 Confere o pedido').first().json;
const ed = $('🧩 Junta tudo').first().json;
const est = $('🧩 Lê a estratégia').first().json;
const st = $('🧩 Atualiza o andamento').first().json;
let capa = st.capa;
try {
  const c = $('🧩 Prepara a capa').first().json;
  if (c.ok) capa = v.arquivo + c.id;
} catch (e) {}
const d = v.dados;
const anuncio = {
  id: v.anuncio, job: v.job, criado_em: new Date().toISOString(), tipo: d.tipo, tipo_txt: d.tipo_txt,
  marca: d.marca, titulo: d.titulo, preco: d.preco, oferta: d.oferta, detalhes: d.detalhes, endereco: d.endereco,
  whatsapp: d.whatsapp, instagram: d.instagram, site: d.site, cor: ed.cor,
  descricao: ed.redes.descricao_pagina || d.detalhes, destaques: ed.destaques && ed.destaques.length ? ed.destaques : est.destaques, mensagem_whatsapp: ed.redes.mensagem_whatsapp,
  fotos: v.fotos, video: st.video || '', video_musica: st.video_musica || '', capa: capa || '',
};
return [{ json: { ok: true, arquivos: { video: anuncio.video, video_musica: anuncio.video_musica, capa: anuncio.capa }, anuncio: JSON.stringify(anuncio), chave: '<SEGREDO_REMOVIDO>' + v.anuncio } }];
