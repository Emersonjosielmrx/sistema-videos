// Funções comuns às páginas (API, avisos, modal, fotos). API = endereço do webhook da API ao lado desta página.
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const brl = v => 'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const num = v => Number(String(v ?? '').replace(/\./g, '').replace(',', '.')) || 0;
const numIn = v => { const s = String(v ?? '').trim(); return s.includes(',') ? num(s) : Number(s) || 0; };
const guarda = { ler(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, gravar(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) {} } };

async function api(acao, dados = {}, tentativas = 2) {
  for (let i = 0; i < tentativas; i++) {
    try {
      const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ acao, token: window.TOKEN || '', ...dados }) });
      const j = await r.json();
      if (j && j.sair && typeof sair === 'function') { sair(); throw new Error(j.erro); }
      return j;
    } catch (e) {
      if (i === tentativas - 1) return { ok: false, erro: e.message && e.message !== 'Failed to fetch' ? e.message : 'Sem conexão. Tente de novo.' };
      await new Promise(r => setTimeout(r, 900));
    }
  }
}
function aviso(msg, erro = false) {
  $$('.toast').forEach(x => x.remove());
  const t = document.createElement('div'); t.className = 'toast' + (erro ? ' er' : ''); t.textContent = msg;
  document.body.appendChild(t); setTimeout(() => t.remove(), erro ? 4500 : 2600);
}
async function chama(acao, dados, ok) {
  const j = await api(acao, dados);
  if (!j.ok) { aviso(j.erro || 'Algo deu errado.', true); return null; }
  if (ok) aviso(ok);
  return j;
}
function modal(html, aoAbrir) {
  const f = document.createElement('div'); f.className = 'modal-fundo';
  f.innerHTML = `<div class="modal" role="dialog">${html}</div>`;
  f.addEventListener('click', e => { if (e.target === f) f.remove(); });
  document.body.appendChild(f);
  const m = f.firstChild; m.fechar = () => f.remove();
  $$('[data-fechar]', m).forEach(b => b.onclick = m.fechar);
  if (aoAbrir) aoAbrir(m);
  return m;
}
function confirma(msg) { return new Promise(res => { const m = modal(`<h3>${esc(msg)}</h3><div class="acoes"><button class="btn" data-n>Não</button><button class="btn pri" data-s>Sim</button></div>`);
  $('[data-n]', m).onclick = () => { m.fechar(); res(false); }; $('[data-s]', m).onclick = () => { m.fechar(); res(true); }; }); }
// foto do celular → JPEG reduzido (base64 sem o prefixo)
function reduzFoto(arquivo, max = 1400, qual = 0.82) {
  return new Promise((res, rej) => {
    const url = URL.createObjectURL(arquivo); const img = new Image();
    img.onload = () => { const k = Math.min(1, max / Math.max(img.width, img.height)); const c = document.createElement('canvas');
      c.width = Math.round(img.width * k); c.height = Math.round(img.height * k); c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url); res(c.toDataURL('image/jpeg', qual).split(',')[1]); };
    img.onerror = () => { URL.revokeObjectURL(url); rej(new Error('Não consegui abrir essa foto (use JPG ou PNG).')); };
    img.src = url;
  });
}
function bipe() { try { const c = new (window.AudioContext || window.webkitAudioContext)(); const o = c.createOscillator(); const g = c.createGain();
  o.connect(g); g.connect(c.destination); o.frequency.value = 880; g.gain.value = .15; o.start(); setTimeout(() => { o.frequency.value = 1320; }, 140); setTimeout(() => { o.stop(); c.close(); }, 320); } catch (e) {} }
function tempoDesde(iso) { const s = Math.max(0, (Date.now() - new Date(iso)) / 1000); return s < 60 ? Math.round(s) + ' s' : s < 3600 ? Math.floor(s / 60) + ' min' : Math.floor(s / 3600) + ' h ' + Math.floor(s % 3600 / 60) + ' min'; }
function tema() { const b = $('#tema'); if (!b) return; const atual = () => document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const s = guarda.ler('tema'); if (s) document.documentElement.dataset.theme = s;
  b.onclick = () => { const n = atual() === 'dark' ? 'light' : 'dark'; document.documentElement.dataset.theme = n; guarda.gravar('tema', n); }; }
// Pix copia e cola (BR Code do Banco Central), sem API
function pixCopiaECola({ chave, nome, cidade, valor, txid }) {
  const emv = (id, v) => id + String(String(v).length).padStart(2, '0') + v;
  const ascii = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9 ]/g, '').trim().toUpperCase();
  let s = emv('00', '01') + emv('26', emv('00', 'br.gov.bcb.pix') + emv('01', chave)) + emv('52', '0000') + emv('53', '986');
  if (valor > 0) s += emv('54', valor.toFixed(2));
  s += emv('58', 'BR') + emv('59', ascii(nome).slice(0, 25) || 'LOJA') + emv('60', ascii(cidade).slice(0, 15) || 'BRASIL');
  s += emv('62', emv('05', String(txid || '***').replace(/[^A-Za-z0-9]/g, '').slice(0, 25) || '***')) + '6304';
  let crc = 0xFFFF;
  for (let i = 0; i < s.length; i++) { crc ^= s.charCodeAt(i) << 8; for (let j = 0; j < 8; j++) { crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) : (crc << 1); crc &= 0xFFFF; } }
  return s + crc.toString(16).toUpperCase().padStart(4, '0');
}
