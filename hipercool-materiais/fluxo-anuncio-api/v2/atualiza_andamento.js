// Lê o andamento dos vídeos no Shotstack e decide se o laço continua (o só com música pode terminar depois do narrado).
const v = $('🧩 Confere o pedido').first().json;
const p = $('🧩 Guarda os projetos').first().json;
const a = ($('🎬 Shotstack: como está o narrado?').first().json || {}).response || {};
const b = p.musica ? (($input.first().json || {}).response || {}) : { status: 'done' };
const PASSOS = { queued: 10, fetching: 25, generating: 40, preprocessing: 55, rendering: 70, saving: 90, done: 100, failed: 100 };
const NOMES = { 10: 'na fila do Shotstack', 25: 'baixando as fotos e a trilha', 40: 'gerando a voz', 55: 'preparando as cenas', 70: 'montando o vídeo', 90: 'salvando', 100: 'terminando a versão só com música' };
const passo = m => PASSOS[m.status] || 10;
const passou = (Date.now() - p.inicio) / 1000;
let estado = 'montando', erro = '';
if (a.status === 'failed') { estado = 'erro'; erro = a.error || 'o Shotstack não conseguiu montar o vídeo'; }
else if (a.status === 'done' && (b.status === 'done' || b.status === 'failed')) estado = 'pronto';
else if (passou > 900) { estado = 'erro'; erro = 'O Shotstack demorou mais de 15 minutos. Tente de novo.'; }
// o Shotstack às vezes volta de "gerando a voz" para "na fila": a porcentagem segue o relógio (nunca desce) e só
// encosta em 99 quando os dois vídeos terminaram
const progresso = estado === 'montando' ? Math.min(95, Math.round(5 + passou / 1.6)) : 99;
const status = { job: v.job, etapa: 'montando', progresso, detalhe: `🎞️ ${NOMES[passo(a)]} · ${progresso}%`, op: v.op, dados: { titulo: v.dados.titulo, tipo: v.dados.tipo_txt } };
// o "url" do andamento some em 24 h; o CDN do Shotstack guarda para sempre (endereço montado com o dono e o código do render)
const cdn = (m, ext) => m.owner && m.id ? `https://cdn.shotstack.io/au/${p.ambiente}/${m.owner}/${m.id}${ext}` : '';
return [{ json: {
  estado, erro, terminou: estado !== 'montando', pronto: estado === 'pronto',
  video: cdn(a, '.mp4') || a.url || '', capa: cdn(a, '-poster.jpg') || a.poster || '',
  video_musica: b.status === 'done' && p.musica ? (cdn(b, '.mp4') || b.url || '') : '',
  duracao: Number(a.duration) || 0, tamanho_mb: 0, status: JSON.stringify(status),
} }];
