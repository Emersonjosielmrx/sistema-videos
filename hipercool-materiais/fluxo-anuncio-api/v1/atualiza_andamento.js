// Lê o andamento dos vídeos na JSON2Video e decide se o laço continua (o só com música pode terminar depois do narrado).
const v = $('🧩 Confere o pedido').first().json;
const p = $('🧩 Guarda os projetos').first().json;
const a = ($('🎬 JSON2Video: como está o narrado?').first().json || {}).movie || {};
const b = p.musica ? (($input.first().json || {}).movie || {}) : { status: 'done' };
const passo = m => m.status === 'done' ? 100 : /movie/i.test(m.message || '') ? 80 : /scene/i.test(m.message || '') ? 50 : /download/i.test(m.message || '') ? 25 : 10;
const NOMES = { 10: 'na fila da JSON2Video', 25: 'baixando as fotos e a trilha', 50: 'narrando e dando movimento às fotos', 80: 'juntando cenas, legenda e trilha', 100: 'terminando a versão só com música' };
const passou = (Date.now() - p.inicio) / 1000;
let estado = 'montando', erro = '';
if (a.status === 'error') { estado = 'erro'; erro = a.message || 'a JSON2Video não conseguiu montar o vídeo'; }
else if (a.status === 'done' && (b.status === 'done' || b.status === 'error')) estado = 'pronto';
else if (passou > 900) { estado = 'erro'; erro = 'A JSON2Video demorou mais de 15 minutos. Tente de novo.'; }
const progresso = Math.min(99, Math.round((passo(a) * 2 + passo(b)) / 3));
const status = { job: v.job, etapa: 'montando', progresso, detalhe: `🎞️ ${NOMES[passo(a)]} · ${progresso}%`, op: v.op, dados: { titulo: v.dados.titulo, tipo: v.dados.tipo_txt } };
return [{ json: {
  estado, erro, terminou: estado !== 'montando', pronto: estado === 'pronto',
  video: a.url || '', capa: a.thumbnail || '', video_musica: b.status === 'done' && p.musica ? (b.url || '') : '',
  duracao: Number(a.duration) || 0, tamanho_mb: a.size ? Math.round(a.size / 1e5) / 10 : 0, status: JSON.stringify(status),
} }];
