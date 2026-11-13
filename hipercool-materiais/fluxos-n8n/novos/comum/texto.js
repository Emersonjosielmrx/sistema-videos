// ── Texto por IA grátis e sem chave (Pollinations, modelo openai-fast) ──
// Limite sem chave: 1 resposta a cada 30 s por IP. Quem chama em sequência precisa esperar (nó ⏳ de 31 s).
// Sem chave o "response_format" dá 400: o JSON é pedido no texto e lido com lerJson (tolera ```json e texto em volta).
// O modelo grátis "pensa" antes de responder: sem reasoning_effort low ele estoura o limite e devolve 400
// (output_token_limit_exceeded); "minimal" não existe e "medium" também estoura.
async function perguntaIA(helpers, mensagens, emJson = false, tentativas = 1) {
  let ultimo = '';
  for (let t = 0; t < tentativas; t++) {
    try {
      const r = await helpers.httpRequest({ method: 'POST', url: 'https://text.pollinations.ai/openai', json: true, timeout: 50000,
        // seed aleatória: sem ela o Pollinations devolve do cache a MESMA resposta para o mesmo pedido
        body: { model: 'openai', messages: mensagens, reasoning_effort: 'low', max_tokens: 6000, seed: Math.floor(Math.random() * 1e9) } });
      const txt = r && r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content;
      if (txt) return emJson ? lerJson(txt) : String(txt).trim();
      ultimo = 'resposta vazia';
    } catch (e) {
      ultimo = String((e.response && e.response.body && JSON.stringify(e.response.body)) || e.message || e).slice(0, 200);
    }
  }
  throw new Error('IA grátis (Pollinations) não respondeu: ' + ultimo);
}

function lerJson(txt) {
  const s = String(txt).replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '').trim();
  try { return JSON.parse(s); } catch (e) { /* tenta achar o bloco */ }
  const i = s.indexOf('{'), j = s.lastIndexOf('}');
  if (i >= 0 && j > i) return JSON.parse(s.slice(i, j + 1));
  throw new Error('a IA não devolveu JSON');
}
