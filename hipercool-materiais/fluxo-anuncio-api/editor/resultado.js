// Grava o resultado: o vídeo editado (link vale 7 dias), a capa, quanto encurtou e a legenda para o post.
const v = $('🧩 Pega o vídeo').first().json;
const st = $('🧩 Atualiza o andamento').first().json;
const mo = $('🧩 Monta a edição').first().json;
const ia = $('🧩 Lê a direção').first().json;
if (!st.pronto) return [{ json: { status: JSON.stringify({ job: v.job, etapa: 'erro', erro: 'A edição falhou: ' + String(st.erro || '').slice(-220) }) } }];
return [{ json: { status: JSON.stringify({
  job: v.job, etapa: 'pronto', video: st.video, capa: st.capa, duracao: mo.total, original: mo.original,
  cortes: mo.cortes, tirou: mo.tirou, gancho: ia.gancho, topicos: ia.topicos, legenda_post: ia.legenda_post,
  segundos: Math.round((Date.now() - v.criado_em) / 1000), dados: { titulo: v.dados.titulo },
}) } }];
