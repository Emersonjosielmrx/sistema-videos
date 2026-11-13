// Monta o pedido para a IA com visão: cada foto vai como miniatura de 512 px (feita pelo wsrv.nl), com o tamanho e a orientação.
const v = $('🧩 Confere o pedido').first().json;
const medidas = $('🌐 Mede a foto (wsrv.nl)').all();
const fotos = [];
for (let i = 0; i < v.fotos.length; i++) {
  const m = (medidas[i] && medidas[i].json) || {};
  const w = Number(m.width) || 0, h = Number(m.height) || 0;
  let b64 = '';
  try { b64 = (await this.helpers.getBinaryDataBuffer(i, 'data')).toString('base64'); } catch (e) {}
  fotos.push({ i, id: v.fotos[i], largura: w, altura: h, orientacao: !w || !h ? 'quadrada' : h > w * 1.1 ? 'vertical' : w > h * 1.1 ? 'deitada' : 'quadrada', b64 });
}
if (!fotos.some(f => f.b64)) throw new Error('Não consegui abrir as fotos (o wsrv.nl não respondeu ou o endereço da foto não abre).');
const conteudo = [{ type: 'text', text: `Você vai ver ${fotos.length} fotos de um anúncio de ${v.dados.tipo_txt}: "${v.dados.titulo}". Analise CADA foto, na ordem (foto 0, 1, 2...).
Para cada foto devolva:
- i: o número da foto
- descricao: o que aparece, em 1 frase objetiva
- ambiente: ex. fachada, sala, cozinha, quarto, banheiro, varanda, área comum, produto inteiro, detalhe do produto, pessoa usando, prato, bebida, salão, carro por fora, interior do carro
- destaque: o detalhe mais atraente para vender o que aparece
- foco: {x, y} = o ponto de interesse principal (0 a 1; x da esquerda para a direita, y de cima para baixo)
- qualidade: 1 a 5 (nitidez, luz, enquadramento)
- problemas: escura, tremida, torta, cortada, com placa/documento/rosto de terceiro, marca d'água, ou "nenhum"
- uso: abertura, meio, final ou descartar
Não invente o que não aparece.
RETORNE SOMENTE JSON: {"fotos":[{"i":0,"descricao":"","ambiente":"","destaque":"","foco":{"x":0.5,"y":0.5},"qualidade":4,"problemas":"nenhum","uso":"meio"}]}` }];
for (const f of fotos) {
  conteudo.push({ type: 'text', text: `FOTO ${f.i} (${f.orientacao}${f.largura ? `, ${f.largura}x${f.altura}` : ''})` + (f.b64 ? '' : ' — não abriu, descreva como "foto indisponível"') });
  if (f.b64) conteudo.push({ type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + f.b64 } });
}
return [{ json: { fotos: fotos.map(({ b64, ...f }) => f),
  corpo: JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 3500, temperature: 0.2, messages: [{ role: 'user', content: conteudo }] }) } }];
