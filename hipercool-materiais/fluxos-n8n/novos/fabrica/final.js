// Monta o status final: links, textos para postar e o "filme" para o montador do navegador.
const v = $('🧩 Confere o pedido').first().json;
const rot = $('🔎 Revisa os fatos').first().json;
const voz = $('🎙️ Narra o roteiro').first().json;
let video = null;
let aviso = voz.aviso || '';
if (v.modo === 'nuvem') {
  const lv = $('🧩 Lê o vídeo').isExecuted ? $('🧩 Lê o vídeo').first().json : { ok: false, erro: 'montador não rodou' };
  const sm = $('🧩 Monta o pedido da montagem').isExecuted ? $('🧩 Monta o pedido da montagem').first().json
    : { ok: false, erro: 'não chegou a montar o pedido' };
  if (lv.ok) video = v.arquivo + 'video.mp4';
  else aviso = 'O montador grátis da nuvem falhou (' + String((sm.ok ? lv.erro : sm.erro) || '').slice(0, 160) +
    '). Monte aqui no navegador.';
}
const imgs = voz.imgs;
const motores = [...new Set(imgs.filter(i => i.ok).map(i => i.motor))];
const [largura, altura] = v.formato === '16:9' ? [1280, 720] : [720, 1280];
return [{ json: { job: v.job, etapa: 'pronto', pct: 100, tema: v.tema, modo: v.modo, formato: v.formato,
  titulo: rot.titulo, descricao: rot.descricao, hashtags: rot.hashtags, video, aviso, fonte: rot.fonte || '',
  revisado: !!rot.revisado,
  voz: v.arquivo + 'voz.mp3', segundos: voz.segundos, motor_voz: voz.motor, motores_imagem: motores,
  imagens: imgs.filter(i => i.ok).sort((a, b) => a.n - b.n).map(i => v.arquivo + 'img' + i.n + '.' + i.ext),
  filme: { largura, altura, voz: v.arquivo + 'voz.mp3', total: Math.round((voz.segundos + 0.6) * 100) / 100,
    gancho: rot.titulo, cenas: voz.cenas.map(c => ({ img: c.img, ini: c.ini, fim: c.fim, fala: c.fala })) } } }];
