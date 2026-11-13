// Guarda o código do trabalho que o Very Good FFmpeg aceitou (um trabalho só faz o narrado, o só música e a capa).
const r = $('🎬 Very Good FFmpeg: cria o vídeo').first().json || {};
const d = r.data || {};
if (!d.id) throw new Error('O Very Good FFmpeg recusou o vídeo: ' + String(r.message || r.errorCode || (r.error && r.error.message) || 'sem resposta').slice(0, 240));
return [{ json: { inicio: Date.now(), id: d.id, total: $('🧩 Monta o filme (Very Good FFmpeg)').first().json.total } }];
