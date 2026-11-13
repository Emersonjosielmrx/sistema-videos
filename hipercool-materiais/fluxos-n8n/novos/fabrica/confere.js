// Confere o pedido e prepara o trabalho (job). Formato: nuvem = 16:9 pronto; navegador = 9:16 montado na página.
const ent = $input.first().json;
const b = ent.body || {};
const h = ent.headers || {};
const base = (h['x-forwarded-proto'] || 'https') + '://' + (h['x-forwarded-host'] || h.host);
const tema = String(b.tema || '').replace(/\s+/g, ' ').trim().slice(0, 300);
if (tema.length < 3) return [{ json: { ok: false, erro: 'Escreva o tema do vídeo (pelo menos 3 letras).' } }];
const modo = b.modo === 'nuvem' ? 'nuvem' : 'navegador';
const duracao = [30, 45, 60].includes(Number(b.duracao)) ? Number(b.duracao) : 45;
const voz = ['thalita', 'andrew', 'brian', 'emma', 'google'].includes(b.voz) ? b.voz : 'thalita';
const velocidade = Math.max(-20, Math.min(30, Number(b.velocidade ?? 10) || 0));
const TIPOS = {
  curiosidades: 'vídeo de curiosidades: fatos surpreendentes e verdadeiros, um por cena',
  historia: 'história narrada com começo, conflito e desfecho surpreendente',
  dicas: 'dicas práticas ou passo a passo, uma dica por cena',
  noticia: 'explicação simples de um assunto/notícia, sem inventar fatos',
  produto: 'apresentação de produto ou serviço: problema, solução, benefícios e chamada para ação' };
const tipo = TIPOS[b.tipo] ? b.tipo : 'curiosidades';
const ESTILOS = {
  foto: 'photorealistic photo, natural light, high detail', cinema: 'cinematic film still, dramatic lighting, depth of field',
  ilustracao: 'digital illustration, clean shapes, vibrant colors', anime: 'anime style illustration, detailed, vibrant colors',
  '3d': '3D animated movie style, soft lighting, cute' };
const estilo = ESTILOS[b.estilo] ? b.estilo : 'foto';
const job = (Date.now().toString(36) + Math.random().toString(36).slice(2, 6)).toLowerCase();
return [{ json: { ok: true, job, base, tema, modo, formato: modo === 'nuvem' ? '16:9' : '9:16', duracao, voz, velocidade,
  tipo, tipo_txt: TIPOS[tipo], estilo, estilo_img: ESTILOS[estilo],
  link: base + '/webhook/gratis-video-ver?id=' + job, arquivo: base + '/webhook/gratis-video-arquivo?id=' + job + '-',
  chave_limite: '<SEGREDO_REMOVIDO>' + new Date().toISOString().slice(0, 13) } }];
