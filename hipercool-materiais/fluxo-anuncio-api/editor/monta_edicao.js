// Monta a EDIÇÃO do vídeo que a pessoa gravou, no estilo do nosso vídeo de produto do Instagram:
//  1) cortes  — tira silêncios longos e vícios ("né", "é", "tipo", "ãh"...) usando o tempo de cada palavra
//  2) quadro  — põe em pé (9:16) com fundo desfocado se o vídeo for deitado, e um zoom leve que alterna a cada trecho
//  3) textos  — frase-gancho fixa no topo na cor da marca, tópicos numerados, legenda KARAOKÊ (a palavra falada acesa
//               na cor da marca), barrinha de progresso e cartão final (marca, chamada, @ e "Link no perfil")
//  4) áudio   — fala normalizada para Instagram (-14 LUFS) e trilha baixinha que abaixa quando a pessoa fala
// Tudo vira UM comando ffmpeg que roda na nuvem (Very Good FFmpeg).
const v = $('🧩 Pega o vídeo').first().json;
const ia = $('🧩 Lê a direção').first().json;            // gancho, tópicos, cartão, cor, trilha (da IA)
const dg = $('🎧 Deepgram: transcreve').first().json;     // palavras com tempo
const ex = $('🧩 Lê a extração').first().json;            // quadro: largura e altura (em pé ou deitado)
const info = { largura: ex.largura, altura: ex.altura, duracao: Number((dg.metadata || {}).duration) || 0 };
const W = 1080, H = 1920, FPS = 30, k = 1.5;               // 1080p no mínimo (padrão nosso); tamanhos das letras pensados em 720p, por isso k = 1,5
const FIM = v.op.cartao_final ? 2.8 : 0;                  // cartão final (s)
const TRILHAS = ['animado', 'calmo', 'chill', 'elegante', 'emocional', 'latino', 'tropical', 'urgente'];
const VICIOS = /^(n[ée]|é+|eh+|ãh+|ah+|hum+|hm+|tipo|então|assim|uh+|ahn|aham|mm+)$/i;
const limpa = s => String(s || '').replace(/[\u{1F000}-\u{1FAFF}☀-➿️‍]/gu, '').replace(/[{}\\]/g, '').replace(/\n/g, ' ').trim();
const clara = c => { const n = parseInt(String(c).slice(1), 16); return ((n >> 16) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000 > 150; };
const cor = /^#[0-9A-Fa-f]{6}$/.test(v.op.cor || ia.cor || '') ? (v.op.cor || ia.cor) : '#F59E0B';
const corTexto = clara(cor) ? '#111111' : '#FFFFFF';
const destaque = clara(cor) ? cor : '#FFD400';            // palavra falada: precisa aparecer sobre o vídeo
const ass = c => '&H00' + c.slice(5, 7) + c.slice(3, 5) + c.slice(1, 3) + '&';
const t2 = x => { x = Math.max(0, x); return `${Math.floor(x / 3600)}:${String(Math.floor(x % 3600 / 60)).padStart(2, '0')}:${(x % 60).toFixed(2).padStart(5, '0')}`; };

// ── 1) cortes ────────────────────────────────────────────────────────────────────────────────────────────────
const alt = (((dg.results || {}).channels || [])[0] || {}).alternatives || [];
let palavras = ((alt[0] || {}).words || []).map(w => ({ w: limpa(w.punctuated_word || w.word), s: +w.start, e: +w.end }));
const dur = Number(info.duracao) || (palavras.length ? palavras[palavras.length - 1].e + 0.5 : 0);
if (!dur) throw new Error('Não consegui ler o vídeo enviado.');
const falou = palavras.length >= 3;
const tirar = v.op.cortar_vicios ? palavras.filter(p => VICIOS.test(p.w.replace(/[.,!?;:]/g, ''))) : [];
const fica = palavras.filter(p => !tirar.includes(p));
const MARGEM = 0.12, PAUSA_MAX = v.op.cortar_pausas ? 0.45 : 99;
let trechos = [];
if (falou && fica.length) {
  let ini = Math.max(0, fica[0].s - MARGEM), fim = fica[0].e + MARGEM;
  for (let i = 1; i < fica.length; i++) {
    const p = fica[i], ant = fica[i - 1];
    const tirouNoMeio = tirar.some(t => t.s >= ant.e - 0.01 && t.e <= p.s + 0.01);
    if (p.s - ant.e > PAUSA_MAX || tirouNoMeio) {
      trechos.push([ini, fim]);
      ini = Math.max(fim, p.s - MARGEM);
    }
    fim = p.e + MARGEM;
  }
  trechos.push([ini, Math.min(dur, fim + 0.25)]);
} else {
  trechos = [[0, Math.min(dur, 59)]];   // sem fala: usa o vídeo inteiro (até 59 s)
}
trechos = trechos.filter(([a, b]) => b - a > 0.2);
// tempo novo de cada palavra (depois dos cortes) -> legenda e tópicos batem com a fala editada
const novo = [];
let ac = 0;
for (const [a, b] of trechos) {
  for (const p of fica) if (p.s >= a - 0.01 && p.e <= b + 0.01) novo.push({ w: p.w, s: ac + p.s - a, e: ac + p.e - a });
  ac += b - a;
}
const total = ac + FIM;
if (total > 90) throw new Error(`O vídeo editado ficou com ${Math.round(total)} s. Envie até 1 minuto e meio de fala.`);

// ── 2) quadro: cada trecho com zoom leve alternado; vídeo deitado vira em pé com fundo desfocado ────────────
const deitado = Number(info.largura) > Number(info.altura) * 1.05;
const f = [];
trechos.forEach(([a, b], i) => {
  const d = b - a, z0 = i % 2 ? 1.08 : 1.0, z1 = i % 2 ? 1.0 : 1.08;
  const zoom = `scale=w='trunc(${W}*(${z0}+(${z1}-${z0})*t/${d.toFixed(3)})/2)*2':h=-2:eval=frame,crop=${W}:${H}`;
  const base = deitado
    ? `split=2[bg${i}][fg${i}];[bg${i}]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=20:2[bgb${i}];[fg${i}]scale=${W}:-2[fgs${i}];[bgb${i}][fgs${i}]overlay=(W-w)/2:(H-h)/2`
    : `scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}`;
  f.push(`[0:v]trim=${a.toFixed(3)}:${b.toFixed(3)},setpts=PTS-STARTPTS,fps=${FPS},${base},${deitado ? 'null' : zoom},setsar=1,format=yuv420p[c${i}]`);
  f.push(`[0:a]atrim=${a.toFixed(3)}:${b.toFixed(3)},asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=0.02,afade=t=out:st=${Math.max(0, d - 0.03).toFixed(3)}:d=0.03[s${i}]`);
});
const n = trechos.length;
f.push(`${trechos.map((_, i) => `[c${i}][s${i}]`).join('')}concat=n=${n}:v=1:a=1[cv][ca]`);
if (FIM) {
  f.push(`[1:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=18:2,eq=brightness=-0.18,loop=loop=${Math.round(FIM * FPS)}:size=1:start=0,setpts=N/${FPS}/TB,fps=${FPS},setsar=1,format=yuv420p,trim=0:${FIM}[fimv]`);
  f.push(`[cv][fimv]concat=n=2:v=1:a=0[vb]`);
  f.push(`[ca]apad=pad_dur=${FIM}[fala]`);
} else {
  f.push(`[cv]null[vb]`);
  f.push(`[ca]anull[fala]`);
}
// out_range=tv: a foto do cartão final (JPEG) deixava o vídeo marcado como yuvj420p (faixa "cheia"); celular/Instagram querem yuv420p
f.push(`[vb]ass={{in_textos}}:fontsdir=inputs,scale=out_range=tv,format=yuv420p,split=2[vid][vcapa]`);
f.push(`[vcapa]trim=start=${Math.min(1.0, total / 3).toFixed(2)},setpts=PTS-STARTPTS[capa]`);
// áudio: fala no padrão do Instagram, trilha embaixo abaixando quando há voz
f.push(`[fala]highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11,asplit=2[f1][f2]`);
const trilha = v.op.trilha !== 'nenhuma';
if (trilha) {
  f.push(`[2:a]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:${total.toFixed(2)},volume=0.22,afade=t=out:st=${Math.max(0, total - 1.5).toFixed(2)}:d=1.5[tr]`);
  f.push(`[tr][f1]sidechaincompress=threshold=0.04:ratio=10:attack=15:release=350[trb]`);
  f.push(`[trb][f2]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95[aud]`);
} else {
  f.push(`[f1]anull[aud]`);
  f.push(`[f2]anullsink`);
}

// ── 3) textos (.ass) ──────────────────────────────────────────────────────────────────────────────────────────
const fs = x => Math.round(x * k);
const grupos = [];
let cur = [];
for (const p of novo) {
  cur.push(p);
  if (cur.length >= 3 || cur.map(x => x.w).join(' ').length >= 18 || /[.!?,:]$/.test(p.w)) { grupos.push(cur); cur = []; }
}
if (cur.length) grupos.push(cur);
const ev = [];
const fimFala = total - FIM;
const gancho = limpa(ia.gancho || v.dados.titulo).toUpperCase();
if (gancho) ev.push(`Dialogue: 3,${t2(0.15)},${t2(fimFala)},Gancho,,0,0,0,,{\\fad(300,0)}${gancho}`);
// tópicos numerados no tempo da fala (a IA diz em que palavra cada um começa)
const topicos = (Array.isArray(ia.topicos) ? ia.topicos : []).slice(0, 4);
topicos.forEach((tp, i) => {
  const ini = (novo[Math.min(novo.length - 1, Math.max(0, Number(tp.palavra) || 0))] || { s: 0 }).s;
  const prox = topicos[i + 1] ? (novo[Math.min(novo.length - 1, Math.max(0, Number(topicos[i + 1].palavra) || 0))] || { s: fimFala }).s : fimFala;
  if (prox - ini > 0.8) ev.push(`Dialogue: 2,${t2(ini)},${t2(prox)},Topico,,0,0,0,,{\\fad(200,0)}{\\c${ass(destaque)}}${i + 1}{\\c&HFFFFFF&}  ${limpa(tp.texto)}`);
});
// legenda karaokê: o grupo aparece e a palavra falada acende na cor da marca
if (v.op.legendas && novo.length) {
  grupos.forEach((g, gi) => {
    const fimG = Math.min(gi + 1 < grupos.length ? grupos[gi + 1][0].s : g[g.length - 1].e + 0.4, g[g.length - 1].e + 0.6);
    g.forEach((p, j) => {
      const a = p.s, b = j + 1 < g.length ? g[j + 1].s : fimG;
      if (b - a < 0.02) return;
      // só as palavras em maiúscula (o código de cor {\c...} tem de ficar minúsculo)
      const txt = g.map((x, q) => q === j ? `{\\c${ass(destaque)}}${x.w.toUpperCase()}{\\c&HFFFFFF&}` : x.w.toUpperCase()).join(' ');
      ev.push(`Dialogue: 1,${t2(a)},${t2(b)},Legenda,,0,0,0,,${j === 0 ? '{\\fscx92\\fscy92\\t(0,120,\\fscx100\\fscy100)}' : ''}${txt}`);
    });
  });
}
// barrinha de progresso no topo
const P = 40;
for (let i = 0; i < P; i++) {
  const a = fimFala * i / P, b = fimFala * (i + 1) / P, larg = Math.round(W * (i + 1) / P);
  ev.push(`Dialogue: 4,${t2(a)},${t2(b)},Barra,,0,0,0,,{\\p1}m 0 0 l ${larg} 0 ${larg} ${fs(9)} 0 ${fs(9)}{\\p0}`);
}
// cartão final
if (FIM) {
  const a = fimFala + 0.15, b = total;
  const pos = (y, extra = '') => `{\\an5\\pos(${W / 2},${Math.round(H * y)})\\fad(250,0)${extra}}`;
  ev.push(`Dialogue: 2,${t2(a)},${t2(b)},Marca,,0,0,0,,${pos(0.33)}${limpa(v.dados.marca || v.dados.titulo).toUpperCase()}`);
  if (ia.cartao) ev.push(`Dialogue: 2,${t2(a + 0.2)},${t2(b)},Chamada,,0,0,0,,${pos(0.47)}${limpa(ia.cartao)}`);
  ev.push(`Dialogue: 2,${t2(a + 0.35)},${t2(b)},Contato,,0,0,0,,${pos(0.6)}${v.dados.instagram ? '@' + limpa(v.dados.instagram) : ''}`);
  ev.push(`Dialogue: 2,${t2(a + 0.45)},${t2(b)},Link,,0,0,0,,${pos(0.68)}Link no perfil`);
}
const estilo = (nome, tam, prim, borda, fundo, bs, out, sh, alinh, mv, extra = '') =>
  `Style: ${nome},Montserrat Black,${fs(tam)},${prim},${prim},${borda},${fundo},-1,0,0,0,100,100,${extra || 0},0,${bs},${fs(out)},${fs(sh)},${alinh},${fs(50)},${fs(50)},${mv},1`;
const cab = `[Script Info]\nScriptType: v4.00+\nPlayResX: ${W}\nPlayResY: ${H}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n` +
  'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n' +
  estilo('Gancho', 56, ass(corTexto), ass(cor), '&H80000000&', 3, 20, 4, 8, Math.round(H * 0.06), 1) + '\n' +
  estilo('Topico', 40, '&H00FFFFFF&', '&H28101010&', '&H00000000&', 3, 16, 0, 7, Math.round(H * 0.17)) + '\n' +
  estilo('Legenda', 74, '&H00FFFFFF&', '&H00000000&', '&H96000000&', 1, 7, 3, 2, Math.round(H * 0.2)) + '\n' +
  estilo('Barra', 10, ass(cor), ass(cor), ass(cor), 1, 0, 0, 7, 0) + '\n' +
  estilo('Marca', 78, '&H00FFFFFF&', '&H00000000&', '&H96000000&', 1, 5, 3, 5, 0, 2) + '\n' +
  estilo('Chamada', 62, ass(corTexto), ass(cor), '&H80000000&', 3, 22, 4, 5, 0) + '\n' +
  estilo('Contato', 50, '&H00FFFFFF&', '&H00000000&', '&H96000000&', 1, 4, 2, 5, 0) + '\n' +
  estilo('Link', 40, ass(destaque), '&H00000000&', '&H96000000&', 1, 4, 2, 5, 0) + '\n\n' +
  '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n';
const textos = cab + ev.join('\n') + '\n';

// ── 4) pedido para o Very Good FFmpeg (um trabalho: vídeo, capa) ─────────────────────────────────────────────
const input_files = {
  'in_video.mp4': v.video_url,
  'in_fundo.jpg': ex.quadro,
  'in_trilha.mp3': v.arquivo + 'trilha-' + (TRILHAS.includes(ia.trilha) ? ia.trilha : 'elegante'),
  'in_textos.ass': v.arquivo + 'textos-' + v.job + '.ass',
  'in_fonte.ttf': 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf',
};
const enc = `-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -color_range tv -r ${FPS} -c:a aac -b:a 160k -ar 48000 -movflags +faststart`;
const cmd = `-i inputs/in_video.mp4 -loop 1 -i inputs/in_fundo.jpg -i inputs/in_trilha.mp3 -filter_complex "${f.join(';').replace(/\{\{in_textos\}\}/g, 'inputs/in_textos.ass')}" ` +
  `-map "[vid]" -map "[aud]" ${enc} -t ${total.toFixed(2)} outputs/editado-${v.job}.mp4 -map "[capa]" -frames:v 1 -q:v 3 -update 1 outputs/capa-${v.job}.jpg`;
return [{ json: {
  corpo: JSON.stringify({ input_files, output_files: [`editado-${v.job}.mp4`, `capa-${v.job}.jpg`], machine: 'cpu', timeout_seconds: 300, ffmpeg_commands: [cmd] }),
  textos: Buffer.from(textos, 'utf8').toString('base64'),
  total: Math.round(total * 100) / 100, original: Math.round(dur * 100) / 100, cortes: n, tirou: tirar.map(t => t.w),
  fala: novo.map(p => p.w).join(' '),
} }];
