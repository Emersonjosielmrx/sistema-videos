// login.js — diz se a conta está logada no 1min e o saldo da tela.
// Sinal PRINCIPAL: o token do usuário no indexedDB (persist:root > authentication > currentUser.token). É positivo e
// não depende de a página ter terminado de renderizar (o texto "Log In" aparece durante a hidratação e dava falso
// negativo em Chrome frio). Fallback: o texto da página. Mantém as chaves logado/time/creditos (usadas por visita_diaria).
(async () => {
  let token = false, email = '';
  try {
    const db = await new Promise((ok, err) => { const r = indexedDB.open('ai'); r.onsuccess = () => ok(r.result); r.onerror = () => err(r.error); });
    const raiz = await new Promise((ok) => {
      const r = db.transaction('keyvaluepairs', 'readonly').objectStore('keyvaluepairs').get('persist:root');
      r.onsuccess = () => ok(r.result); r.onerror = () => ok(null);
    });
    if (raiz) { const u = JSON.parse(JSON.parse(raiz).authentication).currentUser; token = !!(u && u.token); email = (u && u.email) || ''; }
  } catch (e) { /* about:blank ou IDB negado: cai no texto */ }
  const txt = document.body ? document.body.innerText.slice(0, 4000) : '';
  const time = (txt.match(/[^\n]*'s Team/) || [''])[0];
  const creditos = (txt.match(/\n([\d,]{5,})\n/) || ['', ''])[1];
  const logado = token || (!/Log In/.test(txt.slice(0, 3000)) && !!time);
  return { logado, token, email, time, creditos };
})()
