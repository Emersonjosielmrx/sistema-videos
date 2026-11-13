// Lê o andamento no Very Good FFmpeg e decide se o laço continua. Os links dos arquivos valem 7 dias.
const v = $('🧩 Confere o pedido').first().json;
const p = $('🧩 Guarda os projetos').first().json;
const m = ($input.first().json || {}).data || {};
const passou = (Date.now() - p.inicio) / 1000;
let estado = 'montando', erro = '';
if (['failed', 'error', 'timed_out', 'cancelled', 'canceled'].includes(m.status)) { estado = 'erro'; erro = m.error_message || 'o ffmpeg na nuvem não conseguiu montar o vídeo'; }
else if (m.status === 'succeeded') estado = 'pronto';
else if (passou > 900) { estado = 'erro'; erro = 'O Very Good FFmpeg demorou mais de 15 minutos. Tente de novo.'; }
const saidas = m.output_files || {};
// a porcentagem segue o relógio (um vídeo de 30 s costuma levar uns 20 s) e nunca desce
const progresso = estado === 'montando' ? Math.min(95, Math.round(10 + passou * 2.5)) : 99;
const etapa = m.status === 'running' ? 'dando movimento às fotos, juntando voz, textos e trilha' : 'na fila do ffmpeg na nuvem';
const status = { job: v.job, etapa: 'montando', progresso, detalhe: `🎞️ ${etapa} · ${progresso}%`, op: v.op, dados: { titulo: v.dados.titulo, tipo: v.dados.tipo_txt } };
return [{ json: {
  estado, erro, terminou: estado !== 'montando', pronto: estado === 'pronto',
  video: saidas[`anuncio-${v.job}.mp4`] || '', video_musica: saidas[`anuncio-${v.job}-musica.mp4`] || '', capa: saidas[`anuncio-${v.job}.jpg`] || '',
  duracao: p.total || 0, tamanho_mb: m.total_output_bytes ? Math.round(m.total_output_bytes / 1e5) / 10 : 0, status: JSON.stringify(status),
} }];
