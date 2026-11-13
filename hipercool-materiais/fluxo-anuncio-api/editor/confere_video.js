// Confere o vídeo que a página mandou e sobe direto para o armazenamento temporário do Very Good FFmpeg (1 hora):
// é de lá que o ffmpeg na nuvem lê o vídeo para extrair o áudio e para editar.
const it = $input.first();
const chave = Object.keys(it.binary || {})[0];
if (!chave) return [{ json: { ok: false, erro: 'Nenhum vídeo chegou.' } }];
const arq = it.binary[chave];
const mime = String(arq.mimeType || '').toLowerCase();
if (!/^video\/(mp4|quicktime|webm|x-m4v|3gpp)/.test(mime) && !/\.(mp4|mov|m4v|webm|3gp)$/i.test(arq.fileName || ''))
  return [{ json: { ok: false, erro: 'Formato não aceito. Envie MP4, MOV ou WEBM (o vídeo do celular serve).' } }];
const buf = await this.helpers.getBinaryDataBuffer(0, chave);
if (buf.length > 120e6) return [{ json: { ok: false, erro: 'Vídeo maior que 120 MB. Grave mais curto (até 1 minuto e meio).' } }];
return [{ json: { ok: true, tamanho: buf.length, nome: arq.fileName || 'video.mp4', mime: mime || 'video/mp4' }, binary: { video: arq } }];
