// Lê o andamento da edição no Very Good FFmpeg e decide se o laço continua.
const v = $('🧩 Pega o vídeo').first().json;
const p = $('🧩 Guarda o trabalho').first().json;
const m = ($input.first().json || {}).data || {};
const passou = (Date.now() - p.inicio) / 1000;
let estado = 'montando', erro = '';
if (['failed', 'error', 'timed_out', 'cancelled', 'canceled'].includes(m.status)) { estado = 'erro'; erro = m.error_message || 'o ffmpeg na nuvem não conseguiu editar o vídeo'; }
else if (m.status === 'succeeded') estado = 'pronto';
else if (passou > 900) { estado = 'erro'; erro = 'A edição demorou mais de 15 minutos. Tente de novo.'; }
const o = m.output_files || {};
const progresso = estado === 'montando' ? Math.min(95, Math.round(10 + passou * 1.5)) : 99;
const status = { job: v.job, etapa: 'montando', progresso, detalhe: `🎞️ ${m.status === 'running' ? 'cortando, legendando e mixando o som' : 'na fila do ffmpeg na nuvem'} · ${progresso}%` };
return [{ json: { estado, erro, terminou: estado !== 'montando', pronto: estado === 'pronto',
  video: o[`editado-${v.job}.mp4`] || '', capa: o[`capa-${v.job}.jpg`] || '', status: JSON.stringify(status) } }];
