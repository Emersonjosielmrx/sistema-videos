// Monta a EDIÇÃO do vídeo que a pessoa gravou — versão com mais recursos de edição:
//  cortes   — tira silêncios (> 0,35 s) e vícios ("né", "é", "tipo"...) pelo tempo de cada palavra; fala lenta ganha
//             ritmo (1,06x, sem mudar o tom da voz)
//  imagem   — 1080x1920; "jump cut" de zoom a cada frase (alterna perto/longe), zoom de impacto na abertura, cor e
//             nitidez realçadas, vinheta leve; vídeo deitado vira em pé com fundo desfocado
//  textos   — frase de ABERTURA grande no meio (2 s), gancho fixo no topo, tópicos numerados que entram deslizando,
//             flash na troca de tópico, legenda karaokê com a palavra falada pulando e as PALAVRAS-CHAVE na cor de
//             destaque, chamada "Siga @" no meio, barrinha de progresso e cartão final animado
//  som      — voz limpa (tira chiado, compressor) a -14 LUFS, trilha que abaixa quando fala, efeitos: impacto na
//             abertura, whoosh nos tópicos e no cartão final, pop nas palavras-chave
//  NIVEL 3  — + emoji que pula na tela em cada palavra-chave, zoom rápido na palavra-chave e glitch na troca de tópico
// Tudo vira UM comando ffmpeg que roda na nuvem (Very Good FFmpeg).
const NIVEL = __NIVEL__;
const v = $('🧩 Pega o vídeo').first().json;
const ia = $('🧩 Lê a direção').first().json;            // abertura, gancho, tópicos, destaques, cartão, cor, trilha
const dg = $('🎧 Deepgram: transcreve').first().json;     // palavras com tempo
const ex = $('🧩 Lê a extração').first().json;            // quadro: largura e altura (em pé ou deitado)
const info = { largura: ex.largura, altura: ex.altura, duracao: Number((dg.metadata || {}).duration) || 0 };
const W = 1080, H = 1920, FPS = 30, k = 1.5;               // 1080p; tamanhos das letras pensados em 720p (k = 1,5)
const FIM = v.op.cartao_final ? 3.2 : 0;                  // cartão final (s)
const ABRE = 1.9;                                         // frase de abertura no meio da tela (s)
const TRILHAS = ['animado', 'calmo', 'chill', 'elegante', 'emocional', 'latino', 'tropical', 'urgente'];
const VICIOS = /^(n[ée]|é+|eh+|ãh+|ah+|hum+|hm+|tipo|então|assim|uh+|ahn|aham|mm+)$/i;
const limpa = s => String(s || '').replace(/[\u{1F000}-\u{1FAFF}☀-➿️‍]/gu, '').replace(/[{}\\]/g, '').replace(/\n/g, ' ').trim();
const clara = c => { const n = parseInt(String(c).slice(1), 16); return ((n >> 16) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000 > 150; };
const cor = /^#[0-9A-Fa-f]{6}$/.test(v.op.cor || ia.cor || '') ? (v.op.cor || ia.cor) : '#F59E0B';
const corTexto = clara(cor) ? '#111111' : '#FFFFFF';
const destaque = clara(cor) ? cor : '#FFD400';            // palavra falada / palavra-chave: precisa aparecer sobre o vídeo
const ass = c => '&H00' + c.slice(5, 7) + c.slice(3, 5) + c.slice(1, 3) + '&';
const t2 = x => { x = Math.max(0, x); return `${Math.floor(x / 3600)}:${String(Math.floor(x % 3600 / 60)).padStart(2, '0')}:${(x % 60).toFixed(2).padStart(5, '0')}`; };
const n2 = x => x.toFixed(2);
// ── V6: os cards viram desenhos SVG (cantos redondos, degradê, brilho, borda clara e sombra) que o ffmpeg da nuvem lê
// (librsvg, testado 03/11); o .ass fica só com os textos por cima. Cada card = SVG + lugar + tempo + animação de entrada.
const SVGC = NIVEL >= 6;
const tom = (c, p) => '#' + [1, 3, 5].map(j => { const x = parseInt(c.slice(j, j + 2), 16); return Math.round(p >= 0 ? x + (255 - x) * p : x * (1 + p)).toString(16).padStart(2, '0'); }).join('');
const MG = 48;                                            // folga em volta do card para a sombra
const DY = 46, DX = 70;                                   // quanto o card (e o texto dele) anda ao entrar, em 0,25 s
const defs = (c1, c2, sombra, op = 0.5, vertical = false) => `<defs><linearGradient id="g" x1="0" y1="0" x2="${vertical ? 0 : 1}" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient>` +
  `<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".36"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>` +
  `<filter id="s" x="-30%" y="-40%" width="160%" height="200%"><feDropShadow dx="0" dy="12" stdDeviation="14" flood-color="${sombra}" flood-opacity="${op}"/></filter></defs>`;
const R = (w, h, r, extra) => `<rect width="${Math.round(w)}" height="${Math.round(h)}" rx="${Math.round(r)}" ${extra}/>`;
const contorno = (w, h, r, op = 0.35) => `<rect x="1.5" y="1.5" width="${Math.round(w - 3)}" height="${Math.round(h - 3)}" rx="${Math.round(Math.max(0, r - 1.5))}" fill="none" stroke="#fff" stroke-opacity="${op}" stroke-width="3"/>`;
const pilula = (w, h, r, c, sombra = '#000', op = 0.5) => defs(tom(c, 0.25), tom(c, -0.2), sombra, op) +
  R(w, h, r, 'fill="url(#g)" filter="url(#s)"') + R(w, h, r, 'fill="url(#b)"') + contorno(w, h, r);
const cards = [];
const card = (x, y, w, h, a, b, corpo, anim = 'sobe', saida = 0) => {
  const L = Math.round(w + 2 * MG), A = Math.round(h + 2 * MG);
  cards.push({ svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${L}" height="${A}" viewBox="${-MG} ${-MG} ${L} ${A}">${corpo}</svg>`,
    x: Math.round(x - MG), y: Math.round(y - MG), w: L, h: A, a, b, anim, saida });
};
// texto que entra junto com o card (mesmo caminho e tempo)
const mv = (x, y, anim) => anim === 'esq' ? `\\move(${Math.round(x - DX)},${Math.round(y)},${Math.round(x)},${Math.round(y)},0,250)`
  : anim === 'sobe' ? `\\move(${Math.round(x)},${Math.round(y + DY)},${Math.round(x)},${Math.round(y)},0,250)` : `\\pos(${Math.round(x)},${Math.round(y)})`;

// ── 1) cortes ────────────────────────────────────────────────────────────────────────────────────────────────
const alt = (((dg.results || {}).channels || [])[0] || {}).alternatives || [];
const palavras = ((alt[0] || {}).words || []).map(w => ({ w: limpa(w.punctuated_word || w.word), s: +w.start, e: +w.end }));
const dur = Number(info.duracao) || (palavras.length ? palavras[palavras.length - 1].e + 0.5 : 0);
if (!dur) throw new Error('Não consegui ler o vídeo enviado.');
const falou = palavras.length >= 3;
const tirar = v.op.cortar_vicios ? palavras.filter(p => VICIOS.test(p.w.replace(/[.,!?;:]/g, ''))) : [];
const fica = palavras.filter(p => !tirar.includes(p));
const MARGEM = 0.08, PAUSA_MAX = v.op.cortar_pausas ? 0.35 : 99;
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
// ritmo: fala lenta (< 2,7 palavras/s) fica 6% mais rápida, sem mudar o tom (atempo)
const falaOrig = trechos.reduce((s, [a, b]) => s + b - a, 0);
const SP = falou && fica.length / Math.max(1, falaOrig) < 2.7 ? 1.06 : 1;
if (SVGC) {   // V6: vídeo comprido demais não dá mais erro: fica só o começo (até ~88 s editado), cortado no fim de uma palavra
  const MAXF = (88 - FIM) * SP;
  let soma = 0;
  const cabem = [];
  for (const [a, b] of trechos) {
    if (soma + (b - a) <= MAXF) { cabem.push([a, b]); soma += b - a; continue; }
    const ult = fica.filter(p => p.s >= a && p.e <= a + (MAXF - soma)).pop();
    if (ult && MAXF - soma > 1.5) cabem.push([a, ult.e + MARGEM]);
    break;
  }
  trechos = cabem;
}
// tempo novo de cada palavra (depois dos cortes e do ritmo); i = número da palavra (o mesmo que a IA usou)
const novo = [], juntas = [];
let ac = 0;
for (const [a, b] of trechos) {
  fica.forEach((p, i) => { if (p.s >= a - 0.01 && p.e <= b + 0.01) novo.push({ w: p.w, i, s: (ac + p.s - a) / SP, e: (ac + p.e - a) / SP }); });
  ac += b - a;
  juntas.push(ac / SP);
}
const fala = ac / SP, total = fala + FIM;
if (total > 90) throw new Error(`O vídeo editado ficou com ${Math.round(total)} s. Envie até 1 minuto e meio de fala.`);
const tempoDa = idx => { const p = novo.find(x => x.i >= idx); return p ? p.s : null; };

// tópicos e palavras-chave no tempo novo
const topicos = (Array.isArray(ia.topicos) ? ia.topicos : []).slice(0, 4).map(tp => ({ ...tp, t: tempoDa(Number(tp.palavra) || 0) }))
  .filter(tp => tp.t !== null && tp.t < fala - 0.8);
const chaves = (Array.isArray(ia.destaques) ? ia.destaques : []).map(d => ({ ...d, p: novo.find(x => x.i === d.palavra) }))
  .filter(d => d.p && d.p.s > ABRE * 0.5 && d.p.s < fala - 0.6);
const ehChave = new Set(chaves.map(d => d.p.i));

// planos (jump cut de zoom): uma troca a cada frase / corte, de 1,6 s a 4,5 s
const bordas = new Set(juntas.slice(0, -1).map(t => +t.toFixed(2)));
novo.forEach((p, j) => { if (/[.!?,;:]$/.test(p.w) && novo[j + 1]) bordas.add(+((p.e + novo[j + 1].s) / 2).toFixed(2)); });
const planos = [];
let ini = 0;
for (const b of [...[...bordas].filter(x => x > 0 && x < fala).sort((x, y) => x - y), fala]) {
  if (b - ini >= 1.6) { planos.push([ini, b]); ini = b; }
}
if (ini < fala) { if (planos.length) planos[planos.length - 1][1] = fala; else planos.push([0, fala]); }
const cenas = [];
planos.forEach(([a, b]) => { const n = Math.ceil((b - a) / 4.5); for (let q = 0; q < n; q++) cenas.push([a + (b - a) * q / n, a + (b - a) * (q + 1) / n]); });

// ── 2) imagem ────────────────────────────────────────────────────────────────────────────────────────────────
// V6: vídeo deitado com rosto conhecido = corte EM PÉ centrado na pessoa (como um editor faria), em vez da faixa no meio
// com fundo desfocado; daí em diante ele é tratado como vídeo em pé
const deitadoOrig = Number(info.largura) > Number(info.altura) * 1.05;
const corta = SVGC && deitadoOrig && typeof ia.rosto_x === 'number';
const deitado = deitadoOrig && !corta;
const cortaX = corta ? Math.round(Math.min(Math.max(ia.rosto_x * (Number(info.largura) * H / Number(info.altura)) - W / 2, 0),
  Number(info.largura) * H / Number(info.altura) - W)) : 0;
const f = [];
trechos.forEach(([a, b], i) => {
  const d = b - a;
  const base = corta ? `scale=-2:${H},crop=${W}:${H}:${cortaX}:0` : deitado
    ? `split=2[bg${i}][fg${i}];[bg${i}]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=20:2[bgb${i}];[fg${i}]scale=${W}:-2[fgs${i}];[bgb${i}][fgs${i}]overlay=(W-w)/2:(H-h)/2`
    : `scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}`;
  f.push(`[0:v]trim=${a.toFixed(3)}:${b.toFixed(3)},setpts=PTS-STARTPTS,fps=${FPS},${base},setsar=1,format=yuv420p[c${i}]`);
  f.push(`[0:a]atrim=${a.toFixed(3)}:${b.toFixed(3)},asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=0.02,afade=t=out:st=${Math.max(0, d - 0.03).toFixed(3)}:d=0.03[s${i}]`);
});
const n = trechos.length;
f.push(`${trechos.map((_, i) => `[c${i}][s${i}]`).join('')}concat=n=${n}:v=1:a=1[cv0][ca0]`);
// zoom: impacto na abertura (1,22 -> 1,0 em 0,4 s) + nível alternado por plano com leve aproximação contínua
const fz = deitado || corta ? 0.5 : 1;   // vídeo deitado cortado em pé já vem aproximado: zoom pela metade
const NIV = [0, 0.14, 0.06, 0.2];
let Z = `1+0.22*max(0,1-t/0.4)` + cenas.map(([a, b], q) =>
  `+gte(t,${n2(a)})*lt(t,${n2(b)})*(${(NIV[q % 4] * fz).toFixed(3)}+0.03*(t-${n2(a)})/${n2(Math.max(0.1, b - a))})`).join('');
if (NIVEL >= 3) Z += chaves.map(c => `+gte(t,${n2(c.p.s)})*lt(t,${n2(c.p.s + 0.45)})*${(0.08 * fz).toFixed(3)}`).join('');
f.push(`[cv0]setpts=(PTS-STARTPTS)/${SP},fps=${FPS},eq=contrast=1.06:saturation=1.16:brightness=0.012,` +
  `scale=w='2*trunc(${W}*(${Z})/2)':h=-2:eval=frame,crop=${W}:${H}:(in_w-${W})/2:(in_h-${H})*${corta ? 0.12 : 0.35},` +
  `unsharp=5:5:0.45,vignette=angle=PI/6,setsar=1,format=yuv420p[cvz]`);
f.push(SP === 1 ? `[ca0]anull[ca]` : `[ca0]atempo=${SP}[ca]`);
if (FIM) {
  f.push(`[1:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=18:2,eq=brightness=${NIVEL >= 4 ? -0.32 : -0.18},loop=loop=${Math.round(FIM * FPS)}:size=1:start=0,setpts=N/${FPS}/TB,fps=${FPS},setsar=1,format=yuv420p,trim=0:${FIM}[fimv]`);
  f.push(`[cvz][fimv]concat=n=2:v=1:a=0[vb0]`);
  f.push(`[ca]apad=pad_dur=${FIM}[fala]`);
} else {
  f.push(`[cvz]null[vb0]`);
  f.push(`[ca]anull[fala]`);
}
// glitch (só nível 3) na troca de tópico: separa as cores por 0,15 s
const trocas = topicos.map(tp => tp.t).filter(t => t > 0.5);
if (NIVEL >= 3 && trocas.length) {
  f.push(`[vb0]rgbashift=rh=-18:bh=18:enable='${trocas.map(t => `between(t,${n2(t)},${n2(t + 0.15)})`).join('+')}'[vb]`);
} else {
  f.push(`[vb0]null[vb]`);
}
// emojis (só nível 3): pulam ao lado da legenda em cada palavra-chave
const emojis = NIVEL >= 3 ? chaves.filter(c => c.emoji).slice(0, 5) : [];
let atual = 'vass';
f.push(SVGC ? '__CARDS__' : `[vb]ass={{in_textos}}:fontsdir=inputs[vass]`);   // V6: os cards entram aqui (por baixo dos textos)
emojis.forEach((c, q) => {
  const a = c.p.s, b = Math.min(a + 1.5, fala);
  const y = Math.round(H * 0.5);
  f.push(`[${3 + q}:v]scale=240:240,format=rgba,fade=t=in:st=${n2(a)}:d=0.12:alpha=1,fade=t=out:st=${n2(b - 0.2)}:d=0.2:alpha=1[e${q}]`);
  f.push(`[${atual}][e${q}]overlay=x=${W - 300}:y='${y}-70*max(0,1-(t-${n2(a)})/0.22)':enable='between(t,${n2(a)},${n2(b)})'[ve${q}]`);
  atual = `ve${q}`;
});
// out_range=tv: a foto do cartão final (JPEG) deixava o vídeo marcado como yuvj420p; celular/Instagram querem yuv420p
f.push(`[${atual}]scale=out_range=tv,format=yuv420p,split=2[vid][vcapa]`);
f.push(`[vcapa]trim=start=1.0,setpts=PTS-STARTPTS[capa]`);

// ── 3) som ───────────────────────────────────────────────────────────────────────────────────────────────────
f.push(`[fala]highpass=f=80,afftdn=nr=10:nf=-40,acompressor=threshold=0.08:ratio=3:attack=8:release=150:makeup=1.5,loudnorm=I=-14:TP=-1.5:LRA=9,asplit=2[f1][f2]`);
if (v.op.trilha !== 'nenhuma') {
  f.push(`[2:a]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:${total.toFixed(2)},volume=0.22,afade=t=out:st=${Math.max(0, total - 1.5).toFixed(2)}:d=1.5[tr]`);
  f.push(`[tr][f1]sidechaincompress=threshold=0.04:ratio=10:attack=15:release=350[trb]`);
  f.push(`[trb][f2]amix=inputs=2:normalize=0:duration=longest[mix0]`);
} else {
  f.push(`[f1]anull[mix0]`);
  f.push(`[f2]anullsink`);
}
// efeitos sonoros feitos no próprio ffmpeg (sem arquivo): impacto, whoosh e pop
const SOM = {
  impacto: `sine=f=65:r=48000:d=0.45,afade=t=out:st=0.05:d=0.4,volume=0.9`,
  whoosh: `anoisesrc=d=0.5:c=pink:r=48000:a=0.5,highpass=f=300,lowpass=f=5000,afade=t=in:d=0.3:curve=exp,afade=t=out:st=0.3:d=0.2,volume=0.35`,
  pop: `sine=f=1100:r=48000:d=0.09,afade=t=out:st=0.01:d=0.08,volume=0.3`,
};
const efeitos = [{ s: 'impacto', t: 0 }, ...trocas.map(t => ({ s: 'whoosh', t: t - 0.3 })), ...chaves.map(c => ({ s: 'pop', t: c.p.s }))];
if (FIM) efeitos.push({ s: 'whoosh', t: fala - 0.3 });
efeitos.forEach((e, q) => {
  const ms = Math.max(0, Math.round(e.t * 1000));
  f.push(`${SOM[e.s]},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${ms}|${ms}[x${q}]`);
});
f.push(`[mix0]${efeitos.map((_, q) => `[x${q}]`).join('')}amix=inputs=${efeitos.length + 1}:normalize=0:duration=first,alimiter=limit=0.95[aud]`);

// ── 4) textos (.ass) ──────────────────────────────────────────────────────────────────────────────────────────
const fs = x => Math.round(x * k);
const grupos = [];
let cur = [];
for (const p of novo) {
  cur.push(p);
  if (cur.length >= 3 || cur.map(x => x.w).join(' ').length >= 18 || /[.!?,:]$/.test(p.w)) { grupos.push(cur); cur = []; }
}
if (cur.length) grupos.push(cur);
const ev = [];
let mixModo = '';
const abertura = limpa(ia.abertura || ia.gancho || v.dados.titulo).toUpperCase();
const gancho = limpa(ia.gancho || v.dados.titulo).toUpperCase();
const yT = Math.round(H * 0.17);
if (NIVEL >= 4) {
  // ═══ V4: legenda MIX + cards dos nossos vídeos de propaganda (D:\ms-energy\bin\montagem_ms.py, aprovados 01/11) ═══
  const rr = (x0, y0, x1, y1, r) => {
    [x0, y0, x1, y1, r] = [x0, y0, x1, y1, r].map(Math.round);
    return `m ${x0 + r} ${y0} l ${x1 - r} ${y0} b ${x1} ${y0} ${x1} ${y0} ${x1} ${y0 + r} l ${x1} ${y1 - r} b ${x1} ${y1} ${x1} ${y1} ${x1 - r} ${y1} ` +
      `l ${x0 + r} ${y1} b ${x0} ${y1} ${x0} ${y1} ${x0} ${y1 - r} l ${x0} ${y0 + r} b ${x0} ${y0} ${x0} ${y0} ${x0 + r} ${y0}`;
  };
  const roda = (cx, cy, r) => { const q = r * 0.5523, a = [cx, cy, r, q].map(Math.round); [cx, cy, r] = a; const c = a[3];
    return `m ${cx} ${cy - r} b ${cx + c} ${cy - r} ${cx + r} ${cy - c} ${cx + r} ${cy} b ${cx + r} ${cy + c} ${cx + c} ${cy + r} ${cx} ${cy + r} ` +
      `b ${cx - c} ${cy + r} ${cx - r} ${cy + c} ${cx - r} ${cy} b ${cx - r} ${cy - c} ${cx - c} ${cy - r} ${cx} ${cy - r}`; };
  const LARG = { 'Montserrat Black': 0.70, 'Luckiest Guy': 0.66, 'Bangers': 0.48, 'Anton': 0.46 };
  // largura média por letra (medida); texto com minúsculas é ~15% mais estreito que em CAIXA ALTA
  const larg = (t, sz, fn) => String(t).length * sz * (LARG[fn] || 0.65) * (/[a-zà-ú]/.test(String(t)) ? 0.78 : 1);
  const quebra = (t, sz, fn, max) => { const ls = []; let l = ''; for (const p of String(t).split(/\s+/)) { const c = l ? l + ' ' + p : p; if (l && larg(c, sz, fn) > max) { ls.push(l); l = p; } else l = c; } if (l) ls.push(l); return ls; };
  const desenho = (camada, a, b, cor1, caminho, extra = '') =>
    `Dialogue: ${camada},${t2(a)},${t2(b)},Mix,,0,0,0,,{\\an7\\pos(0,0)\\bord0\\shad0\\1c${ass(cor1)}${extra}\\p1}${caminho}{\\p0}`;
  const texto = (camada, a, b, x, y, an, sz, cor1, txt, extra = '', fn = 'Montserrat Black', anim = '') =>
    `Dialogue: ${camada},${t2(a)},${t2(b)},Mix,,0,0,0,,{\\an${an}${anim ? mv(x, y, anim) : `\\pos(${Math.round(x)},${Math.round(y)})`}\\fn${fn}\\fs${Math.round(sz)}\\bord0\\shad0\\1c${ass(cor1)}${extra}}${txt}`;
  const sobe = SVGC ? 'sobe' : '', esq = SVGC ? 'esq' : '';   // V6: o texto entra junto com o card
  const fimAbre = Math.min(2.6, fala);                     // gancho de 0 a 2,6 s, como no montar() do PC
  // rosto (a IA mede no quadro) levado para a tela final, com folga para cabelo e queixo como o rosto_faixa do PC
  let rosto = null;
  if (Array.isArray(ia.rosto)) {
    const sw = Number(info.largura) || W, sh = Number(info.altura) || H;
    const yTela = fr => deitado ? (H - W * sh / sw) / 2 + fr * W * sh / sw
      : fr * sh * Math.max(W / sw, H / sh) - (sh * Math.max(W / sw, H / sh) - H) / 2;
    const t0 = yTela(ia.rosto[0]), b0 = yTela(ia.rosto[1]), fh = b0 - t0;
    rosto = [Math.max(0, t0 - fh * 0.45), Math.min(H, b0 + fh * 0.15)];
  }
  // altura do card: o lugar livre que menos encosta no rosto, nunca sobre a legenda (_y_pergunta do PC)
  const yLivre = alto => {
    if (!rosto) return 225;
    const [ft, fb] = rosto, lim = H * 0.64 - 18 - alto;
    const c = [225, 105, fb + 30, ft - 30 - alto].filter(y => y >= 0 && y <= lim);
    return (c.length ? c : [105]).sort((p, q) => Math.max(0, Math.min(p + alto, fb) - Math.max(p, ft)) - Math.max(0, Math.min(q + alto, fb) - Math.max(q, ft)) || (p !== 225) - (q !== 225))[0];
  };
  // abertura: PERGUNTA vira o card branco "responder comentário" do Instagram; frase vira a faixa arredondada na cor da marca
  const abre = limpa(ia.abertura || ia.gancho || v.dados.titulo);
  if (abre.endsWith('?')) {
    const fq = 81, linhas = quebra(abre, fq, 'Montserrat Black', W - 240), ROT = 'Pergunta que a gente sempre recebe';
    const lg = Math.max(...linhas.map(l => larg(l, fq, 'Montserrat Black')), larg(ROT, 36, 'Montserrat Black') + 84);
    const altoC = 99 + 99 * linhas.length + 30;
    const x0 = (W - lg) / 2 - 45, y0 = yLivre(altoC + 36), x1 = x0 + lg + 90, y1 = y0 + altoC;
    const fad = '\\fad(150,220)';
    if (SVGC) {   // balão branco com bico, brilho de cima para baixo, sombra e bolinha da marca em degradê
      const w = x1 - x0, h = y1 - y0;
      card(x0, y0, w, h + 36, 0, fimAbre, defs('#FFFFFF', '#F3F4F8', '#000', 0.45, true) +
        `<g filter="url(#s)">${R(w, h, 46, 'fill="#F3F4F8"')}<path d="M 84 ${Math.round(h - 4)} L 142 ${Math.round(h - 4)} L 93 ${Math.round(h + 36)} Z" fill="#F3F4F8"/></g>` +
        R(w, h, 46, 'fill="url(#g)"') + `<circle cx="64" cy="50" r="23" fill="${tom(cor, -0.15)}"/><circle cx="64" cy="50" r="23" fill="url(#b)"/>` +
        `<circle cx="64" cy="50" r="21" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>`, 'sobe', 0.22);
    } else {
      ev.push(desenho(8, 0, fimAbre, '#000000', rr(x0 + 5, y0 + 9, x1 + 5, y1 + 9, 42), `\\1a&H88&\\blur10${fad}`));
      ev.push(desenho(9, 0, fimAbre, '#FFFFFF', rr(x0, y0, x1, y1, 42) + ` m ${Math.round(x0 + 87)} ${Math.round(y1 - 1)} l ${Math.round(x0 + 138)} ${Math.round(y1 - 1)} l ${Math.round(x0 + 93)} ${Math.round(y1 + 36)}`, `\\1a&H08&${fad}`));
      ev.push(desenho(10, 0, fimAbre, cor, roda(x0 + 64, y0 + 50, 22), fad));
    }
    ev.push(texto(10, 0, fimAbre, x0 + 104, y0 + 50, 4, 36, '#696973', ROT, fad, undefined, sobe));
    linhas.forEach((l, q) => ev.push(texto(10, 0, fimAbre, W / 2, y0 + 93 + q * 99, 8, fq, '#16161A', l, fad, undefined, sobe)));
  } else if (abertura) {
    const fz2 = 90, linhas = quebra(abertura, fz2, 'Montserrat Black', W - 210), alto = 111 * linhas.length;
    const lg = Math.max(...linhas.map(l => larg(l, fz2, 'Montserrat Black')));
    const x0 = (W - lg) / 2 - 51, y0 = yLivre(alto + 54);
    const fad = '\\fad(120,220)';
    if (SVGC) card(x0, y0, lg + 102, alto + 54, 0, fimAbre, pilula(lg + 102, alto + 54, 44, cor), 'sobe', 0.22);
    else {
      ev.push(desenho(8, 0, fimAbre, '#000000', rr(x0 + 5, y0 + 9, x0 + lg + 107, y0 + alto + 63, 39), `\\1a&H88&\\blur10${fad}`));
      ev.push(desenho(9, 0, fimAbre, cor, rr(x0, y0, x0 + lg + 102, y0 + alto + 54, 39), `\\1a&H14&${fad}`));
    }
    linhas.forEach((l, q) => ev.push(texto(10, 0, fimAbre, W / 2, y0 + 24 + q * 111, 8, fz2, corTexto, l, fad, undefined, sobe)));
  }
  // faixa de título fixa (layout "aula") + etiqueta da etapa (círculo com o número + texto) trocando com os tópicos
  const fb = 63, lb = quebra(gancho, fb, 'Montserrat Black', W - 230).slice(0, 2), caixaH = 78 * lb.length + 42;
  const lwb = Math.max(...lb.map(l => larg(l, fb, 'Montserrat Black')), 200), bx0 = Math.max(30, (W - lwb) / 2 - 39), by0 = 54;
  if (gancho && fala > fimAbre) {
    if (SVGC) card(bx0, by0, W - 2 * bx0, caixaH, fimAbre, fala, pilula(W - 2 * bx0, caixaH, Math.min(40, caixaH / 2), cor), 'sobe');
    else ev.push(desenho(3, fimAbre, fala, cor, rr(bx0, by0, W - bx0, by0 + caixaH, 21), '\\1a&H0A&\\fad(250,0)'));
    lb.forEach((l, q) => ev.push(texto(4, fimAbre, fala, W / 2, by0 + 21 + q * 78, 8, fb, corTexto, l, '\\fad(250,0)', undefined, sobe)));
  }
  const ey = by0 + caixaH + 21, eh = SVGC ? 66 : 60;
  topicos.forEach((tp, i) => {
    const a = Math.max(tp.t, fimAbre), b = topicos[i + 1] ? topicos[i + 1].t : fala, tx = limpa(tp.texto);
    if (b - a <= 0.8) return;
    const x1 = bx0 + eh + larg(tx, 33, 'Montserrat Black') + 45, fad = '\\fad(200,0)';
    if (SVGC) {   // etiqueta de vidro escuro com a bolinha do número em degradê da marca
      const w = x1 - bx0, r = eh / 2;
      card(bx0, ey, w, eh, a, b, defs(tom(cor, 0.3), tom(cor, -0.2), '#000', 0.45) +
        R(w, eh, r, 'fill="#10131B" fill-opacity=".86" filter="url(#s)"') + R(w, eh, r, 'fill="url(#b)" fill-opacity=".5"') + contorno(w, eh, r, 0.18) +
        `<circle cx="${r}" cy="${r}" r="${Math.round(eh * 0.37)}" fill="url(#g)"/><circle cx="${r}" cy="${r}" r="${Math.round(eh * 0.37)}" fill="url(#b)"/>`, 'esq');
    } else {
      ev.push(desenho(3, a, b, '#14181E', rr(bx0, ey, x1, ey + eh, 30), `\\1a&H22&${fad}`));
      ev.push(desenho(4, a, b, cor, roda(bx0 + 30, ey + 30, 21), fad));
    }
    ev.push(texto(5, a, b, bx0 + eh / 2, ey + eh / 2 + 1, 5, 33, corTexto, String(i + 1), fad, undefined, esq));
    ev.push(texto(5, a, b, bx0 + eh + 12, ey + eh / 2 + 1, 4, 33, '#FFFFFF', tx, fad, undefined, esq));
  });
  // legenda MIX: palavras curtas se juntam à próxima forte; cada bloco tem desenho, cor, fonte, giro, pop e lugar próprios
  if (v.op.legendas && novo.length) {
    const CURTAS = new Set('a o e é de do da dos das em no na nos nas um uma que com pra para por se seu sua te eu ao à os as ou mas não já tem vai só isso essa esse ela ele me mais muito quem como'.split(' '));
    const FORTES = new Set('conta luz economia economizar grátis solar sol energia orçamento telhado parcela zero nunca erro verdade mito noite dinheiro inversor placas painéis calor chuva hoje agora novo nova melhor resultado segredo sempre promoção desconto instalação projeto cliente casa'.split(' '));
    const CORES = ['#3CC8FF', '#FFD60A', '#FF50AA', '#FF4632', '#4678FF', '#3CE678', '#FF961E', '#FFFFFF'];
    const QUENTES = ['#FFD60A', '#FF4632', '#FF50AA', '#FF961E'];
    const FONTES = ['Luckiest Guy', 'Bangers', 'Anton', 'Montserrat Black'];
    const CONT = '#0E1228';
    const LUGARES = [[0.50, 0.74], [0.32, 0.68], [0.68, 0.80], [0.38, 0.84], [0.64, 0.70], [0.50, 0.80]];
    const GIROS = [-7, 5, -3, 8, -5, 3, -8, 6];
    const clarear = c => '#' + [1, 3, 5].map(j => { const x = parseInt(c.slice(j, j + 2), 16); return Math.round(x + (255 - x) * 0.55).toString(16).padStart(2, '0'); }).join('');
    let sem = 0; for (const ch of String(v.job)) sem = (sem * 31 + ch.charCodeAt(0)) >>> 0;
    const rnd = () => { sem = (sem * 1664525 + 1013904223) >>> 0; return sem / 4294967296; };
    const pick = l => l[Math.floor(rnd() * l.length)];
    const blocos = [];
    let pre = [];
    for (const p of novo) {
      const lw = p.w.replace(/[.,!?;:"']/g, '').toLowerCase();
      if (CURTAS.has(lw) && pre.length < 3) { pre.push(p); continue; }
      blocos.push({ cima: pre.map(x => x.w), forte: p, s: pre.length ? pre[0].s : p.s, e: p.e });
      pre = [];
    }
    if (pre.length) blocos.push({ cima: pre.slice(0, -1).map(x => x.w), forte: pre[pre.length - 1], s: pre[0].s, e: pre[pre.length - 1].e });
    blocos.forEach((bl, i) => { const prox = blocos[i + 1] ? blocos[i + 1].s : bl.e + 0.5; bl.e = Math.min(Math.max(Math.min(prox, bl.e + 0.5), bl.s + 0.3), fala); });
    const peso = bl => { const w = bl.forte.w.replace(/[.,!?;:"']/g, ''); return ehChave.has(bl.forte.i) || FORTES.has(w.toLowerCase()) || /[!?]$/.test(bl.forte.w) ? 3 : (w.length >= 7 ? 2 : 1); };
    // um adesivo (palavra) = várias camadas do .ass: brilho, borda branca, borda escura e preenchimento em 2 tons (degradê)
    const adesivo = (a, b, x, y, sz, fn, c, giro, des, pop, txt, rastro) => {
      const out = [], s = Math.max(4, Math.round(sz / 9)), base = `\\an5\\pos(${Math.round(x)},${Math.round(y)})\\fn${fn}\\fs${Math.round(sz)}\\frz${giro}\\shad0`;
      const p = pop ? `\\fscx${Math.round(pop * 100)}\\fscy${Math.round(pop * 100)}\\t(0,130,\\fscx100\\fscy100)` : '';
      const al = rastro ? '\\alpha&HA6&' : '';
      const L = (cam, extra) => out.push(`Dialogue: ${cam},${t2(a)},${t2(b)},Mix,,0,0,0,,{${base}${p}${extra}${al}}${txt}`);
      if (des === 'caixa') {
        out.push(`Dialogue: 12,${t2(a)},${t2(b)},MixCaixa,,0,0,0,,{${base}${p}\\1c&HFFFFFF&\\3c${ass(c === '#FFFFFF' ? '#FF4632' : c)}\\bord${Math.round(sz * 0.13)}\\shad${s}\\4a&H70&${al}}${txt}`);
        return out;
      }
      if (des !== 'recorte') L(10, `\\bord${Math.round(s * (des === 'contorno_duplo' ? 3.4 : 2.4))}\\blur${Math.round(s * 1.6)}\\3c${ass(c)}\\1a&HFF&\\3a&H55&`);
      if (des === 'contorno_duplo') L(11, `\\bord${s + Math.max(3, Math.round(s / 2)) + s}\\3c&HFFFFFF&\\1a&HFF&`);
      if (des === 'recorte') L(11, `\\bord${s + Math.max(8, Math.round(sz / 6))}\\3c&HFFFFFF&\\1c&HFFFFFF&\\shad${Math.round(s * 1.3)}\\4c&H000000&\\4a&H66&`);
      const sombra = des === 'sombra' ? `\\shad${Math.round(s * 1.4)}\\4c&H000000&\\4a&H60&` : '';
      const borda = des === 'recorte' ? Math.max(3, Math.round(sz / 14)) : s;
      L(12, `\\bord${borda}\\3c${ass(CONT)}${sombra}\\clip(0,0,${W},${Math.round(y)})\\1c${ass(clarear(c))}`);
      L(12, `\\bord${borda}\\3c${ass(CONT)}${sombra}\\clip(0,${Math.round(y)},${W},${H})\\1c${ass(c)}`);
      return out;
    };
    // modo como no PC (escolher_mix): 'inteligente' (desenho e efeitos seguem o peso da palavra) ou 'livre' (sorteado)
    mixModo = rnd() < 0.5 ? 'inteligente' : 'livre';
    let ant = null, antEv = [], antRastro = false, antCaixa = null;
    blocos.forEach((bl, n) => {
      const pz = peso(bl);
      const livre = mixModo === 'livre';
      const ops = livre ? ['degrade', 'sombra', 'contorno_duplo', 'recorte', 'caixa']
        : { 3: ['recorte', 'caixa', 'contorno_duplo'], 2: ['recorte', 'contorno_duplo', 'sombra', 'degrade'], 1: ['degrade', 'sombra', 'recorte'] }[pz];
      const c = livre ? pick(CORES) : (pz === 3 ? pick(QUENTES) : CORES[(n * 3) % CORES.length]);
      const popK = livre ? pick([1.18, 1.35, 1.40]) : { 3: 1.40, 2: 1.35, 1: 1.18 }[pz];
      const giro = GIROS[n % 8] * (livre ? pick([1, 1, 1.7]) : (pz === 3 && rnd() < 0.5 ? 1.7 : 1));
      const des = pick(ops.filter(d => d !== ant).length ? ops.filter(d => d !== ant) : ops);
      const sub = des !== 'caixa' && (livre ? rnd() < 0.25 : pz >= 2 && rnd() < (pz === 3 ? 0.5 : 0.25));
      let rastro = n > 0 && (livre ? rnd() < 0.35 : bl.s - blocos[n - 1].e < 0.25 && !antRastro && rnd() < 0.5);
      const fn = FONTES[n % FONTES.length], txt = bl.forte.w.replace(/[.,!?;:"']/g, '').toUpperCase();
      let sz = { 1: 92, 2: 110, 3: 138 }[pz] * k;
      const maxL = W * (des === 'degrade' || des === 'sombra' ? 0.80 : 0.72);
      if (larg(txt, sz, fn) > maxL) sz = Math.max(60, sz * maxL / larg(txt, sz, fn));
      const w = larg(txt, sz, fn) + (des === 'caixa' ? sz * 0.5 : sz * 0.3);
      // lugar: gira pela lista; se cair no rosto vai para o próximo; nenhum livre = embaixo do rosto (como o PC)
      const altoB = sz * (bl.cima.length ? 2.0 : 1.2);
      let x, y;
      for (let t = 0; t <= LUGARES.length; t++) {
        if (t === LUGARES.length) { x = W / 2; y = Math.min(H * 0.90 - sz / 2, (rosto ? rosto[1] + 30 : H * 0.70) + altoB - sz / 2); break; }
        const [fx, fy] = LUGARES[(n + t) % LUGARES.length];
        x = Math.min(Math.max(fx * W, 39 + w / 2), W - 39 - w / 2); y = Math.min(fy * H, H * 0.90 - sz / 2);
        const topo = y - altoB + sz / 2, base = y + sz / 2;
        if (!rosto || base < rosto[0] - 15 || topo > rosto[1] + 45) break;
      }
      // rastro só se a palavra anterior NÃO encosta na nova (_encostam do PC): em cima dela embola as duas
      const caixa = [x - w / 2, y - sz * 1.4, x + w / 2, y + sz * 0.6], f2 = 30;
      if (rastro && antCaixa && !(antCaixa[2] + f2 < caixa[0] || caixa[2] + f2 < antCaixa[0] || antCaixa[3] + f2 < caixa[1] || caixa[3] + f2 < antCaixa[1])) rastro = false;
      const evs = [];
      if (rastro) antEv.forEach(e1 => evs.push(e1.replace(/^Dialogue: (\d+),[^,]+,[^,]+,/, (m, cam) => `Dialogue: ${Math.max(1, cam - 6)},${t2(bl.s)},${t2(bl.e)},`).replace(/\}/, '\\alpha&HA6&}')));
      const a = bl.s, b = bl.e;
      evs.push(...adesivo(a, Math.min(a + 0.13, b), x, y, sz, fn, c, giro, des, popK, txt));
      evs.push(...adesivo(Math.min(a + 0.13, b), b, x, y, sz, fn, c, giro, des, 0, txt));
      const meus = adesivo(a, b, x, y, sz, fn, c, giro, des, 0, txt);
      if (sub) evs.push(`Dialogue: 12,${t2(a)},${t2(b)},Mix,,0,0,0,,{\\an7\\pos(0,0)\\org(${Math.round(x)},${Math.round(y)})\\frz${giro}\\bord0\\shad0\\1c${ass(c)}\\p1}${rr(x - w * 0.38, y + sz * 0.5, x + w * 0.38, y + sz * 0.5 + 15, 7)}{\\p0}`);
      const cimaTxt = bl.cima.map(t => t.replace(/[.,]/g, '')).join(' ').toUpperCase();
      if (cimaTxt) {
        const fn2 = FONTES[(n + 1) % FONTES.length], sz2 = Math.max(60, sz * 0.55);
        const des2 = des !== 'caixa' && rnd() < 0.35 ? 'caixa' : (des === 'caixa' ? 'recorte' : des);
        const w2 = larg(cimaTxt, sz2, fn2);
        const x2 = Math.min(Math.max(x + (n % 2 ? -1 : 1) * w * 0.12, 39 + w2 / 2), W - 39 - w2 / 2), y2 = y - sz * 0.82;
        const c2 = CORES[(n * 3 + 2) % CORES.length];
        evs.push(...adesivo(a, b, x2, y2, sz2, fn2, c2, giro, des2, popK, cimaTxt));
        meus.push(...adesivo(a, b, x2, y2, sz2, fn2, c2, giro, des2, 0, cimaTxt));
      }
      ev.push(...evs);
      ant = des; antEv = meus; antRastro = rastro; antCaixa = caixa;
    });
  }
  // cartão final (como o dos vídeos de propaganda): marca, oferta, serviços, botão em pílula na cor da marca, @ e link
  if (FIM) {
    const a = fala + 0.15, b = total, fad = '\\fad(250,0)';
    const marca = limpa(v.dados.marca || v.dados.titulo).toUpperCase();
    const fm = Math.min(114, (W - 105) / Math.max(1, marca.length * 0.70));
    ev.push(texto(6, a, b, W / 2, H * 0.27, 5, fm, '#FFFFFF', marca, `\\bord6\\3c${ass(cor)}\\3a&H60&\\blur4\\fscx50\\fscy50\\t(0,220,\\fscx106\\fscy106)\\t(220,320,\\fscx100\\fscy100)`));
    let y = H * 0.355;
    if (ia.oferta) quebra(limpa(ia.oferta), 66, 'Montserrat Black', W - 150).slice(0, 2).forEach(l => { ev.push(texto(6, a + 0.2, b, W / 2, y, 8, 66, '#FFFFFF', l, fad)); y += 80; });
    if (ia.servicos) { ev.push(texto(6, a + 0.3, b, W / 2, y + 10, 8, 42, '#E1E1E1', limpa(ia.servicos), fad)); y += 70; }
    const bt = limpa(ia.cartao || 'Chame no direct'), fbt = Math.min(66, (W - 255) / Math.max(1, bt.length * 0.70)), lbt = larg(bt, fbt, 'Montserrat Black');
    const yb = Math.max(y + 60, H * 0.50);
    const pulsa = [0, 1, 2, 3].map(q => `\\t(${q * 700},${q * 700 + 350},\\fscx106\\fscy106)\\t(${q * 700 + 350},${q * 700 + 700},\\fscx100\\fscy100)`).join('');
    if (SVGC) {
      // painel de vidro escuro atrás de tudo, com friso na cor da marca; botão em pílula com brilho colorido que pulsa junto
      const py0 = H * 0.27 - 120, py1 = yb + 320, pw = W - 120;
      card(60, py0, pw, py1 - py0, a, b, defs('#000', '#000', '#000', 0.55) + R(pw, py1 - py0, 54, 'fill="#0B0E18" fill-opacity=".62" filter="url(#s)"') +
        R(pw, py1 - py0, 54, 'fill="url(#b)" fill-opacity=".45"') + contorno(pw, py1 - py0, 54, 0.2) +
        `<rect x="${Math.round(pw * 0.36)}" y="0" width="${Math.round(pw * 0.28)}" height="7" rx="3.5" fill="${cor}"/>`, 'fica');
      const bw = lbt + 132, bh = 132;
      card((W - bw) / 2, yb - 27, bw, bh, a + 0.4, b, pilula(bw, bh, 66, cor, cor, 0.75), 'pulsa');
    } else {
      ev.push(desenho(5, a + 0.4, b, '#000000', rr((W - lbt) / 2 - 66 + 5, yb - 27 + 9, (W + lbt) / 2 + 66 + 5, yb + 105 + 9, 66), `\\1a&H88&\\blur10${fad}`));
      ev.push(desenho(6, a + 0.4, b, cor, rr((W - lbt) / 2 - 66, yb - 27, (W + lbt) / 2 + 66, yb + 105, 66), fad));
    }
    ev.push(texto(7, a + 0.4, b, W / 2, yb + 39, 5, fbt, corTexto, bt, fad + pulsa));
    if (v.dados.instagram) ev.push(texto(6, a + 0.55, b, W / 2, yb + 190, 5, 54, '#FFFFFF', 'Instagram @' + limpa(v.dados.instagram), fad));
    ev.push(texto(6, a + 0.7, b, W / 2, yb + 265, 5, 42, destaque, 'Link no perfil', fad));
  }
} else {
// abertura: frase grande no meio, entra crescendo
if (abertura) ev.push(`Dialogue: 6,${t2(0)},${t2(Math.min(ABRE, fala))},Abertura,,0,0,0,,{\\an5\\pos(${W / 2},${Math.round(H * 0.4)})\\fscx40\\fscy40\\t(0,160,\\fscx108\\fscy108)\\t(160,260,\\fscx100\\fscy100)\\fad(0,180)}${abertura}`);
const gancho = limpa(ia.gancho || v.dados.titulo).toUpperCase();
if (gancho) ev.push(`Dialogue: 3,${t2(ABRE)},${t2(fala)},Gancho,,0,0,0,,{\\an8\\move(${W / 2},${-fs(60)},${W / 2},${Math.round(H * 0.06)},0,250)}${gancho}`);
// tópicos numerados entrando da esquerda + flash na troca
const yT = Math.round(H * 0.17);
topicos.forEach((tp, i) => {
  const a = Math.max(tp.t, i === 0 ? ABRE : 0), b = topicos[i + 1] ? topicos[i + 1].t : fala;
  if (b - a > 0.8) ev.push(`Dialogue: 2,${t2(a)},${t2(b)},Topico,,0,0,0,,{\\an7\\move(${-W / 2},${yT},${fs(50)},${yT},0,250)}{\\c${ass(destaque)}}${i + 1}{\\c&HFFFFFF&}  ${limpa(tp.texto)}`);
});
trocas.forEach(t => ev.push(`Dialogue: 7,${t2(t)},${t2(t + 0.18)},Barra,,0,0,0,,{\\an7\\pos(0,0)\\bord0\\shad0\\1c&HFFFFFF&\\1a&H40&\\fad(0,160)\\p1}m 0 0 l ${W} 0 ${W} ${H} 0 ${H}{\\p0}`));
// legenda karaokê: o grupo aparece; a palavra falada acende e pula; palavras-chave na cor de destaque e maiores
if (v.op.legendas && novo.length) {
  grupos.forEach((g, gi) => {
    const fimG = Math.min(gi + 1 < grupos.length ? grupos[gi + 1][0].s : g[g.length - 1].e + 0.4, g[g.length - 1].e + 0.6, fala);
    g.forEach((p, j) => {
      const a = Math.max(p.s, 0), b = j + 1 < g.length ? g[j + 1].s : fimG;
      if (b - a < 0.02) return;
      // só as palavras em maiúscula (o código de cor {\c...} tem de ficar minúsculo)
      const txt = g.map((x, q) => {
        const W1 = x.w.toUpperCase(), chave = ehChave.has(x.i);
        if (q === j) return `{\\c${ass(destaque)}\\t(0,90,\\fscx${chave ? 132 : 120}\\fscy${chave ? 132 : 120})\\t(90,180,\\fscx${chave ? 122 : 110}\\fscy${chave ? 122 : 110})}${W1}{\\r}`;
        return chave ? `{\\c${ass(destaque)}}${W1}{\\r}` : W1;
      }).join(' ');
      ev.push(`Dialogue: 1,${t2(a)},${t2(b)},Legenda,,0,0,0,,${j === 0 ? '{\\fscx90\\fscy90\\t(0,120,\\fscx100\\fscy100)}' : ''}${txt}`);
    });
  });
}
}
// "Siga @" no meio do vídeo
if (v.dados.instagram && fala > 12) {
  const a = fala * 0.45, b = Math.min(fala * 0.45 + 3, fala - 1), y = Math.round(H * 0.27);
  if (SVGC) {   // pílula da marca vinda da esquerda (o estilo Siga desenhava uma caixa quadrada)
    const txt = 'Siga @' + limpa(v.dados.instagram), sz = fs(38), w = txt.length * sz * 0.64 + 72, h = sz + 40;
    card(fs(40), y - h / 2, w, h, a, b, pilula(w, h, h / 2, cor), 'esq', 0.25);
    ev.push(`Dialogue: 5,${t2(a)},${t2(b)},Mix,,0,0,0,,{\\an4${mv(fs(40) + 32, y, 'esq')}\\fnMontserrat Black\\fs${sz}\\bord0\\shad0\\1c${ass(corTexto)}\\fad(0,250)}${txt}`);
  } else {
    ev.push(`Dialogue: 2,${t2(a)},${t2(b)},Siga,,0,0,0,,{\\an4\\move(${-W / 2},${y},${fs(50)},${y},0,300)\\fad(0,250)}Siga @${limpa(v.dados.instagram)}`);
  }
}
// barrinha de progresso no topo
const P = 40;
for (let i = 0; i < P; i++) {
  const a = fala * i / P, b = fala * (i + 1) / P, larg = Math.round(W * (i + 1) / P);
  ev.push(`Dialogue: 4,${t2(a)},${t2(b)},Barra,,0,0,0,,{\\p1}m 0 0 l ${larg} 0 ${larg} ${fs(9)} 0 ${fs(9)}{\\p0}`);
}
// cartão final animado (a V4 desenha o dela no bloco acima)
if (FIM && NIVEL < 4) {
  const a = fala + 0.15, b = total;
  const pos = (y, extra = '') => `{\\an5\\pos(${W / 2},${Math.round(H * y)})\\fad(250,0)${extra}}`;
  const pulsa = [0, 1, 2, 3].map(q => `\\t(${q * 700},${q * 700 + 350},\\fscx108\\fscy108)\\t(${q * 700 + 350},${q * 700 + 700},\\fscx100\\fscy100)`).join('');
  ev.push(`Dialogue: 2,${t2(a)},${t2(b)},Marca,,0,0,0,,${pos(0.33, '\\fscx50\\fscy50\\t(0,220,\\fscx106\\fscy106)\\t(220,320,\\fscx100\\fscy100)')}${limpa(v.dados.marca || v.dados.titulo).toUpperCase()}`);
  if (ia.cartao) ev.push(`Dialogue: 2,${t2(a + 0.3)},${t2(b)},Chamada,,0,0,0,,${pos(0.47, pulsa)}${limpa(ia.cartao)}`);
  if (v.dados.instagram) ev.push(`Dialogue: 2,${t2(a + 0.45)},${t2(b)},Contato,,0,0,0,,${pos(0.6)}@${limpa(v.dados.instagram)}`);
  ev.push(`Dialogue: 2,${t2(a + 0.6)},${t2(b)},Link,,0,0,0,,${pos(0.68)}Link no perfil`);
}
const estilo = (nome, tam, prim, borda, fundo, bs, out, sh, alinh, mv, extra = '') =>
  `Style: ${nome},Montserrat Black,${fs(tam)},${prim},${prim},${borda},${fundo},-1,0,0,0,100,100,${extra || 0},0,${bs},${fs(out)},${fs(sh)},${alinh},${fs(50)},${fs(50)},${mv},1`;
const cab = `[Script Info]\nScriptType: v4.00+\nPlayResX: ${W}\nPlayResY: ${H}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n` +
  'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n' +
  estilo('Abertura', 62, ass(corTexto), ass(cor), '&H80000000&', 3, 24, 6, 5, 0, 1) + '\n' +
  estilo('Gancho', 56, ass(corTexto), ass(cor), '&H80000000&', 3, 20, 4, 8, Math.round(H * 0.06), 1) + '\n' +
  estilo('Topico', 40, '&H00FFFFFF&', '&H28101010&', '&H00000000&', 3, 16, 0, 7, Math.round(H * 0.17)) + '\n' +
  estilo('Legenda', 74, '&H00FFFFFF&', '&H00000000&', '&H96000000&', 1, 7, 3, 2, Math.round(H * 0.2)) + '\n' +
  estilo('Siga', 38, ass(corTexto), ass(cor), '&H00000000&', 3, 16, 0, 4, 0) + '\n' +
  estilo('Barra', 10, ass(cor), ass(cor), ass(cor), 1, 0, 0, 7, 0) + '\n' +
  estilo('Marca', 78, '&H00FFFFFF&', '&H00000000&', '&H96000000&', 1, 5, 3, 5, 0, 2) + '\n' +
  estilo('Chamada', 62, ass(corTexto), ass(cor), '&H80000000&', 3, 22, 4, 5, 0) + '\n' +
  estilo('Contato', 50, '&H00FFFFFF&', '&H00000000&', '&H96000000&', 1, 4, 2, 5, 0) + '\n' +
  estilo('Link', 40, ass(destaque), '&H00000000&', '&H96000000&', 1, 4, 2, 5, 0) + '\n' +
  estilo('Mix', 60, '&H00FFFFFF&', '&H000E1228&', '&H00000000&', 1, 0, 0, 5, 0) + '\n' +
  estilo('MixCaixa', 60, '&H00FFFFFF&', '&H000E1228&', '&H00000000&', 3, 10, 0, 5, 0) + '\n\n' +
  '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n';
const textos = cab + ev.join('\n') + '\n';

// V6: cada card é um SVG (lido 1 vez e repetido com loop) que entra com fade e anda junto com o texto dele; o botão do
// cartão final pulsa; tudo por baixo do .ass
if (SVGC) {
  const fc = [], base = 3 + emojis.length;
  let cur = 'vb';
  cards.forEach((c, i) => {
    const A = n2(c.a), B = n2(c.b), p = `max(0,1-(t-${A})/0.25)`;
    const sai = c.saida ? `,fade=t=out:st=${n2(Math.max(c.a, c.b - c.saida))}:d=${n2(c.saida)}:alpha=1` : '';
    const pul = c.anim === 'pulsa' ? `,scale=w='2*trunc(iw*(1+0.06*(1-abs(2*mod(max(0,t-${A})/0.7,1)-1)))/2)':h=-2:eval=frame` : '';
    fc.push(`[${base + i}:v]format=rgba,loop=loop=${Math.ceil(c.b * FPS) + 2}:size=1:start=0,setpts=N/${FPS}/TB,fade=t=in:st=${A}:d=0.22:alpha=1${sai}${pul}[k${i}]`);
    const x = c.anim === 'esq' ? `${c.x}-${DX}*${p}` : c.anim === 'pulsa' ? `${c.x + c.w / 2}-overlay_w/2` : `${c.x}`;
    const y = c.anim === 'sobe' ? `${c.y}+${DY}*${p}` : c.anim === 'pulsa' ? `${c.y + c.h / 2}-overlay_h/2` : `${c.y}`;
    fc.push(`[${cur}][k${i}]overlay=x='${x}':y='${y}':eof_action=pass:enable='between(t,${A},${B})'[vk${i}]`);
    cur = `vk${i}`;
  });
  fc.push(`[${cur}]ass={{in_textos}}:fontsdir=inputs[vass]`);
  f[f.indexOf('__CARDS__')] = fc.join(';');
}

// ── 5) pedido para o Very Good FFmpeg (um trabalho: vídeo, capa) ─────────────────────────────────────────────
const input_files = {
  'in_video.mp4': v.video_url,
  'in_fundo.jpg': ex.quadro,
  'in_trilha.mp3': v.arquivo + 'trilha-' + (TRILHAS.includes(ia.trilha) ? ia.trilha : 'elegante'),
  'in_textos.ass': v.arquivo + 'textos-' + v.job + '.ass',
  'in_fonte.ttf': 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf',
};
if (NIVEL >= 4) {   // fontes da legenda MIX (Google Fonts); a Impact da versão do PC vira Anton
  input_files['in_f1.ttf'] = 'https://fonts.gstatic.com/s/luckiestguy/v25/_gP_1RrxsjcxVyin9l9n_j2RSg.ttf';
  input_files['in_f2.ttf'] = 'https://fonts.gstatic.com/s/bangers/v25/FeVQS0BTqb0h60ACL5k.ttf';
  input_files['in_f3.ttf'] = 'https://fonts.gstatic.com/s/anton/v27/1Ptgg87LROyAm0K0.ttf';
}
emojis.forEach((c, q) => { input_files[`in_e${q}.png`] = `https://fonts.gstatic.com/s/e/notoemoji/latest/${c.emoji}/512.png`; });
const enc = `-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -color_range tv -r ${FPS} -c:a aac -b:a 160k -ar 48000 -movflags +faststart`;
const entradasEmoji = emojis.map((_, q) => `-loop 1 -framerate ${FPS} -t ${total.toFixed(2)} -i inputs/in_e${q}.png `).join('');
cards.forEach((c, i) => { input_files[`in_c${i}.svg`] = v.arquivo + `cards-${v.job}-${i}.svg`; });   // V6: o n8n entrega cada card
const entradasCards = cards.map((_, i) => `-i inputs/in_c${i}.svg `).join('');
const cmd = `-i inputs/in_video.mp4 -loop 1 -i inputs/in_fundo.jpg -i inputs/in_trilha.mp3 ${entradasEmoji}${entradasCards}-filter_complex "${f.join(';').replace(/\{\{in_textos\}\}/g, 'inputs/in_textos.ass')}" ` +
  `-map "[vid]" -map "[aud]" ${enc} -t ${total.toFixed(2)} outputs/editado-${v.job}.mp4 -map "[capa]" -frames:v 1 -q:v 3 -update 1 outputs/capa-${v.job}.jpg`;
return [{ json: {
  corpo: JSON.stringify({ input_files, output_files: [`editado-${v.job}.mp4`, `capa-${v.job}.jpg`], machine: 'cpu', timeout_seconds: 300, ffmpeg_commands: [cmd] }),
  textos: Buffer.from(textos, 'utf8').toString('base64'),
  cards: Buffer.from(JSON.stringify(cards.map(c => c.svg)), 'utf8').toString('base64'), qtd_cards: cards.length,
  total: Math.round(total * 100) / 100, original: Math.round(dur * 100) / 100, cortes: n, tirou: tirar.map(t => t.w),
  fala: novo.map(p => p.w).join(' '), ritmo: SP, planos: cenas.length, palavras_chave: chaves.map(c => c.p.w), emojis: emojis.length, legenda_mix: mixModo,
} }];
