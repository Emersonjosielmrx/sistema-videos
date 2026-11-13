// Junta as vozes guardadas: o endereço de cada uma (o próprio n8n entrega) e a duração, para montar o vídeo.
const v = $('🧩 Confere o pedido').first().json;
const cenas = $('🧩 Narra as falas (Google)').all().map(x => ({ n: x.json.n, url: v.arquivo + x.json.id, dur: x.json.dur }));
return [{ json: { cenas } }];
