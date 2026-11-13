// O PC pergunta se tem trabalho. Confere o token e marca o PC como "online" (para a página mostrar).
const TOKEN = __TOKEN__;
const ent = $input.first().json;
const h = ent.headers || {};
const q = ent.query || {};
const ok = String(h['x-ponte-token'] || q.token || '') === TOKEN;
const maquina = String(q.maquina || 'pc').replace(/[^a-z0-9-]/gi, '').slice(0, 30) || 'pc';
return [{ json: { ok, maquina, visto: JSON.stringify({ maquina, quando: new Date().toISOString(), versao: String(q.versao || '') }) } }];
