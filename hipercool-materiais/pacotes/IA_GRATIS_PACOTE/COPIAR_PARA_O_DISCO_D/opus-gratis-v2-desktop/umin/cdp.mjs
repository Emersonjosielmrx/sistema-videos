// cdp.mjs — controla UMA janela própria no Chrome do cofre (porta: env CDP_PORTA ou ..\nav_estado.json) por CDP direto.
// Por que não Playwright: o connect_over_cdp se pendura em TODAS as abas do Chrome; com outra sessão
// usando o mesmo Chrome (Genspark) ele travou 3 min só para conectar. Aqui só falamos com a nossa janela.
// A janela é nova (newWindow): aba nova na janela dos outros tiraria a aba deles da frente.
//   node cdp.mjs ir <url> [espera_s]     | texto [limite]   | print <nome>    | fechar
//   node cdp.mjs js "<expr>"  | jsf <arquivo.js>            (avalia na página; aceita Promise)
//   node cdp.mjs clicar "<texto>"        (clique de mouse de verdade no centro do menor elemento visível com o texto)
//   node cdp.mjs clicarxy <x> <y> [espera_s]   (coordenadas do print)
//   node cdp.mjs tecla Escape|Enter|Tab  | escrever "<seletor>" "<texto>"
//   node cdp.mjs cookies <url> [url...]  (nome, validade e tamanho; nunca o valor)
//   node cdp.mjs alvos | usar <trecho-da-url> | voltar   (seguir um popup, ex. o login do Google, e voltar)
//   node cdp.mjs segredo <arquivo-destino> <arquivo.js>   (grava o texto que o JS devolver, sem mostrar)
//   node cdp.mjs rede <trecho-url> [espera_s] [regex] [arquivo]   (recarrega; lista respostas; grava o 1º grupo do regex)
//   node cdp.mjs encerrar   (fecha o Chrome todo gravando cookies — só quando fomos nós que abrimos)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const ESTADO = path.join(AQUI, 'cdp_estado.json');
const PORTA = process.env.CDP_PORTA || JSON.parse(fs.readFileSync(path.join(AQUI, '..', 'nav_estado.json'), 'utf8')).porta;
const PRINTS = path.join(AQUI, '..', 'prints');
const BASE = `http://127.0.0.1:${PORTA}`;
const dormir = (s) => new Promise((r) => setTimeout(r, s * 1000));

setTimeout(() => { console.error('ERRO: passou de 170 s, desisti (Chrome lento?)'); process.exit(2); }, 170000).unref();

function conectar(url) {
  return new Promise((ok, falha) => {
    const ws = new WebSocket(url);
    const pend = new Map();
    const ouvintes = [];
    let n = 0;
    ws.onopen = () => ok({
      on(fn) { ouvintes.push(fn); },
      send(method, params = {}, limite = 60000) {
        const id = ++n;
        ws.send(JSON.stringify({ id, method, params }));
        return new Promise((r, j) => {
          const t = setTimeout(() => { pend.delete(id); j(new Error(`sem resposta para ${method}`)); }, limite);
          pend.set(id, { r, j, t });
        });
      },
      fechar() { ws.close(); },
    });
    ws.onerror = (e) => falha(new Error(`websocket ${url}: ${e.message || e.type}`));
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.method) for (const fn of ouvintes) fn(m);
      const p = m.id && pend.get(m.id);
      if (!p) return;
      pend.delete(m.id);
      clearTimeout(p.t);
      m.error ? p.j(new Error(JSON.stringify(m.error))) : p.r(m.result);
    };
  });
}

async function json(caminho) {
  const r = await fetch(BASE + caminho, { signal: AbortSignal.timeout(20000) });
  return r.json();
}

async function navegador() {
  return conectar((await json('/json/version')).webSocketDebuggerUrl);
}

async function minhaJanela(criar = true) {
  let tid = null;
  let janela = null;
  try { ({ tid, janela } = JSON.parse(fs.readFileSync(ESTADO, 'utf8'))); } catch { /* primeira vez */ }
  const vivos = (await json('/json/list')).map((t) => t.id);
  if (tid && vivos.includes(tid)) return tid;
  if (janela && vivos.includes(janela)) {  // o popup que eu comandava fechou (login terminou): volta à janela
    fs.writeFileSync(ESTADO, JSON.stringify({ tid: janela }));
    return janela;
  }
  if (!criar) return null;
  const br = await navegador();
  tid = (await br.send('Target.createTarget', { url: 'about:blank', newWindow: true })).targetId;
  br.fechar();
  fs.writeFileSync(ESTADO, JSON.stringify({ tid }));
  return tid;
}

async function avaliar(pg, expr, limite = 60000) {
  const r = await pg.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }, limite);
  if (r.exceptionDetails) throw new Error('JS: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  return r.result.value;
}

const TEXTO = `(() => { const t = document.body ? document.body.innerText : ''; return t.split(/\\s+/).join(' '); })()`;

async function main(a) {
  const cmd = a[0];
  if (cmd === 'fechar') {
    const tid = await minhaJanela(false);
    if (tid) { const br = await navegador(); await br.send('Target.closeTarget', { targetId: tid }); br.fechar(); }
    fs.rmSync(ESTADO, { force: true });
    console.log('janela fechada');
    return;
  }
  if (cmd === 'encerrar') {  // fecha o Chrome inteiro pelo CDP (grava os cookies); só para o Chrome que NÓS abrimos
    const br = await navegador();
    await br.send('Browser.close').catch(() => {});
    fs.rmSync(ESTADO, { force: true });
    console.log('Chrome encerrado');
    return;
  }
  if (cmd === 'alvos') {  // lista as abas/popups do Chrome (para achar o popup do login do Google)
    for (const t of await json('/json/list')) if (t.type === 'page') console.log(t.id, t.url.slice(0, 110));
    return;
  }
  if (cmd === 'usar' || cmd === 'voltar') {  // passa a comandar o popup cuja URL contém o texto; voltar = nossa janela
    let st = {};
    try { st = JSON.parse(fs.readFileSync(ESTADO, 'utf8')); } catch { /* sem estado */ }
    const janela = st.janela || st.tid;
    let tid = janela;
    if (cmd === 'usar') {
      const t = (await json('/json/list')).find((x) => x.type === 'page' && x.url.includes(a[1]));
      if (!t) throw new Error(`nenhuma aba com "${a[1]}" na URL`);
      tid = t.id;
    }
    fs.writeFileSync(ESTADO, JSON.stringify(tid === janela ? { tid } : { tid, janela }));
    console.log('comandando', tid);
    return;
  }
  const tid = await minhaJanela();
  const pg = await conectar(`ws://127.0.0.1:${PORTA}/devtools/page/${tid}`);
  try {
    if (cmd === 'ir') {
      await pg.send('Page.navigate', { url: a[1] });
      await dormir(Number(a[2] || 6));
      const info = await avaliar(pg, `({u: location.href, t: document.title})`);
      console.log('URL:', info.u, '| TÍTULO:', info.t);
      console.log((await avaliar(pg, TEXTO)).slice(0, 4000));
    } else if (cmd === 'texto') {
      console.log('URL:', await avaliar(pg, 'location.href'));
      console.log((await avaliar(pg, TEXTO)).slice(0, Number(a[1] || 6000)));
    } else if (cmd === 'rede') {  // rede <trecho-url> [espera_s] [regex] [arquivo]: recarrega e olha as respostas
      const vistas = [];
      pg.on((m) => {
        if (m.method === 'Network.responseReceived' && m.params.response.url.includes(a[1])) vistas.push(m.params);
      });
      await pg.send('Network.enable', {});
      await pg.send('Page.reload', {});
      await dormir(Number(a[2] || 8));
      const re = a[3] ? new RegExp(a[3]) : null;
      for (const r of vistas) {
        let extra = '';
        if (re) {
          try {
            const { body } = await pg.send('Network.getResponseBody', { requestId: r.requestId });
            const achou = body.match(re);
            if (achou && a[4]) {
              fs.mkdirSync(path.dirname(a[4]), { recursive: true });
              fs.writeFileSync(a[4], (achou[1] || achou[0]) + '\n');
              extra = ` -> gravado em ${a[4]} (${(achou[1] || achou[0]).length} caracteres)`;
            } else extra = achou ? ' -> casou' : '';
          } catch { extra = ' (sem corpo)'; }
        }
        console.log(r.response.status, r.type, r.response.url.slice(0, 120) + extra);
      }
      await pg.send('Network.disable', {});
    } else if (cmd === 'segredo') {  // segredo <arquivo-destino> <arquivo.js>: grava o valor sem mostrar na tela
      const v = await avaliar(pg, fs.readFileSync(a[2], 'utf8'), 120000);
      if (typeof v !== 'string' || !v) throw new Error('o JS não devolveu texto: ' + JSON.stringify(v).slice(0, 200));
      fs.mkdirSync(path.dirname(a[1]), { recursive: true });
      fs.writeFileSync(a[1], v.trim() + '\n');
      console.log(`gravado em ${a[1]} (${v.trim().length} caracteres, ${v.slice(0, 4)}…${v.trim().slice(-3)})`);
    } else if (cmd === 'js' || cmd === 'jsf') {
      const expr = cmd === 'jsf' ? fs.readFileSync(a[1], 'utf8') : a[1];
      console.log(JSON.stringify(await avaliar(pg, expr, 120000)).slice(0, 12000));
    } else if (cmd === 'print') {
      fs.mkdirSync(PRINTS, { recursive: true });
      const f = path.join(PRINTS, `${a[1]}.png`);
      fs.writeFileSync(f, Buffer.from((await pg.send('Page.captureScreenshot', { format: 'png' })).data, 'base64'));
      console.log(f);
    } else if (cmd === 'clicarxy') {  // coordenadas do print (viewport)
      const [x, y] = [Number(a[1]), Number(a[2])];
      for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased']) {
        await pg.send('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: type === 'mouseMoved' ? 0 : 1 });
      }
      await dormir(Number(a[3] || 4));
      console.log('clicou em', x, y, '| URL:', await avaliar(pg, 'location.href'));
      console.log((await avaliar(pg, TEXTO)).slice(0, 1500));
    } else if (cmd === 'clicar') {
      const alvo = await avaliar(pg, `(() => {
        const q = ${JSON.stringify(a[1])}.toLowerCase();
        const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
        const cands = [...document.querySelectorAll('body *')].filter((e) => vis(e) && (e.innerText || e.value || e.getAttribute('aria-label') || '').toLowerCase().includes(q));
        if (!cands.length) return null;
        cands.sort((x, y) => x.getBoundingClientRect().width * x.getBoundingClientRect().height - y.getBoundingClientRect().width * y.getBoundingClientRect().height);
        const e = cands[0]; e.scrollIntoView({ block: 'center' }); const r = e.getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2, tag: e.tagName, txt: (e.innerText || '').slice(0, 60) };
      })()`);
      if (!alvo) throw new Error(`nada visível com o texto "${a[1]}"`);
      for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased']) {
        await pg.send('Input.dispatchMouseEvent', { type, x: alvo.x, y: alvo.y, button: 'left', clickCount: type === 'mouseMoved' ? 0 : 1 });
      }
      await dormir(Number(a[2] || 4));
      console.log('clicou em', alvo.tag, JSON.stringify(alvo.txt), '| URL:', await avaliar(pg, 'location.href'));
      console.log((await avaliar(pg, TEXTO)).slice(0, 1500));
    } else if (cmd === 'cookies') {  // só nome/validade/tamanho: o valor é segredo de login
      const { cookies } = await pg.send('Network.getCookies', { urls: a.slice(1) });
      for (const c of cookies) {
        const vence = c.expires > 0 ? new Date(c.expires * 1000).toISOString().slice(0, 16) : 'sessão';
        console.log(`${c.domain}\t${c.name}\thttpOnly=${c.httpOnly}\tvence=${vence}\ttam=${c.value.length}`);
      }
    } else if (cmd === 'tecla') {
      const k = a[1];
      const cod = { Escape: 27, Enter: 13, Tab: 9 }[k];
      for (const type of ['keyDown', 'keyUp']) {
        await pg.send('Input.dispatchKeyEvent', { type, key: k, code: k, windowsVirtualKeyCode: cod, nativeVirtualKeyCode: cod });
      }
      console.log('tecla', k);
    } else if (cmd === 'escrever') {
      const ok = await avaliar(pg, `(() => { const e = document.querySelector(${JSON.stringify(a[1])}); if (!e) return false; e.focus(); return true; })()`);
      if (!ok) throw new Error(`seletor não achado: ${a[1]}`);
      await pg.send('Input.insertText', { text: a[2] });
      console.log('escrito');
    } else {
      throw new Error(`comando desconhecido: ${cmd}`);
    }
  } finally {
    pg.fechar();
  }
}

main(process.argv.slice(2)).then(() => process.exit(0)).catch((e) => { console.error('ERRO:', e.message); process.exit(1); });
