// Confere se o vídeo subiu e devolve o código do envio para a página (o endereço de leitura vale 1 hora).
const lugar = $('🧩 Junta o vídeo e o lugar').first().json || {};
const subiu = $input.first().json || {};
if (lugar.semLugar || !lugar.download_url) return [{ json: { ok: false, erro: 'Não deu para guardar o vídeo agora (o ffmpeg na nuvem não respondeu). Tente de novo.' } }];
if (subiu.error) return [{ json: { ok: false, erro: 'O envio do vídeo falhou. Tente de novo.' } }];
const id = require('crypto').randomBytes(6).toString('hex');
return [{ json: { ok: true, id, url: lugar.download_url } }];
