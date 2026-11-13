// Guarda o código de cada vídeo que a JSON2Video aceitou (o narrado e, se pediu, o só com música) para o laço perguntar o andamento.
const pedidos = $('🧩 Monta o filme (JSON2Video)').all().map(x => x.json.versao);
const p = { inicio: Date.now() };
$input.all().forEach((it, i) => { if (it.json && it.json.success && it.json.project) p[pedidos[i]] = it.json.project; });
if (!p.narrado) {
  const r = $input.first().json || {};
  throw new Error('A JSON2Video recusou o vídeo: ' + String(r.message || (r.error && r.error.message) || 'sem resposta').slice(0, 240));
}
return [{ json: p }];
