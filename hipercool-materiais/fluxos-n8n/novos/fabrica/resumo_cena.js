// Volta para o loop com o que a montagem precisa (a imagem em base64 segue junto para subir ao montador).
const g = $('🖼️ Gera a imagem da cena').first().json;
return [{ json: { n: g.n, ok: g.ok, ext: g.ext || '', tipo: g.tipo || '', motor: g.motor || '', erro: g.erro || '', b64: g.b64 || '' } }];
