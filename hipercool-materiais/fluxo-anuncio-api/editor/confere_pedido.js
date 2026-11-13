// Confere o pedido: o vídeo já enviado (código), os dados do negócio e as escolhas. Cria o código do trabalho (job).
let b = $('🔔 Pedido de edição (POST)').first().json.body;
if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = {}; } }
b = b || {};
const crypto = require('crypto');
const limpa = (v, max) => String(v ?? '').replace(/[\u0000-\u0008\u000b-\u001f\u007f<>{}\\]/g, ' ').replace(/[ \t]+/g, ' ').trim().slice(0, max);
const TIPOS = { imovel: 'imóvel', produto: 'produto', comida: 'restaurante / comida', veiculo: 'carro ou moto', servico: 'serviço', evento: 'evento', outro: 'outro' };
const TRILHAS = ['auto', 'nenhuma', 'elegante', 'animado', 'urgente', 'emocional', 'calmo', 'tropical', 'latino', 'chill'];
const video = /^[a-f0-9]{12}$/.test(String(b.video || '')) ? String(b.video) : (b.video === 'exemplo' ? 'exemplo' : '');
const tipo = TIPOS[b.tipo] ? b.tipo : 'produto';
const dados = {
  tipo, tipo_txt: TIPOS[tipo], marca: limpa(b.marca, 50), titulo: limpa(b.titulo, 90), detalhes: limpa(b.detalhes, 1000),
  instagram: limpa(b.instagram, 40).replace(/^@/, '').replace(/[^a-zA-Z0-9._]/g, ''),
};
const erros = [];
if (!video) erros.push('Envie o vídeo (ou use o exemplo).');
if (dados.titulo.length < 3) erros.push('Diga o que está sendo mostrado no vídeo.');
const op = {
  cor: /^#[0-9a-fA-F]{6}$/.test(b.cor || '') ? String(b.cor).toUpperCase() : '',
  trilha: TRILHAS.includes(b.trilha) ? b.trilha : 'auto',
  legendas: b.legendas !== false, cartao_final: b.cartao_final !== false,
  cortar_pausas: b.cortar_pausas !== false, cortar_vicios: b.cortar_vicios !== false,
};
const job = 'e' + Date.now().toString(36) + crypto.randomBytes(2).toString('hex');
const base = String($('🔔 Pedido de edição (POST)').first().json.webhookUrl || '').split('/webhook/')[0];
return [{ json: {
  valido: erros.length === 0, erros, job, video_id: video, dados, op, criado_em: Date.now(),
  exemplo: video === 'exemplo' ? `${base}/webhook/editor-reel-arquivo?id=exemplo.mp4` : '',   // passa pelo n8n (o catbox derruba downloads da nuvem)
  link: `${base}/webhook/editor-reel-ver?job=${job}`, arquivo: `${base}/webhook/editor-reel-arquivo?id=`,
  chave_limite: '<SEGREDO_REMOVIDO>' + new Date().toISOString().slice(0, 13),
} }];
