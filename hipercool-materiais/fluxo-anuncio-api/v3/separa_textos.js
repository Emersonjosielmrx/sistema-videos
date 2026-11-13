// Os textos do vídeo (manchetes, preço, legenda e cartão final) vão num arquivo .ass que o ffmpeg lê por endereço:
// um com legenda (narrado) e um sem (só música). Ficam no Redis e o próprio n8n entrega.
const v = $('🧩 Confere o pedido').first().json;
const m = $input.first().json;
return [
  { json: { id: `textos-${v.job}.ass`, b64: m.textos } },
  { json: { id: `textos-${v.job}-m.ass`, b64: m.textos_musica } },
];
