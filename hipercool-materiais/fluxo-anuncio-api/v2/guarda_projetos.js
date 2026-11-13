// Guarda o código de cada vídeo que o Shotstack aceitou (o narrado e, se pediu, o só com música) para o laço perguntar o andamento.
const pedidos = $('🧩 Monta o filme (Shotstack)').all().map(x => x.json);
const p = { inicio: Date.now(), ambiente: pedidos[0].ambiente };
$input.all().forEach((it, i) => {
  const r = it.json || {};
  if (r.success && r.response && r.response.id) p[pedidos[i].versao] = r.response.id;
});
if (!p.narrado) {
  const r = $input.first().json || {};
  const motivo = (r.response && (r.response.error || r.response.message)) || r.message || (r.error && r.error.message) || 'sem resposta';
  throw new Error('O Shotstack recusou o vídeo: ' + String(motivo).slice(0, 240));
}
return [{ json: p }];
