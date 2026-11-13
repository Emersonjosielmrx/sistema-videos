// Lê UM canal do YouTube sem login e sem chave: RSS público (15 vídeos mais novos com visualizações) e a página
// pública do canal pelo youtubei/browse (inscritos e nº de vídeos).
const c = $input.first().json;
const UA = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36' };
function numeroBR(txt) {
  const m = /([\d.,]+)\s*(mil|mi|bi)?/i.exec(String(txt || ''));
  if (!m) return null;
  let n = m[2] ? parseFloat(m[1].replace(/\./g, '').replace(',', '.')) : parseInt(m[1].replace(/[.,]/g, ''), 10);
  if (m[2]) n *= { mil: 1e3, mi: 1e6, bi: 1e9 }[m[2].toLowerCase()];
  return Math.round(n);
}
const ent = s => String(s).replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const out = { slug: c.slug, nome: c.nome, handle: c.handle, yt_id: c.yt_id, status: c.status, lido: new Date().toISOString(),
  ok: false, inscritos: null, videos: null, ultimos: [], erro: '' };
try {
  const xml = String(await this.helpers.httpRequest({ url: 'https://www.youtube.com/feeds/videos.xml?channel_id=' + c.yt_id,
    headers: UA, timeout: 20000 }));
  for (const e of xml.split('<entry>').slice(1)) {
    const id = (/<yt:videoId>([^<]+)</.exec(e) || [])[1];
    if (!id) continue;
    out.ultimos.push({ id, titulo: ent((/<title>([^<]*)</.exec(e) || [])[1] || ''),
      publicado: (/<published>([^<]+)</.exec(e) || [])[1] || '',
      views: Number((/<media:statistics views="(\d+)"/.exec(e) || [])[1] || 0),
      short: /\/shorts\//.test((/<link rel="alternate" href="([^"]+)"/.exec(e) || [])[1] || '') });
  }
  out.ok = true;
} catch (e) {
  out.erro = 'RSS: ' + String(e.message || e).slice(0, 100);
}
try {
  const t = JSON.stringify(await this.helpers.httpRequest({ method: 'POST', json: true, timeout: 25000, headers: UA,
    url: 'https://www.youtube.com/youtubei/v1/browse?prettyPrint=false',
    body: { context: { client: { clientName: 'WEB', clientVersion: '2.20251020.01.00', hl: 'pt', gl: 'BR' } }, browseId: c.yt_id } }));
  const insc = /"content":"([^"]{1,40}inscrit[^"]{0,20})"/.exec(t) || /"accessibilityLabel":"([^"]{1,60}inscrit[^"]{0,30})"/.exec(t);
  const vids = /"content":"([^"]{1,30}v[ií]deos?)"/.exec(t);
  out.inscritos = insc ? (/nenhum/i.test(insc[1]) ? 0 : numeroBR(insc[1])) : null;
  out.videos = vids ? numeroBR(vids[1]) : null;
  out.ok = true;
} catch (e) {
  out.erro += (out.erro ? ' · ' : '') + 'página: ' + String(e.message || e).slice(0, 100);
}
return [{ json: out }];
