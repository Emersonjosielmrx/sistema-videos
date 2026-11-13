// Melhora o texto da cena com IA grátis (depois da resposta à página). A foto segue como arquivo para o nó HTTP subir ao Space.
__TEXTO__
const c = $('🧩 Confere o pedido').first();
let prompt = c.json.prompt;
let usado = '';
if (c.json.melhorar && prompt) {
  try {
    usado = await perguntaIA(this.helpers, [
      { role: 'system', content: 'You write prompts for a text-to-video model (LTX-Video). Translate to English and ' +
        'describe ONE continuous shot in max 50 words: subject, action/motion, camera movement, lighting, style. ' +
        'No text, captions or logos. Answer only the prompt.' },
      { role: 'user', content: prompt }]);
    usado = usado.replace(/^["']|["']$/g, '').slice(0, 600);
    if (usado.length > 10) prompt = usado; else usado = '';
  } catch (e) { usado = ''; }
}
if (!prompt) prompt = 'smooth cinematic camera movement, subtle natural motion, high quality';
const item = { json: { ...c.json, prompt, prompt_usado: usado } };
if (c.binary) item.binary = c.binary;
return [item];
