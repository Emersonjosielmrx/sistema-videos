// Um item por cena para gerar as imagens uma por vez (o Code do n8n para em 60 s).
const v = $('🧩 Confere o pedido').first().json;
const r = $('🔎 Revisa os fatos').first().json;
const semente = Math.floor(Math.random() * 1e8);
// sufixo fixo: o Pollinations às vezes devolve colagem/grade de retratos quando a cena não tem assunto claro
const SUFIXO = ', ' + v.estilo_img + ', single scene, one subject, no collage, no grid, no text, no watermark';
return r.cenas.map((c, i) => ({ json: { job: v.job, n: i + 1, prompt: c.imagem + SUFIXO, formato: v.formato, semente: semente + i } }));
