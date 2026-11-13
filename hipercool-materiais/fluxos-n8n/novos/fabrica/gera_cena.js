// Gera a imagem de UMA cena (FLUX do Hugging Face; reserva Pollinations).
__IMAGEM__
const it = $input.first().json;
try {
  const r = await geraImagem(this.helpers, it.prompt, it.formato, it.semente);
  return [{ json: { ...it, ok: true, motor: r.motor, aviso: r.aviso || '', ext: r.ext, tipo: r.tipo, b64: r.img.toString('base64') } }];
} catch (e) {
  return [{ json: { ...it, ok: false, erro: String(e.message || e).slice(0, 200) } }];
}
