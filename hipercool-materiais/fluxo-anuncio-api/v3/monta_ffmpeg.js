// Monta UM comando ffmpeg para o Very Good FFmpeg (ffmpeg na nuvem, sem marca d'água): cada foto vira um clipe com zoom ou
// panorâmica, as cenas se ligam com transição (xfade), a voz de cada cena (já gerada e medida) entra na hora certa,
// a trilha fica baixinha embaixo, e os textos (manchete, preço, legenda e cartão final) vêm de um arquivo .ass.
// A versão só com música usa o mesmo comando sem a voz e sem a legenda, no mesmo pedido (2 saídas).
const v = $('🧩 Confere o pedido').first().json;
const ed = $('🧩 Junta tudo').first().json;
const vozes = $('🧩 Mede as vozes').first().json;      // { cenas: [{ n, url, dur }] }
const FORMATOS = { vertical: [1080, 1920], quadrado: [1080, 1080], deitado: [1920, 1080] };
// cobra por GB processado (entradas + saídas): 720p deixa o vídeo leve e rende mais anúncios com os 2 GB grátis
const ESCALA = 2 / 3;
const [W0, H0] = FORMATOS[v.op.formato] || FORMATOS.vertical;
const W = Math.round(W0 * ESCALA / 2) * 2, H = Math.round(H0 * ESCALA / 2) * 2;
// letras 35% maiores que a conta direta: em 720p ficavam miúdas no celular
const vertical = H > W, k = Math.min(W, H) / 1080 * 1.35, FPS = 25;
const TRILHAS = {
  animado: 'https://files.catbox.moe/qpmdb1.mp3', calmo: 'https://files.catbox.moe/xoym41.mp3', chill: 'https://files.catbox.moe/2rqu0z.mp3',
  elegante: 'https://files.catbox.moe/yb6h1l.mp3', emocional: 'https://files.catbox.moe/tomvef.mp3', latino: 'https://files.catbox.moe/kic00y.mp3',
  tropical: 'https://files.catbox.moe/x14vcg.mp3', urgente: 'https://files.catbox.moe/2gttp6.mp3',
};
const TRANS = ['fade', 'fadeblack', 'fadewhite', 'dissolve', 'slideleft', 'slideright', 'wipeleft', 'wiperight', 'smoothleft', 'smoothright', 'circleopen', 'radial', 'zoomin', 'hblur', 'pixelize'];
const T = 0.5, DF = 3;                                  // transição e cartão final (s)
const clara = c => { const n = parseInt(String(c).slice(1), 16); return ((n >> 16) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000 > 150; };
const cor = /^#[0-9A-Fa-f]{6}$/.test(ed.cor || '') ? ed.cor : '#F59E0B';
const ass = c => '&H00' + c.slice(5, 7) + c.slice(3, 5) + c.slice(1, 3) + '&';   // #RRGGBB -> &H00BBGGRR&
const corTexto = clara(cor) ? '#111111' : '#FFFFFF';
const limpa = s => String(s || '').replace(/[\u{1F000}-\u{1FAFF}☀-➿️‍]/gu, '').replace(/[{}\\]/g, '').replace(/\n/g, ' ').trim();
const wsrv = (u, extra) => 'https://wsrv.nl/?url=' + encodeURIComponent(u) + '&' + extra;
const t2 = x => { x = Math.max(0, x); return `${Math.floor(x / 3600)}:${String(Math.floor(x % 3600 / 60)).padStart(2, '0')}:${(x % 60).toFixed(2).padStart(5, '0')}`; };

// a voz do Google é calma: acelera 25% (atempo, sem mudar o tom) para o anúncio caber no tempo pedido
const VEL = 1.25;
const porN = Object.fromEntries((vozes.cenas || []).map(c => [c.n, { ...c, dur: c.dur / VEL }]));
const segs = ed.segmentos.filter(s => porN[s.n] && porN[s.n].dur > 0.3);
if (segs.length < 2) throw new Error('A voz falhou em quase todas as cenas. Tente de novo em instantes.');
const durs = segs.map(s => Math.max(2.2, porN[s.n].dur + 0.45));
const final = !!v.op.cartao_final;
const lens = durs.map((d, i) => d + (i < segs.length - 1 || final ? T : 0));
if (final) lens.push(DF);
const inicios = [0];
for (let i = 1; i < lens.length; i++) inicios.push(inicios[i - 1] + lens[i - 1] - T);
const total = inicios[lens.length - 1] + lens[lens.length - 1];

// ── entradas: fotos já no tamanho do vídeo (o wsrv.nl recorta), vozes, trilha e o .ass ──
const input = {}, args = [];
segs.forEach((s, i) => {
  const mov = s.movimento || 'zoom_in';
  const pan = /^pan_/.test(mov), horiz = mov === 'pan_esq' || mov === 'pan_dir';
  // pan: a foto vem 25% maior no sentido do passeio; zoom: vem 2x maior para o zoom não serrilhar
  const fw = pan && horiz ? Math.round(W * 1.25) : pan ? W : W * 2, fh = pan && !horiz ? Math.round(H * 1.25) : pan ? H : H * 2;
  const f = s.foco || { x: 0.5, y: 0.5 };
  const a = f.x < 0.35 ? (f.y < 0.35 ? 'top-left' : f.y > 0.65 ? 'bottom-left' : 'left') : f.x > 0.65 ? (f.y < 0.35 ? 'top-right' : f.y > 0.65 ? 'bottom-right' : 'right') : (f.y < 0.35 ? 'top' : f.y > 0.65 ? 'bottom' : 'center');
  input['in_f' + i] = wsrv(v.fotos[s.foto] || v.fotos[0], `w=${fw}&h=${fh}&fit=cover&a=${a}&output=jpg&q=88&n=.jpg`);
});
if (final) {
  const f0 = v.fotos[ed.segmentos[0].foto] || v.fotos[0];
  input.in_fim = wsrv(f0, `w=${W}&h=${H}&fit=cover&blur=14&mod=0.5&output=jpg&q=80&n=.jpg`);
}
segs.forEach((s, i) => { input['in_v' + i] = porN[s.n].url; });
// a trilha vem pelo endereço do próprio n8n (o catbox derruba downloads de servidores na nuvem)
input.in_trilha = v.arquivo + 'trilha-' + (TRILHAS[ed.clima] ? ed.clima : 'elegante');
input.in_textos = v.arquivo + 'textos-' + v.job + '.ass';
input.in_textos_m = v.arquivo + 'textos-' + v.job + '-m.ass';

// ── filtros ──
const f = [];
const nIn = {};
let idx = 0;
Object.keys(input).forEach(k2 => { nIn[k2] = idx++; });
const fr = d => Math.max(2, Math.round(d * FPS));
segs.forEach((s, i) => {
  const F = fr(lens[i]), p = `(1-cos(PI*on/${F - 1}))/2`, src = `[${nIn['in_f' + i]}:v]`;
  const mov = s.movimento || 'zoom_in';
  if (mov === 'pan_esq' || mov === 'pan_dir') {
    const x = mov === 'pan_dir' ? `(iw-ow)*${p.replace(/on/g, 'n')}` : `(iw-ow)*(1-${p.replace(/on/g, 'n')})`;
    f.push(`${src}loop=loop=${F - 1}:size=1:start=0,setpts=N/${FPS}/TB,crop=${W}:${H}:x='${x}':y=0,setsar=1,format=yuv420p[c${i}]`);
  } else if (mov === 'pan_cima' || mov === 'pan_baixo') {
    const y = mov === 'pan_baixo' ? `(ih-oh)*${p.replace(/on/g, 'n')}` : `(ih-oh)*(1-${p.replace(/on/g, 'n')})`;
    f.push(`${src}loop=loop=${F - 1}:size=1:start=0,setpts=N/${FPS}/TB,crop=${W}:${H}:x=0:y='${y}',setsar=1,format=yuv420p[c${i}]`);
  } else {
    const fx = (s.foco && s.foco.x) || 0.5, fy = (s.foco && s.foco.y) || 0.5;
    const z = mov === 'zoom_out' ? `1.16-0.16*${p}` : mov === 'parado' ? `1+0.03*${p}` : `1+0.16*${p}`;
    f.push(`${src}zoompan=z='${z}':x='(iw-iw/zoom)*${fx.toFixed(2)}':y='(ih-ih/zoom)*${fy.toFixed(2)}':d=${F}:s=${W}x${H}:fps=${FPS},setsar=1,format=yuv420p[c${i}]`);
  }
});
if (final) f.push(`[${nIn.in_fim}:v]loop=loop=${fr(DF) - 1}:size=1:start=0,setpts=N/${FPS}/TB,scale=${W}:${H},setsar=1,format=yuv420p[c${segs.length}]`);
const nClips = segs.length + (final ? 1 : 0);
let ant = 'c0';
for (let i = 1; i < nClips; i++) {
  const tr = i === segs.length ? 'fadeblack' : TRANS.includes(segs[i].transicao) ? segs[i].transicao : 'fade';
  f.push(`[${ant}][c${i}]xfade=transition=${tr}:duration=${T}:offset=${(inicios[i]).toFixed(3)}[x${i}]`);
  ant = 'x' + i;
}
f.push(`[${ant}]split=2[base1][base2]`);
f.push(`[base1]ass={{in_textos}},split=2[vid][vidc]`);
f.push(`[base2]ass={{in_textos_m}}[vidm]`);
// vozes: cada uma atrasada para o começo da sua cena
segs.forEach((s, i) => { const ms = Math.round((inicios[i] + 0.25) * 1000); f.push(`[${nIn['in_v' + i]}:a]aresample=44100,atempo=${VEL},adelay=${ms}|${ms}[a${i}]`); });
f.push(`${segs.map((s, i) => `[a${i}]`).join('')}amix=inputs=${segs.length}:normalize=0,apad[voz]`);
f.push(`[${nIn.in_trilha}:a]aresample=44100,atrim=0:${total.toFixed(2)},afade=t=out:st=${(total - 1.5).toFixed(2)}:d=1.5,asplit=2[tr1][tr2]`);
f.push(`[voz]asplit=2[voz1][voz2]`);
f.push(`[tr1][voz1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]`);
f.push(`[duck]volume=0.35[trb]`);
f.push(`[trb][voz2]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[aud]`);
f.push(`[tr2]volume=0.9[audm]`);

const entradas = Object.keys(input).filter(k2 => !/^in_textos/.test(k2)).map(k2 => (/^in_f|^in_fim/.test(k2) ? `-i {{${k2}}}` : `-i {{${k2}}}`)).join(' ');
const enc = `-c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -r ${FPS} -c:a aac -b:a 128k -movflags +faststart -t ${total.toFixed(2)}`;
let cmd = `${entradas} -filter_complex "${f.join(';')}" -map "[vid]" -map "[aud]" ${enc} {{out_video}}`;
const saidas = { out_video: `anuncio-${v.job}.mp4`, out_capa: `anuncio-${v.job}.jpg` };
if (v.op.versao_musica) { cmd += ` -map "[vidm]" -map "[audm]" ${enc} {{out_musica}}`; saidas.out_musica = `anuncio-${v.job}-musica.mp4`; }
f.push(`[vidc]trim=start=1.2,setpts=PTS-STARTPTS[capa]`);
cmd = cmd.replace(`-filter_complex "${f.slice(0, -1).join(';')}"`, `-filter_complex "${f.join(';')}"`);
cmd += ` -map "[capa]" -frames:v 1 -q:v 3 -update 1 {{out_capa}}`;

// ── textos (.ass): manchete, selo de preço, legenda e cartão final; a versão só música não tem legenda ──
function legenda(semFala) {
  const fs = n => Math.round(n * k);
  const cab = `[Script Info]\nScriptType: v4.00+\nPlayResX: ${W}\nPlayResY: ${H}\nWrapStyle: 0\n\n[V4+ Styles]\n` +
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n' +
    `Style: Manchete,DejaVu Sans,${fs(vertical ? 58 : 50)},${ass(corTexto)},${ass(corTexto)},${ass(cor)},${ass(cor)},-1,0,0,0,100,100,0,0,3,${fs(16)},0,8,40,40,${Math.round(H * 0.07)},1\n` +
    `Style: Preco,DejaVu Sans,${fs(vertical ? 80 : 64)},${ass(corTexto)},${ass(corTexto)},${ass(cor)},${ass(cor)},-1,0,0,0,100,100,0,0,3,${fs(18)},0,5,40,40,0,1\n` +
    `Style: Legenda,DejaVu Sans,${fs(vertical ? 76 : 56)},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H64000000&,-1,0,0,0,100,100,0,0,1,${fs(5)},1,2,${fs(60)},${fs(60)},${Math.round(H * (vertical ? 0.16 : 0.08))},1\n` +
    `Style: Marca,DejaVu Sans,${fs(vertical ? 66 : 54)},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H00000000&,-1,0,0,0,100,100,0,0,1,${fs(4)},1,5,40,40,0,1\n` +
    `Style: Contato,DejaVu Sans,${fs(vertical ? 44 : 36)},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H00000000&,-1,0,0,0,100,100,0,0,1,${fs(3)},1,5,40,40,0,1\n\n` +
    '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n';
  const ev = [];
  const pos = (x, y) => `{\\an5\\pos(${Math.round(x)},${Math.round(y)})\\fad(250,0)}`;
  segs.forEach((s, i) => {
    const a = inicios[i] + 0.15, b = inicios[i] + durs[i];
    if (s.texto_tela) ev.push(`Dialogue: 2,${t2(a)},${t2(b)},Manchete,,0,0,0,,{\\fad(250,0)}${limpa(s.texto_tela)}`);
    if (s.selo_preco && v.dados.preco) ev.push(`Dialogue: 2,${t2(a + 0.3)},${t2(b)},Preco,,0,0,0,,${pos(W / 2, H * (vertical ? 0.55 : 0.5))}${limpa(v.dados.preco)}`);
    if (!semFala && v.op.legendas) {
      // a fala é dividida em pedaços de até 4 palavras, no tempo proporcional ao tamanho de cada pedaço
      const pal = limpa(s.texto).split(/\s+/).filter(Boolean), grupos = [];
      for (let j = 0; j < pal.length; j += 4) grupos.push(pal.slice(j, j + 4).join(' '));
      const letras = grupos.reduce((t, g) => t + g.length, 0) || 1;
      let t = inicios[i] + 0.25;
      const fala = porN[s.n].dur;
      grupos.forEach(g => { const d = fala * g.length / letras; ev.push(`Dialogue: 1,${t2(t)},${t2(t + d)},Legenda,,0,0,0,,${g}`); t += d; });
    }
  });
  if (final) {
    const a = inicios[lens.length - 1] + 0.2, b = total;
    ev.push(`Dialogue: 2,${t2(a)},${t2(b)},Marca,,0,0,0,,${pos(W / 2, H * 0.28)}${limpa(v.dados.marca || v.dados.titulo)}`);
    if (ed.cta) ev.push(`Dialogue: 2,${t2(a + 0.2)},${t2(b)},Preco,,0,0,0,,${pos(W / 2, H * 0.42)}{\\fs${fs(vertical ? 58 : 48)}}${limpa(ed.cta)}`);
    if (v.dados.preco) ev.push(`Dialogue: 2,${t2(a + 0.3)},${t2(b)},Marca,,0,0,0,,${pos(W / 2, H * 0.55)}${limpa(v.dados.preco)}`);
    (ed.contatos || []).slice(0, 3).forEach((c, j) => ev.push(`Dialogue: 2,${t2(a + 0.4)},${t2(b)},Contato,,0,0,0,,${pos(W / 2, H * (0.66 + j * 0.065))}${limpa(c)}`));
  }
  return cab + ev.join('\n') + '\n';
}

// formato do Very Good FFmpeg: cada entrada vira um arquivo com nome em inputs/ e cada saída um nome em outputs/
function pedido() {
  const ext = k2 => /^in_textos/.test(k2) ? '.ass' : /^in_v|^in_trilha/.test(k2) ? '.mp3' : '.jpg';
  const nome = {}, input_files = {};
  Object.keys(input).forEach(k2 => { nome[k2] = 'inputs/' + k2 + ext(k2); input_files[k2 + ext(k2)] = input[k2]; });
  Object.entries(saidas).forEach(([k2, n]) => { nome[k2] = 'outputs/' + n; });
  return {
    input_files, output_files: Object.values(saidas), machine: 'cpu', timeout_seconds: 300,   // máximo do saldo grátis
    ffmpeg_commands: [cmd.replace(/\{\{(\w+)\}\}/g, (m, k2) => nome[k2])],
  };
}

return [{ json: {
  corpo: JSON.stringify(pedido()),
  textos: Buffer.from(legenda(false), 'utf8').toString('base64'), textos_musica: Buffer.from(legenda(true), 'utf8').toString('base64'),
  total: Math.round(total * 100) / 100,
} }];
