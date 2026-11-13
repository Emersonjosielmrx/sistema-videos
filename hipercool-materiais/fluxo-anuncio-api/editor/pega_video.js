// Endereço do vídeo: o de exemplo (público) ou o que a página enviou (guardado no Redis com validade de 1 hora).
const v = $('🧩 Confere o pedido').first().json;
const url = v.exemplo || String(($input.first().json || {}).url || '');
if (!url) throw new Error('O vídeo enviado expirou (vale 1 hora). Envie de novo.');
return [{ json: { ...v, video_url: url } }];
