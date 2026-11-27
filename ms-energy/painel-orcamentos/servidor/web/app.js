/* /opt/orcamentos-ms/servidor/web/app.js — painel de orçamentos MS Energy (SPA sem build)
   Rotas por hash: #/painel #/novo #/orcamento/ID #/orcamentos #/clientes #/simulador
                   #/catalogo #/empresa #/vendedores #/conta  (as 3 de admin só aparecem para admin)
   Estado global em S; o editor de orçamento usa E (dados do orçamento aberto). */
'use strict';
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const S = { eu: null, cfg: null, status: [], vendedores: [], filtros: { status: '', q: '', vendedor: '', tipo: '', de: '', ate: '' }, ordem: { col: 'id', dir: -1 }, dias: 30 };
let E = null; // editor
const ROT_ST = { rascunho: 'Rascunho', enviado: 'Enviado', negociando: 'Negociando', fechado: 'Fechado', perdido: 'Perdido' };
const TIPOS = { ongrid: 'On-grid', hibrido: 'Híbrido', micro: 'Microinversor' };

// ------------------------------------------------------------------ utilidades
const brl = (v, c = 2) => (Number(v) || 0).toLocaleString('pt-BR', { minimumFractionDigits: c, maximumFractionDigits: c });
const rs = (v, c = 2) => 'R$ ' + brl(v, c);
const rsCurto = v => { v = Number(v) || 0; if (Math.abs(v) >= 1e6) return 'R$ ' + brl(v / 1e6, 1) + ' mi'; if (Math.abs(v) >= 1e4) return 'R$ ' + brl(v / 1e3, 1) + ' mil'; return rs(v, 0); };
const num = (v, c = 0) => brl(v, c);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const dataBR = s => { if (!s) return ''; const [d, h] = String(s).split(' '); const [a, m, di] = d.split('-'); return `${di}/${m}/${a}` + (h ? ' ' + h.slice(0, 5) : ''); };
const hojeISO = () => new Date().toISOString().slice(0, 10);
const digitos = s => String(s || '').replace(/\D/g, '');
const clone = o => JSON.parse(JSON.stringify(o));
const iniciais = n => { const r = String(n || '').split(/\s+/).map(p => (p.match(/\p{L}|\p{N}/u) || [''])[0]).filter(Boolean).slice(0, 2).join('').toUpperCase(); return r || '?'; };
const cores = ['#22c55e', '#38bdf8', '#a78bfa', '#f472b6', '#facc15', '#fb923c', '#2dd4bf', '#f87171'];
const corDe = (id, c) => c || cores[(Number(id) || 0) % cores.length];
function icones() { if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 2 } }); }
function deb(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function getP(o, p) { return p.split('.').reduce((a, k) => (a == null ? a : a[k]), o); }
function setP(o, p, v) { const ks = p.split('.'); let a = o; ks.slice(0, -1).forEach(k => { if (a[k] == null || typeof a[k] !== 'object') a[k] = {}; a = a[k]; }); a[ks[ks.length - 1]] = v; }
function mascDoc(v) { const d = digitos(v).slice(0, 14); if (d.length <= 11) return d.replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2'); return d.replace(/^(\d{2})(\d)/, '$1.$2').replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3').replace(/\.(\d{3})(\d)/, '.$1/$2').replace(/(\d{4})(\d)/, '$1-$2'); }
function mascTel(v) { const d = digitos(v).slice(0, 11); if (d.length <= 10) return d.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2'); return d.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2'); }
function docValido(doc) {
  const n = digitos(doc);
  if (n.length === 11) { if (/^(\d)\1+$/.test(n)) return false; for (const t of [9, 10]) { let s = 0; for (let i = 0; i < t; i++) s += +n[i] * (t + 1 - i); if ((s * 10 % 11) % 10 !== +n[t]) return false; } return true; }
  if (n.length === 14) { if (/^(\d)\1+$/.test(n)) return false; const p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], p2 = [6, ...p1]; for (const [t, p] of [[12, p1], [13, p2]]) { let s = 0; for (let i = 0; i < t; i++) s += +n[i] * p[i]; const r = s % 11; if ((r < 2 ? 0 : 11 - r) !== +n[t]) return false; } return true; }
  return false;
}
function waLink(tel, msg) { let d = digitos(tel); if (d && !d.startsWith('55')) d = '55' + d; return `https://wa.me/${d}?text=${encodeURIComponent(msg)}`; }

async function api(metodo, url, corpo, bruto) {
  const op = { method: metodo, headers: {}, credentials: 'same-origin' };
  if (corpo !== undefined) { op.headers['Content-Type'] = 'application/json'; op.body = JSON.stringify(corpo); }
  const r = await fetch(url, op);
  if (r.status === 401 && !url.endsWith('/login')) { S.eu = null; render(); throw new Error('Entre de novo'); }
  if (bruto) { if (!r.ok) throw new Error('Erro ' + r.status); return r; }
  let j = null; try { j = await r.json(); } catch (e) { /* vazio */ }
  if (!r.ok) throw new Error((j && (j.detail || j.erro)) || ('Erro ' + r.status));
  return j;
}
function toast(msg, tipo = 'ok') { const t = document.createElement('div'); t.className = 'toast ' + tipo; t.innerHTML = msg; $('#toasts').appendChild(t); setTimeout(() => t.remove(), tipo === 'erro' ? 6000 : 3500); }
function erro(e) { toast(esc(e.message || e), 'erro'); }
function modal(html, cls = '') {
  fecharModal(); const f = document.createElement('div'); f.className = 'fundo'; f.id = 'fundo';
  f.innerHTML = `<div class="modal ${cls}">${html}</div>`; f.addEventListener('mousedown', e => { if (e.target === f) fecharModal(); });
  document.body.appendChild(f); icones(); const i = $('input,select,textarea', f); if (i) setTimeout(() => i.focus(), 50); return f;
}
function fecharModal() { $('#fundo')?.remove(); }
function gaveta(html) { fecharGaveta(); const g = document.createElement('div'); g.className = 'gaveta'; g.id = 'gaveta'; g.innerHTML = html; document.body.appendChild(g); icones(); return g; }
function fecharGaveta() { $('#gaveta')?.remove(); }
async function copiar(txt) { try { await navigator.clipboard.writeText(txt); toast('Link copiado'); } catch (e) { prompt('Copie o link:', txt); } }
async function baixar(url, nome) {
  toast('Gerando o PDF… leva alguns segundos');
  try {
    const r = await api('GET', url, undefined, true); const b = await r.blob(); const a = document.createElement('a');
    const cd = r.headers.get('Content-Disposition') || ''; const m = cd.match(/filename="?([^"]+)"?/);
    a.href = URL.createObjectURL(b); a.download = nome || (m ? decodeURIComponent(m[1]) : 'proposta.pdf'); document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000); toast('PDF pronto');
  } catch (e) { erro(e); }
}

// ------------------------------------------------------------------ gráficos SVG
function spark(vals, cor = 'var(--verde)') {
  const v = vals.length ? vals : [0, 0]; const mx = Math.max(...v, 1), w = 96, h = 36;
  const pts = v.map((y, i) => [i / (v.length - 1 || 1) * w, h - 3 - (y / mx) * (h - 8)]);
  const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const id = 'g' + Math.random().toString(36).slice(2, 7);
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${cor}" stop-opacity=".35"/><stop offset="1" stop-color="${cor}" stop-opacity="0"/></linearGradient></defs><path d="${d} L${w} ${h} L0 ${h}Z" fill="url(#${id})"/><path d="${d}" fill="none" stroke="${cor}" stroke-width="2" stroke-linecap="round"/></svg>`;
}
function anel(pct, cor = 'var(--verde)', tam = 120) {
  const r = 46, c = 2 * Math.PI * r, p = Math.max(0, Math.min(100, pct));
  return `<svg width="${tam}" height="${tam}" viewBox="0 0 120 120"><circle cx="60" cy="60" r="${r}" fill="none" stroke="rgba(255,255,255,.07)" stroke-width="12"/><circle cx="60" cy="60" r="${r}" fill="none" stroke="${cor}" stroke-width="12" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - p / 100)}" transform="rotate(-90 60 60)" style="filter:drop-shadow(0 0 6px ${cor})"/><text x="60" y="68" text-anchor="middle" font-size="24" font-weight="800" fill="currentColor">${Math.round(p)}%</text></svg>`;
}
function graficoBarras(serie) {
  const W = 760, H = 220, ml = 44, mb = 26, mt = 10, n = serie.length || 1; const mx = Math.max(...serie.map(s => s.valor), 1);
  const pw = W - ml - 8, ph = H - mb - mt, bw = Math.max(3, pw / n * .62); let g = '';
  const vazio = !serie.some(s => s.valor); for (let i = 0; i <= 4; i++) { const y = mt + ph - ph * i / 4; g += `<line x1="${ml}" x2="${W - 8}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,.06)"/>` + (vazio ? '' : `<text x="${ml - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mut)">${rsCurto(mx * i / 4).replace('R$ ', '')}</text>`); } if (vazio) g += `<text x="${W / 2}" y="${H / 2}" text-anchor="middle" font-size="13" fill="var(--mut)">Sem orçamentos no período</text>`;
  serie.forEach((s, i) => {
    const h = s.valor / mx * ph, x = ml + i * pw / n + (pw / n - bw) / 2;
    g += `<rect x="${x.toFixed(1)}" y="${(mt + ph - h).toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(h, s.valor ? 2 : 0).toFixed(1)}" rx="3" fill="url(#gb)"><title>${dataBR(s.dia)}: ${s.n} orçamento(s) · ${rs(s.valor, 0)}</title></rect>`;
    if (n <= 31 ? (i % Math.ceil(n / 10) === 0) : (i % 15 === 0)) g += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="10" fill="var(--mut)">${dataBR(s.dia).slice(0, 5)}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block"><defs><linearGradient id="gb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4ade80"/><stop offset="1" stop-color="#059669" stop-opacity=".55"/></linearGradient></defs>${g}</svg>`;
}

// ------------------------------------------------------------------ início
async function iniciar() {
  try { S.eu = await api('GET', '/api/eu'); await carregarBase(); } catch (e) { S.eu = null; }
  window.addEventListener('hashchange', render);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { fecharModal(); fecharGaveta(); $('.menu-acoes')?.remove(); }
    if (!S.eu || /input|textarea|select/i.test(document.activeElement?.tagName)) return;
    if (e.key === 'n' || e.key === 'N') { location.hash = '#/facil'; }
  });
  document.addEventListener('click', e => { if (!e.target.closest('.menu-acoes') && !e.target.closest('[data-menu]')) $('.menu-acoes')?.remove(); });
  render();
}
async function carregarBase() {
  const c = await api('GET', '/api/config'); S.cfg = c.cfg; S.status = c.status;
  try { S.vendedores = await api('GET', '/api/vendedores'); } catch (e) { S.vendedores = []; }
}

function render() {
  fecharGaveta(); if (W.timer) { clearInterval(W.timer); W.timer = null; } if (W.qrTimer) { clearInterval(W.qrTimer); W.qrTimer = null; }
  if (!S.eu) return telaLogin();
  const rota = (location.hash || '#/painel').slice(2).split('/');
  montarCasca(rota[0]);
  const alvo = $('#conteudo');
  const mapa = { painel: telaPainel, facil: telaFacil, whatsapp: telaWhatsapp, novo: () => telaEditor(null), orcamento: () => telaEditor(rota[1]), orcamentos: telaLista, clientes: telaClientes, simulador: telaSimulador, catalogo: telaCatalogo, empresa: telaEmpresa, vendedores: telaVendedores, conta: telaConta };
  const f = mapa[rota[0]] || telaPainel;
  if (['catalogo', 'empresa', 'vendedores'].includes(rota[0]) && S.eu.papel !== 'admin') { location.hash = '#/painel'; return; }
  alvo.innerHTML = '<div class="vazio"><i data-lucide="loader"></i><div>Carregando…</div></div>'; icones();
  Promise.resolve(f(alvo)).catch(erro);
  $('.app')?.classList.remove('mob-aberto');
  window.scrollTo(0, 0);
}

// ------------------------------------------------------------------ login
function telaLogin() {
  $('#raiz').innerHTML = `
  <div class="login">
    <div class="ilus">
      <div class="janela"><div class="bol"><i style="background:#ef4444"></i><i style="background:#f59e0b"></i><i style="background:#22c55e"></i></div>
        <div class="corpo"><div class="bl v"><i data-lucide="sun" style="width:44px;height:44px;color:var(--verde)"></i></div>
        <div class="bl"><i data-lucide="file-text" style="width:40px;height:40px;color:var(--mut)"></i></div>
        <div class="bl l">${spark([2, 3, 2, 5, 4, 7, 6, 9, 8, 11], '#22c55e').replace('class="spark"', 'style="width:100%;height:90px"')}</div></div></div>
      <div class="flut" style="right:0;top:22%"><i data-lucide="zap" style="color:var(--verde)"></i></div>
      <div class="flut" style="left:-6%;bottom:16%;border-radius:50%"><i data-lucide="battery-charging" style="color:var(--azul)"></i></div>
    </div>
    <form class="cartao-login" id="fLogin">
      <div style="text-align:center"><span class="selo"><i data-lucide="shield-check" style="width:14px;height:14px"></i> Acesso dos vendedores</span></div>
      <div class="logo-q"><i data-lucide="sun"></i></div>
      <h1>Bem-vindo(a) de volta</h1><p class="s">MS Energy — Orçamentos de energia solar</p>
      <div class="campo" style="margin-bottom:14px"><label>Usuário</label><input class="inp" name="usuario" autocomplete="username" placeholder="seu usuário" required></div>
      <div class="campo" style="margin-bottom:10px"><label>Senha</label><input class="inp" name="senha" type="password" autocomplete="current-password" placeholder="sua senha" required></div>
      <label class="flex mut" style="font-size:13px;margin:6px 0 18px"><input type="checkbox" name="lembrar" checked> Manter conectado por 30 dias</label>
      <button class="bt pri" style="width:100%;padding:14px">Entrar</button>
      <p class="mut" style="text-align:center;font-size:12.5px;margin:18px 0 0">Esqueceu a senha? Peça ao administrador para gerar uma nova.</p>
    </form>
  </div>`;
  icones();
  $('#fLogin').onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target); const b = $('button', e.target); b.disabled = true; b.textContent = 'Entrando…';
    try { const r = await api('POST', '/api/login', { usuario: f.get('usuario'), senha: f.get('senha'), lembrar: !!f.get('lembrar') }); S.eu = r.usuario; await carregarBase(); if (!location.hash) location.hash = '#/painel'; render(); }
    catch (er) { erro(er); b.disabled = false; b.textContent = 'Entrar'; }
  };
}

// ------------------------------------------------------------------ casca (menu lateral)
function montarCasca(rota) {
  if (!$('.app')) {
    const rec = localStorage.getItem('orc_recolhido') === '1';
    $('#raiz').innerHTML = `<div class="app ${rec ? 'recolhido' : ''}"><aside class="lateral"><div class="lat" id="lat"></div></aside><main class="principal"><div id="conteudo"></div></main></div>`;
  }
  const adm = S.eu.papel === 'admin';
  const item = (r, ic, t) => `<a href="#/${r}" class="${rota === r || (r === 'orcamentos' && rota === 'orcamento') ? 'ativo' : ''}" title="${t}"><i data-lucide="${ic}"></i><span>${t}</span></a>`;
  $('#lat').innerHTML = `
    <div class="marca"><div class="q"><i data-lucide="sun"></i></div><div><b>MS Energy</b><small>Orçamentos solares</small></div></div>
    <nav class="nav">
      <a href="#/facil" class="novo" title="Orçamento fácil (N)"><i data-lucide="sparkles"></i><span>Orçamento fácil</span></a>
      ${item('painel', 'layout-grid', 'Visão Geral')}
      ${item('novo', 'file-plus', 'Orçamento completo')}
      ${item('orcamentos', 'file-text', 'Orçamentos')}
      ${item('clientes', 'users', 'Clientes')}
      ${item('simulador', 'calculator', 'Simulador rápido')}
      ${S.eu.tem_whatsapp || adm ? item('whatsapp', 'message-circle', adm ? 'WhatsApp dos vendedores' : 'Meu WhatsApp') : ''}
      ${adm ? `<div class="sec">Administração</div>${item('catalogo', 'package', 'Catálogo e preços')}${item('vendedores', 'user-cog', 'Vendedores')}${item('empresa', 'building-2', 'Dados da empresa')}` : ''}
    </nav>
    <a href="#/conta" class="quem" title="Minha conta"><div class="ava" style="background:${corDe(S.eu.id, S.eu.cor)}">${iniciais(S.eu.nome)}</div><div style="min-width:0"><b>${esc(S.eu.nome)}</b><small>${adm ? 'Administrador' : 'Vendedor(a)'}</small></div></a>
    <div class="rod-lat">
      <button id="btTema" title="Tema claro/escuro"><i data-lucide="${document.documentElement.dataset.tema === 'claro' ? 'moon' : 'sun'}"></i></button>
      <button onclick="location.hash='#/conta'" title="Minha conta"><i data-lucide="user"></i></button>
      <button id="btSair" title="Sair"><i data-lucide="log-out"></i></button>
      <button id="btRecolher" title="Recolher menu" class="esconde-mob"><i data-lucide="chevrons-left"></i></button>
    </div>`;
  icones();
  $('#btTema').onclick = () => { const t = document.documentElement.dataset.tema === 'claro' ? '' : 'claro'; document.documentElement.dataset.tema = t; localStorage.setItem('orc_tema', t); montarCasca(rota); };
  $('#btSair').onclick = async () => { await api('POST', '/api/logout').catch(() => { }); S.eu = null; location.hash = ''; render(); };
  $('#btRecolher').onclick = () => { const a = $('.app'); a.classList.toggle('recolhido'); localStorage.setItem('orc_recolhido', a.classList.contains('recolhido') ? '1' : '0'); };
}
function topo(titulo, icone, direita = '') {
  return `<div class="topo"><button class="bt fan menu-mob" onclick="document.querySelector('.app').classList.toggle('mob-aberto')"><i data-lucide="menu"></i></button>
  <h2><i data-lucide="${icone}" style="color:var(--verde)"></i>${titulo}</h2><div class="esp"></div>${direita}</div>`;
}

// ------------------------------------------------------------------ visão geral
async function telaPainel(alvo) {
  const p = await api('GET', '/api/painel?dias=' + S.dias); const t = p.totais; const adm = S.eu.papel === 'admin';
  const serieV = p.serie.map(s => s.valor), serieN = p.serie.map(s => s.n);
  const ticket = t.n ? t.soma / t.n : 0;
  const metr = (ic, cor, rot, val, sub, sp) => `<div class="card metrica"><div class="ic" style="color:${cor}"><i data-lucide="${ic}"></i></div><div class="rot">${rot}</div><div class="val">${val}</div><div class="sub">${sub}</div>${sp || ''}</div>`;
  const funil = S.status.map(s => { const v = p.por_status[s] || { n: 0, valor: 0 }; const pct = t.n ? v.n / t.n * 100 : 0; return `<div style="margin-bottom:12px"><div class="flex" style="margin-bottom:6px"><span class="st ${s}">${ROT_ST[s]}</span><span class="esp"></span><b>${v.n}</b><span class="mut" style="font-size:12px">${rsCurto(v.valor)}</span></div><div class="barra-h"><i style="width:${pct}%"></i></div></div>`; }).join('');
  const it = o => `<div class="it" onclick="location.hash='#/orcamento/${o.id}'"><div class="ava" style="background:${corDe(o.vendedor_id)}">${iniciais(o.cliente_nome || '?')}</div><div class="esp"><b>${esc(o.cliente_nome || 'Sem nome')}</b><small>${o.num} · ${num(o.consumo)} kWh · ${adm ? esc(o.vendedor_nome) + ' · ' : ''}${dataBR(o.criado)}</small></div><div style="text-align:right"><b>${rsCurto(o.valor)}</b><span class="st ${o.status}">${ROT_ST[o.status]}</span></div></div>`;
  let metaHtml = '';
  if (p.meta && p.meta.meta) { const pc = p.meta.feito / p.meta.meta * 100; metaHtml = `<div class="card brilho"><h3><i data-lucide="target" style="color:var(--verde)"></i>Sua meta do mês</h3><div class="flex"><div class="esp"><div class="val" style="font-size:24px;font-weight:800">${rs(p.meta.feito, 0)} <span class="mut" style="font-size:14px">de ${rs(p.meta.meta, 0)}</span></div><div class="barra-h" style="margin:10px 0"><i style="width:${Math.min(pc, 100)}%"></i></div><small class="mut">Comissão estimada: <b class="verde">${rs(p.meta.feito * (p.meta.comissao_pct || 0) / 100)}</b> (${num(p.meta.comissao_pct, 1)}%)</small></div><div class="anel">${anel(pc)}</div></div></div>`; }
  alvo.innerHTML = topo('Visão Geral', 'layout-grid', `<select class="inp" style="width:auto" id="selDias">${[7, 30, 90, 365].map(d => `<option value="${d}" ${d === S.dias ? 'selected' : ''}>Últimos ${d} dias</option>`).join('')}</select><a class="bt pri" href="#/facil"><i data-lucide="sparkles"></i>Orçamento fácil</a>`) + `
  <div class="card heroi"><div><h1><i data-lucide="zap"></i>${adm ? 'Visão geral das vendas' : 'Olá, ' + esc(S.eu.nome.split(' ')[0]) + '!'}</h1><p>${adm ? 'Acompanhe em tempo real os orçamentos de toda a equipe.' : 'Acompanhe seus orçamentos e o que os clientes estão vendo.'}</p></div><span class="pilula v"><i data-lucide="activity" style="width:14px;height:14px"></i>Sistema operante</span></div>
  ${metaHtml ? '<div style="margin-top:16px">' + metaHtml + '</div>' : ''}
  <div class="secao-t">Resultados do período</div>
  <div class="grade g4">
    ${metr('file-text', 'var(--verde)', 'Orçamentos feitos', num(t.n), `${num(t.kwp, 1)} kWp orçados`, spark(serieN))}
    ${metr('dollar-sign', 'var(--azul)', 'Valor orçado', rsCurto(t.soma), `Ticket médio ${rsCurto(ticket)}`, spark(serieV, '#38bdf8'))}
    ${metr('badge-check', 'var(--verde)', 'Vendas fechadas', rsCurto(t.fechado), `${num(t.nf)} contrato(s)`, spark(serieV.map((v, i) => v * .3 + i), '#22c55e'))}
    <div class="card metrica anel"><div>${anel(p.conversao)}</div><div class="rot" style="margin-top:6px">Taxa de fechamento</div><div class="sub">fechados ÷ (fechados + perdidos)</div></div>
  </div>
  <div class="grade g21" style="margin-top:16px">
    <div class="card"><h3><i data-lucide="bar-chart-3" style="color:var(--verde)"></i>Volume orçado por dia<span class="esp"></span><span class="pilula">${num(t.views)} visualizações dos clientes</span></h3>${graficoBarras(p.serie)}</div>
    <div class="card"><h3><i data-lucide="filter" style="color:var(--verde)"></i>Funil de vendas</h3>${funil}</div>
  </div>
  <div class="grade g3" style="margin-top:16px">
    <div class="card"><h3><i data-lucide="bell-ring" style="color:var(--amarelo)"></i>Retornar hoje</h3><div class="lista-mini">${p.retornos.map(it).join('') || '<div class="vazio" style="padding:20px">Nenhum retorno marcado para hoje.</div>'}</div></div>
    <div class="card"><h3><i data-lucide="eye" style="color:var(--azul)"></i>Clientes que abriram a proposta</h3><div class="lista-mini">${p.vistos.map(o => `<div class="it" onclick="location.hash='#/orcamento/${o.id}'"><i data-lucide="eye" style="color:var(--azul)"></i><div class="esp"><b>${esc(o.cliente_nome || 'Sem nome')}</b><small>${o.visualizacoes}× · última ${dataBR(o.ultima_visualizacao)}</small></div><b>${rsCurto(o.valor)}</b></div>`).join('') || '<div class="vazio" style="padding:20px">Quando o cliente abrir o link, aparece aqui.</div>'}</div></div>
    <div class="card"><h3><i data-lucide="${adm ? 'trophy' : 'pie-chart'}" style="color:var(--amarelo)"></i>${adm ? 'Ranking dos vendedores' : 'Por tipo de sistema'}</h3>
      ${adm ? (p.ranking.map((r, i) => `<div class="flex" style="padding:9px 0;border-bottom:1px dashed var(--borda)"><b style="width:22px;color:${i < 3 ? 'var(--amarelo)' : 'var(--mut)'}">${i + 1}º</b><div class="ava" style="background:${corDe(r.vendedor_id)};width:30px;height:30px">${iniciais(r.nome)}</div><div class="esp"><b>${esc(r.nome)}</b><small class="mut">${r.n} orçamentos · ${rsCurto(r.v)}</small></div><b class="verde">${rsCurto(r.f)}</b></div>`).join('') || '<div class="vazio" style="padding:20px">Sem orçamentos no período.</div>')
      : Object.entries(p.por_tipo).map(([k, v]) => `<div class="flex" style="padding:8px 0"><span class="esp">${TIPOS[k] || k}</span><b>${v}</b></div>`).join('') || '<div class="vazio" style="padding:20px">Sem dados.</div>'}
      <div class="sep"></div><small class="mut">Faixas de consumo</small>${Object.entries(p.faixas).map(([k, v]) => `<div class="flex" style="padding:4px 0"><span class="esp mut">${k} kWh</span><b>${v}</b></div>`).join('')}
    </div>
  </div>
  <div class="card" style="margin-top:16px"><h3><i data-lucide="clock" style="color:var(--verde)"></i>Últimos orçamentos<span class="esp"></span><a href="#/orcamentos" class="bt peq">Ver todos</a></h3><div class="lista-mini">${p.recentes.map(it).join('') || `<div class="vazio"><i data-lucide="file-plus"></i><div>Nenhum orçamento ainda.</div><a class="bt pri" href="#/novo" style="margin-top:12px">Fazer o primeiro</a></div>`}</div></div>`;
  icones();
  $('#selDias').onchange = e => { S.dias = +e.target.value; render(); };
}

// ------------------------------------------------------------------ editor de orçamento
function dadosPadrao() {
  const c = S.cfg;
  return {
    cliente_nome: '', cliente_doc: '', cliente_tel: '', cliente_email: '', cliente_endereco: '', cliente_cidade: '', cliente_uc: '',
    modo_consumo: 'kwh', consumo: '', conta_rs: '', meses: Array(12).fill(''), folga_pct: 0,
    tipo: 'ongrid', painel_id: c.paineis[0]?.id, n_manual: false, n_paineis: '', inv_manual: false, inversor_id: '', qtd_inversor: '',
    estrutura_id: 'ceramico', ligacao: '', grupo: 'Grupo B1 – Residencial', tarifa: c.calculo.tarifa, minimo_manual: false, minimo: '',
    extras: [], baterias: [], valor_manual: false, valor: '', mostrar_desconto: false, validade_dias: c.empresa.validade_dias,
    pagamento: clone(c.pagamento), financeiras_ids: c.financeiras.filter(f => f.ativo).map(f => f.id), tabela_prazos: true,
    observacoes: '', porque_txt: '', status: 'rascunho', proximo_contato: '', vendedor_id: ''
  };
}
function prepararDados(d) {
  const o = clone(d);
  if (o.modo_consumo === 'conta' && o.conta_rs) o.consumo = Math.round(Number(o.conta_rs) / (Number(o.tarifa) || S.cfg.calculo.tarifa));
  if (o.modo_consumo === 'meses') { const v = o.meses.map(Number).filter(x => x > 0); o.consumo = v.length ? Math.round(v.reduce((a, b) => a + b, 0) / v.length) : ''; }
  o.consumo = Number(o.consumo) || 0;
  o.porque = (o.porque_txt || '').split('\n').map(s => s.trim()).filter(Boolean);
  if (!o.porque.length) delete o.porque;
  ['tarifa', 'folga_pct', 'valor', 'minimo', 'n_paineis', 'qtd_inversor', 'validade_dias'].forEach(k => { if (o[k] !== '' && o[k] != null) o[k] = Number(o[k]); });
  return o;
}
const PASSOS = [['cliente', 'user', 'Cliente'], ['consumo', 'gauge', 'Consumo'], ['sistema', 'sun', 'Sistema'], ['itens', 'package-plus', 'Itens extras'], ['preco', 'wallet', 'Preço e pagamento'], ['final', 'send', 'Revisão e envio']];

async function telaEditor(id) {
  const alvo = $('#conteudo');
  E = { id: id ? +id : null, passo: 0, dados: dadosPadrao(), res: null, orc: null };
  if (id) {
    const o = await api('GET', '/api/orcamentos/' + id); E.orc = o; E.dados = Object.assign(dadosPadrao(), o.dados);
    E.dados.status = o.status; E.dados.vendedor_id = o.vendedor_id;
  } else {
    const rasc = sessionStorage.getItem('orc_sim'); if (rasc) { Object.assign(E.dados, JSON.parse(rasc)); sessionStorage.removeItem('orc_sim'); }
  }
  const tit = id ? `Orçamento ${E.orc.num}` : 'Novo orçamento';
  const dir = id ? `<span class="st ${E.orc.status}">${ROT_ST[E.orc.status]}</span><button class="bt" id="btHist"><i data-lucide="history"></i><span class="esconde-mob">Histórico</span></button>` : '';
  alvo.innerHTML = topo(tit, id ? 'file-pen' : 'file-plus', dir) + `
   <div class="editor"><div><div class="passos" id="passos"></div><div id="passoCorpo"></div>
     <div class="flex" style="margin-top:16px"><button class="bt" id="btVoltar"><i data-lucide="arrow-left"></i>Voltar</button><span class="esp"></span><button class="bt" id="btPrevia"><i data-lucide="eye"></i><span class="esconde-mob">Prévia</span></button><button class="bt pri" id="btAvancar">Avançar<i data-lucide="arrow-right"></i></button></div>
   </div><div class="resumo" id="resumo"></div></div>`;
  $('#btVoltar').onclick = () => irPasso(E.passo - 1);
  $('#btAvancar').onclick = () => E.passo < PASSOS.length - 1 ? irPasso(E.passo + 1) : salvar();
  $('#btPrevia').onclick = previa;
  if (id) $('#btHist').onclick = () => abrirDetalhe(E.id);
  irPasso(0); calcular();
}
function irPasso(n) {
  if (n < 0 || n >= PASSOS.length) return;
  if (n > 0 && E.passo === 0 && !E.dados.cliente_nome.trim()) { toast('Coloque pelo menos o nome do cliente', 'erro'); $('[data-k="cliente_nome"]')?.focus(); return; }
  if (n > 1 && E.passo === 1 && !prepararDados(E.dados).consumo) { toast('Informe o consumo do cliente', 'erro'); return; }
  E.passo = n;
  $('#passos').innerHTML = PASSOS.map((p, i) => `<div class="passo ${i === n ? 'on' : i < n ? 'ok' : ''}" data-i="${i}"><span class="n">${i < n ? '✓' : i + 1}</span>${p[2]}</div>`).join('');
  $$('#passos .passo').forEach(el => el.onclick = () => irPasso(+el.dataset.i));
  desenharPasso();
  const av = $('#btAvancar'); av.innerHTML = n === PASSOS.length - 1 ? `<i data-lucide="save"></i>${E.id ? 'Salvar alterações' : 'Salvar orçamento'}` : 'Avançar<i data-lucide="arrow-right"></i>';
  $('#btVoltar').style.visibility = n ? 'visible' : 'hidden'; icones();
  $('#passos .on')?.scrollIntoView({ block: 'nearest', inline: 'center' });
}
function campo(k, rot, tipo = 'text', extra = {}) {
  const v = getP(E.dados, k) ?? '';
  const inp = tipo === 'textarea' ? `<textarea class="inp" data-k="${k}" placeholder="${esc(extra.ph || '')}">${esc(v)}</textarea>`
    : tipo === 'select' ? `<select class="inp" data-k="${k}">${extra.ops.map(([val, t]) => `<option value="${esc(val)}" ${String(val) === String(v) ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>`
      : `<input class="inp" data-k="${k}" type="${tipo}" value="${esc(v)}" placeholder="${esc(extra.ph || '')}" ${extra.attr || ''}>`;
  const env = extra.pre ? `<div class="inp-pre"><span>${extra.pre}</span>${inp}</div>` : extra.suf ? `<div class="inp-suf">${inp}<span>${extra.suf}</span></div>` : inp;
  return `<div class="campo" ${extra.span ? `style="grid-column:span ${extra.span}"` : ''}><label>${rot}</label>${env}${extra.dica ? `<span class="dica" ${extra.idDica ? `id="${extra.idDica}"` : ''}>${extra.dica}</span>` : ''}</div>`;
}
function chave(k, extraAttr = '') { return `<label class="chave"><input type="checkbox" data-k="${k}" ${getP(E.dados, k) ? 'checked' : ''} ${extraAttr}><i></i></label>`; }
function ligarCampos(raiz) {
  $$('[data-k]', raiz).forEach(el => {
    const k = el.dataset.k;
    const ev = el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(ev, () => {
      let v = el.type === 'checkbox' ? el.checked : el.value;
      if (k === 'cliente_doc') { el.value = mascDoc(el.value); v = el.value; validarDoc(); }
      if (k === 'cliente_tel') { el.value = mascTel(el.value); v = el.value; }
      setP(E.dados, k, v);
      if (el.dataset.redesenha) desenharPasso();
      calcularDeb();
    });
  });
}
function validarDoc() {
  const el = $('[data-k="cliente_doc"]'); const d = $('#dicaDoc'); if (!el || !d) return;
  const n = digitos(el.value);
  if (!n) { d.textContent = 'Opcional · aparece na proposta e na simulação do financiamento'; el.classList.remove('erro'); return; }
  const ok = docValido(n); el.classList.toggle('erro', !ok && (n.length === 11 || n.length === 14));
  d.innerHTML = (n.length === 11 || n.length === 14) ? (ok ? '<span class="verde">✓ ' + (n.length === 11 ? 'CPF' : 'CNPJ') + ' válido</span>' : '<span style="color:#f87171">Dígitos não conferem — confira o número</span>') : 'Digitando…';
}
function desenharPasso() {
  const c = S.cfg, d = E.dados, corpo = $('#passoCorpo'); const p = PASSOS[E.passo][0]; let h = '';
  if (p === 'cliente') {
    h = `<div class="card"><h3><i data-lucide="user" style="color:var(--verde)"></i>Dados do cliente</h3>
      <div class="linha">${campo('cliente_nome', 'Nome completo *', 'text', { ph: 'Ex.: Maria de Fátima da Silva', span: 2 })}
      ${campo('cliente_doc', 'CPF ou CNPJ', 'text', { ph: '000.000.000-00', dica: '', idDica: 'dicaDoc', attr: 'inputmode="numeric"' })}
      ${campo('cliente_tel', 'WhatsApp', 'tel', { ph: '(91) 90000-0000', attr: 'inputmode="tel"' })}
      ${campo('cliente_email', 'E-mail', 'email', { ph: 'opcional' })}
      ${campo('cliente_cidade', 'Cidade', 'text', { ph: 'Ex.: Capitão Poço – PA' })}
      ${campo('cliente_endereco', 'Endereço', 'text', { ph: 'Rua, número, bairro, CEP', span: 2 })}
      ${campo('cliente_uc', 'Unidade consumidora (UC)', 'text', { ph: 'número na conta de luz' })}
      ${campo('grupo', 'Tipo de unidade', 'select', { ops: [['Grupo B1 – Residencial', 'Residencial (B1)'], ['Grupo B2 – Rural', 'Rural (B2)'], ['Grupo B3 – Comercial / Serviços', 'Comercial / serviços (B3)'], ['Grupo B3 – Industrial', 'Industrial (B3)'], ['Grupo A – Média tensão', 'Média tensão (Grupo A)']] })}
      ${S.eu.papel === 'admin' ? campo('vendedor_id', 'Vendedor responsável', 'select', { ops: [['', 'Eu mesmo(a)'], ...S.vendedores.filter(v => v.ativo).map(v => [v.id, v.nome])] }) : ''}</div></div>`;
  }
  if (p === 'consumo') {
    const m = d.modo_consumo;
    h = `<div class="card"><h3><i data-lucide="gauge" style="color:var(--verde)"></i>Quanto o cliente gasta de energia?</h3>
      <div class="opcoes" style="margin-bottom:16px">${[['kwh', 'zap', 'Consumo em kWh', 'O número da conta de luz (média mensal)'], ['conta', 'receipt', 'Valor da conta (R$)', 'Converto pelo preço do kWh'], ['meses', 'calendar-range', 'Histórico de 12 meses', 'Faço a média dos meses da conta']].map(([v, ic, t, s]) => `<div class="opc ${m === v ? 'on' : ''}" data-modo="${v}"><div class="ic"><i data-lucide="${ic}"></i></div><b>${t}</b><small>${s}</small></div>`).join('')}</div>
      <div class="linha">
      ${m === 'kwh' ? campo('consumo', 'Consumo médio por mês', 'number', { suf: 'kWh', ph: 'Ex.: 500', attr: 'min="0" inputmode="numeric"' }) : ''}
      ${m === 'conta' ? campo('conta_rs', 'Valor médio da conta de luz', 'number', { pre: 'R$', ph: 'Ex.: 650', attr: 'min="0" inputmode="decimal"', dica: 'Convertido em kWh pelo preço do kWh abaixo' }) : ''}
      ${campo('tarifa', 'Preço do kWh com impostos', 'number', { pre: 'R$', attr: 'step="0.01" min="0"', dica: 'Média da Equatorial: R$ ' + brl(c.calculo.tarifa) })}
      ${campo('folga_pct', 'Folga para aumentar o consumo', 'number', { suf: '%', attr: 'min="0" max="200" step="5"', dica: 'Ex.: 20% se vai comprar ar-condicionado' })}
      </div>
      ${m === 'meses' ? `<div class="campo" style="margin-top:14px"><label>Consumo de cada mês (kWh) — deixe em branco os que não tiver</label><div class="meses">${['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'].map((n, i) => `<div><small class="mut">${n}</small><input class="inp" type="number" data-k="meses.${i}" value="${esc(d.meses[i] || '')}"></div>`).join('')}</div></div>` : ''}
      <div id="consumoInfo" style="margin-top:14px"></div></div>`;
  }
  if (p === 'sistema') {
    const tipos = [['ongrid', 'sun', 'On-grid', 'Ligado à rede, sem bateria. O mais vendido e o retorno mais rápido.'], ['hibrido', 'battery-charging', 'Híbrido com bateria', 'Rede + bateria: tem energia quando falta luz.'], ['micro', 'grid-3x3', 'Microinversor', 'Cada painel trabalha sozinho; ótimo com sombra.']];
    const ests = [['ceramico', 'home', 'Telha cerâmica'], ['fibrocimento', 'warehouse', 'Fibrocimento'], ['metalico', 'factory', 'Telha metálica'], ['laje', 'building', 'Laje'], ['solo', 'trees', 'Solo (mesa)']];
    const invs = c.inversores.filter(i => i.tipo === (d.tipo === 'micro' ? 'micro' : d.tipo) || (d.tipo !== 'micro' && i.tipo === 'ongrid' && d.tipo === 'hibrido' && false));
    h = `<div class="card"><h3><i data-lucide="sun" style="color:var(--verde)"></i>Tipo de sistema</h3>
      <div class="opcoes">${tipos.map(([v, ic, t, s]) => `<div class="opc ${d.tipo === v ? 'on' : ''}" data-tipo="${v}"><div class="ic"><i data-lucide="${ic}"></i></div><b>${t}</b><small>${s}</small></div>`).join('')}</div></div>
      <div class="card" style="margin-top:14px"><h3><i data-lucide="panels-top-left" style="color:var(--verde)"></i>Painéis e inversor<span class="esp"></span><span class="pilula v" id="pilAuto">dimensionado automaticamente</span></h3>
      <div class="linha">
        ${campo('painel_id', 'Painel solar', 'select', { ops: c.paineis.map(x => [x.id, `${x.w} W · ${x.nome.replace(/PAINEL SOLAR \d+ W /, '')}`]) })}
        <div class="campo"><label class="flex">Quantidade de painéis <span class="esp"></span>${chave('n_manual', 'data-redesenha="1"')} <small class="mut">manual</small></label>
          <input class="inp" type="number" data-k="n_paineis" min="1" ${d.n_manual ? '' : 'disabled'} value="${esc(d.n_paineis || '')}" placeholder="automático"></div>
        <div class="campo"><label class="flex">Inversor <span class="esp"></span>${chave('inv_manual', 'data-redesenha="1"')} <small class="mut">manual</small></label>
          <select class="inp" data-k="inversor_id" ${d.inv_manual ? '' : 'disabled'}>${(invs.length ? invs : c.inversores).map(i => `<option value="${i.id}" ${i.id === d.inversor_id ? 'selected' : ''}>${esc(i.curto)}</option>`).join('')}</select></div>
        ${d.inv_manual ? campo('qtd_inversor', 'Qtd. de inversores', 'number', { attr: 'min="1"' }) : ''}
        ${campo('ligacao', 'Ligação (padrão de entrada)', 'select', { ops: [['', 'Automático'], ['Monofásico', 'Monofásico'], ['Bifásico', 'Bifásico'], ['Trifásico', 'Trifásico']] })}
      </div></div>
      <div class="card" style="margin-top:14px"><h3><i data-lucide="home" style="color:var(--verde)"></i>Onde os painéis vão ficar</h3>
      <div class="opcoes">${ests.map(([v, ic, t]) => `<div class="opc ${d.estrutura_id === v ? 'on' : ''}" data-estr="${v}"><div class="ic"><i data-lucide="${ic}"></i></div><b>${t}</b></div>`).join('')}</div></div>
      ${d.tipo === 'hibrido' ? `<div class="card brilho" style="margin-top:14px"><h3><i data-lucide="battery-charging" style="color:var(--verde)"></i>Baterias (cada uma vira um valor separado na proposta)</h3>
        <p class="mut" style="margin-top:-6px">A proposta mostra o valor <b>sem bateria</b> e um valor <b>com cada bateria</b> marcada, cada um com a sua página de pagamento.</p>
        <div class="grade" style="gap:10px">${c.baterias.map(b => { const sel = d.baterias.find(x => x.id === b.id); return `<div class="item-ex ${sel ? 'on' : ''}"><i data-lucide="battery-full" style="color:var(--verde)"></i><div class="esp"><b>${esc(b.nome)}</b><small>${esc(b.desc)}</small></div>
          ${sel && S.eu.papel === 'admin' ? `<div class="inp-pre" style="width:150px"><span>R$</span><input class="inp" type="number" value="${sel.preco ?? b.preco}" data-bat-preco="${b.id}"></div>` : `<b>${rs(b.preco, 0)}</b>`}
          <label class="chave"><input type="checkbox" data-bat="${b.id}" ${sel ? 'checked' : ''}><i></i></label></div>`; }).join('')}</div></div>` : ''}`;
  }
  if (p === 'itens') {
    h = `<div class="card"><h3><i data-lucide="package-plus" style="color:var(--verde)"></i>Itens extras<span class="esp"></span><button class="bt peq" id="btItemLivre"><i data-lucide="plus"></i>Outro custo / item</button></h3>
      <p class="mut" style="margin-top:-6px">Ar-condicionado, poste, carregador… O valor de cada item já entra no orçamento.</p>
      <div class="grade" style="gap:10px">${c.extras.map(x => { const sel = d.extras.find(e => e.id === x.id); return `<div class="item-ex ${sel ? 'on' : ''}"><div class="esp"><b>${esc(x.nome)}</b><small>${esc(x.desc)}</small></div>
        ${sel && S.eu.papel === 'admin' ? `<div class="inp-pre" style="width:130px"><span>R$</span><input class="inp" type="number" value="${sel.preco ?? x.preco}" data-ex-preco="${x.id}"></div>`
          : sel && x.preco_livre ? `<div class="inp-pre" style="width:150px"><span>R$</span><input class="inp" type="number" min="0" placeholder="seu preço" value="${sel.preco_vendedor || ''}" data-ex-pv="${x.id}"></div>`
          : `<b style="white-space:nowrap">${x.preco_livre ? '<small class="mut">você põe o preço</small>' : rs(x.preco, 0)}</b>`}
        <div class="qtd"><button data-ex-menos="${x.id}">−</button><span>${sel ? sel.qtd : 0}</span><button data-ex-mais="${x.id}">+</button></div></div>`; }).join('')}
      ${d.extras.filter(e => !c.extras.find(x => x.id === e.id)).map((e, i) => `<div class="item-ex on"><div class="esp"><b>${esc(e.nome)}</b><small>${esc(e.desc || 'Item livre')}</small></div><b>${rs(e.preco, 0)} × ${e.qtd}</b><button class="bt fan peq" data-livre-rm="${esc(e.id)}"><i data-lucide="trash-2"></i></button></div>`).join('')}
      </div>
      ${d.extras.length && S.eu.papel === 'admin' ? `<div class="sep"></div><div class="flex wrap">${d.extras.map(e => `<label class="chip ${e.no_valor === false ? 'on' : ''}"><input type="checkbox" data-cortesia="${esc(e.id)}" ${e.no_valor === false ? 'checked' : ''} style="display:none">🎁 ${esc(e.nome.split(' ').slice(0, 3).join(' '))} como cortesia</label>`).join('')}</div>` : ''}</div>`;
  }
  if (p === 'preco') {
    const pg = d.pagamento;
    const adm = S.eu.papel === 'admin';
    const bloco = (k, ic, t, corpoB) => `<div class="bloco-pag ${getP(pg, k + '.ativo') ? '' : 'off'}"><div class="cab"><i data-lucide="${ic}" style="color:var(--verde)"></i><b>${t}</b>${chave('pagamento.' + k + '.ativo', 'data-redesenha="1"')}</div>${getP(pg, k + '.ativo') && adm ? `<div class="corpo"><div class="linha">${corpoB}</div></div>` : ''}</div>`;
    h = `<div class="card brilho"><h3><i data-lucide="badge-dollar-sign" style="color:var(--verde)"></i>Preço da proposta</h3>
      <div id="precoInfo"></div>
      <div class="linha" style="margin-top:12px">
        <div class="campo"><label class="flex">${adm ? 'Valor final (sem bateria)' : 'Valor do orçamento'} <span class="esp"></span>${chave('valor_manual', 'data-redesenha="1"')} <small class="mut">${adm ? 'mudar' : 'aumentar'}</small></label>
          <div class="inp-pre"><span>R$</span><input class="inp" type="number" step="100" data-k="valor" ${d.valor_manual ? '' : 'disabled'} value="${esc(d.valor || '')}" placeholder="preço sugerido"></div>
          <span class="dica">${adm ? 'Valor livre para o administrador' : 'Você pode aumentar o valor, mas não baixar'}</span></div>
        ${campo('validade_dias', 'Validade da proposta', 'number', { suf: 'dias', attr: 'min="1"' })}
        <div class="campo" ${adm ? '' : 'style="display:none"'}><label>Mostrar o desconto riscado</label><div class="flex" style="height:44px">${chave('mostrar_desconto')}<small class="mut">“de R$ X por R$ Y”</small></div></div>
      </div></div>
      <div class="card" style="margin-top:14px"><h3><i data-lucide="credit-card" style="color:var(--verde)"></i>Formas de pagamento na proposta</h3>
      ${bloco('avista', 'banknote', 'À vista (PIX)', campo('pagamento.avista.desconto_pct', 'Desconto à vista', 'number', { suf: '%', attr: 'min="0" max="30" step="0.5"' }))}
      ${bloco('direto', 'split', 'Parcelamento direto MS Energy', campo('pagamento.direto.pct1', '1ª parte (% do valor)', 'number', { suf: '%', attr: 'min="0" max="100"' }) + campo('pagamento.direto.n1', '1ª parte em', 'number', { suf: 'vezes' }) + campo('pagamento.direto.boleto_n', '2ª parte no boleto em', 'number', { suf: 'vezes' }) + campo('pagamento.direto.cartao_n', 'ou no cartão em', 'number', { suf: 'vezes' }))}
      ${bloco('cartao', 'credit-card', 'Cartão de crédito (valor todo)', campo('pagamento.cartao.n', 'Parcelas', 'number', { suf: 'vezes' }) + campo('pagamento.cartao.juros_am', 'Juros ao mês (0 = sem juros)', 'number', { attr: 'step="0.001"', dica: 'Ex.: 0.0199 = 1,99% a.m.' }))}
      ${bloco('entrada', 'hand-coins', 'Entrada + financiamento', campo('pagamento.entrada.pct', 'Entrada', 'number', { suf: '%', attr: 'min="0" max="90"' }))}
      <div class="bloco-pag ${pg.financiamento.ativo ? '' : 'off'}"><div class="cab"><i data-lucide="landmark" style="color:var(--verde)"></i><b>Simulação de financiamento</b>${chave('pagamento.financiamento.ativo', 'data-redesenha="1"')}</div>
        ${pg.financiamento.ativo ? `<div class="corpo"><div class="chips">${c.financeiras.map(f => `<span class="chip ${d.financeiras_ids.includes(f.id) ? 'on' : ''}" data-fin="${f.id}">${esc(f.nome.split(' –')[0])} <small>${f.prazo}× · ${brl(f.taxa * 100, 2)}%</small></span>`).join('')}</div>
          <label class="flex mut" style="margin-top:12px;font-size:13px">${chave('tabela_prazos')} Mostrar tabela de parcelas por prazo (24× a 120×)</label>
          <div id="finInfo" style="margin-top:12px"></div></div>` : ''}</div></div>`;
  }
  if (p === 'final') {
    h = `<div class="card"><h3><i data-lucide="message-square-text" style="color:var(--verde)"></i>Texto da proposta</h3>
      <div class="linha">${campo('observacoes', 'Observações para o cliente (aparece na proposta)', 'textarea', { ph: 'Ex.: Valor válido para pagamento até o dia 10. Inclui visita técnica gratuita.', span: 2 })}
      ${campo('porque_txt', '“Por que esta solução?” — uma linha por item (vazio = automático)', 'textarea', { ph: 'Deixe vazio para o texto automático', span: 2 })}</div></div>
      <div class="card" style="margin-top:14px"><h3><i data-lucide="calendar-clock" style="color:var(--verde)"></i>Acompanhamento</h3>
      <div class="linha">${campo('status', 'Status', 'select', { ops: S.status.map(s => [s, ROT_ST[s]]) })}${campo('proximo_contato', 'Lembrar de retornar em', 'date')}</div></div>
      <div class="card brilho" style="margin-top:14px" id="cardEnvio"><h3><i data-lucide="send" style="color:var(--verde)"></i>Tudo pronto?</h3>
      <p class="mut">Ao salvar, a proposta ganha um número e um <b>link para o cliente</b> (que você pode mandar no WhatsApp). Você também pode baixar o PDF.</p>
      ${E.id ? acoesEnvio(E.orc) : ''}</div>`;
  }
  corpo.innerHTML = h; icones(); ligarCampos(corpo);
  if (p === 'cliente') validarDoc();
  $$('[data-modo]', corpo).forEach(el => el.onclick = () => { E.dados.modo_consumo = el.dataset.modo; desenharPasso(); calcularDeb(); });
  $$('[data-tipo]', corpo).forEach(el => el.onclick = () => { E.dados.tipo = el.dataset.tipo; E.dados.inv_manual = false; if (el.dataset.tipo !== 'hibrido') E.dados.baterias = []; desenharPasso(); calcularDeb(); });
  $$('[data-estr]', corpo).forEach(el => el.onclick = () => { E.dados.estrutura_id = el.dataset.estr; desenharPasso(); calcularDeb(); });
  $$('[data-bat]', corpo).forEach(el => el.onchange = () => { const id = el.dataset.bat; if (el.checked) { const b = c.baterias.find(x => x.id === id); E.dados.baterias.push({ id, qtd: 1 }); } else E.dados.baterias = E.dados.baterias.filter(x => x.id !== id); desenharPasso(); calcularDeb(); });
  $$('[data-bat-preco]', corpo).forEach(el => el.oninput = () => { const b = E.dados.baterias.find(x => x.id === el.dataset.batPreco); if (b) b.preco = Number(el.value); calcularDeb(); });
  $$('[data-ex-mais],[data-ex-menos]', corpo).forEach(el => el.onclick = () => {
    const id = el.dataset.exMais || el.dataset.exMenos; const mais = !!el.dataset.exMais; let e = E.dados.extras.find(x => x.id === id);
    if (!e && mais) { const x = c.extras.find(y => y.id === id); E.dados.extras.push({ id, qtd: 1 }); }
    else if (e) { e.qtd += mais ? 1 : -1; if (e.qtd <= 0) E.dados.extras = E.dados.extras.filter(y => y.id !== id); }
    desenharPasso(); calcularDeb();
  });
  $$('[data-ex-pv]', corpo).forEach(el => el.oninput = () => { const e = E.dados.extras.find(x => x.id === el.dataset.exPv); if (e) e.preco_vendedor = Number(el.value) || 0; calcularDeb(); });
  $$('[data-ex-preco]', corpo).forEach(el => el.oninput = () => { const e = E.dados.extras.find(x => x.id === el.dataset.exPreco); if (e) e.preco = Number(el.value); calcularDeb(); });
  $$('[data-cortesia]', corpo).forEach(el => el.onchange = () => { const e = E.dados.extras.find(x => x.id === el.dataset.cortesia); if (e) e.no_valor = !el.checked; desenharPasso(); calcularDeb(); });
  $$('[data-livre-rm]', corpo).forEach(el => el.onclick = () => { E.dados.extras = E.dados.extras.filter(x => x.id !== el.dataset.livreRm); desenharPasso(); calcularDeb(); });
  $('#btItemLivre', corpo) && ($('#btItemLivre', corpo).onclick = itemLivre);
  $$('[data-fin]', corpo).forEach(el => el.onclick = () => { const id = el.dataset.fin; const l = E.dados.financeiras_ids; E.dados.financeiras_ids = l.includes(id) ? l.filter(x => x !== id) : [...l, id]; desenharPasso(); calcularDeb(); });
  $$('#cardEnvio [data-acao]', corpo).forEach(ligarAcao);
  atualizarInfos();
}
function itemLivre() {
  const f = modal(`<h3><i data-lucide="plus"></i>Item livre</h3><div class="grade" style="gap:12px">
    <div class="campo"><label>Nome do item</label><input class="inp" id="lvNome" placeholder="Ex.: TOMADA DE 20 A NA GARAGEM"></div>
    <div class="campo"><label>Descrição</label><input class="inp" id="lvDesc" placeholder="opcional"></div>
    <div class="linha"><div class="campo"><label>Preço unitário</label><div class="inp-pre"><span>R$</span><input class="inp" id="lvPreco" type="number" value="0"></div></div>
    <div class="campo"><label>Quantidade</label><input class="inp" id="lvQtd" type="number" value="1" min="1"></div>
    <div class="campo"><label>Unidade</label><select class="inp" id="lvUn"><option>PC</option><option>SV</option><option>M</option><option>KIT</option><option>CJ</option></select></div></div></div>
    <div class="acoes"><button class="bt" onclick="fecharModal()">Cancelar</button><button class="bt pri" id="lvOk">Adicionar</button></div>`);
  $('#lvOk', f).onclick = () => { const n = $('#lvNome').value.trim(); if (!n) return toast('Dê um nome ao item', 'erro'); E.dados.extras.push({ id: 'livre_' + Date.now(), nome: n.toUpperCase(), desc: $('#lvDesc').value, preco: Number($('#lvPreco').value) || 0, qtd: Number($('#lvQtd').value) || 1, unid: $('#lvUn').value, icone: 'protecao' }); fecharModal(); desenharPasso(); calcularDeb(); };
}
const calcularDeb = deb(calcular, 280);
async function calcular() {
  if (!E) return; const dd = prepararDados(E.dados);
  if (!dd.consumo) { E.res = null; desenharResumo(); atualizarInfos(); return; }
  $('#resumo')?.classList.add('carregando');
  try { E.res = await api('POST', '/api/calcular', { dados: dd }); } catch (e) { erro(e); }
  $('#resumo')?.classList.remove('carregando');
  if (!E.dados.n_manual && E.res) E.dados.n_paineis = E.res.n_paineis;
  if (!E.dados.inv_manual && E.res) { E.dados.inversor_id = E.res.inversor_id; E.dados.qtd_inversor = E.res.qtd_inversor; }
  if (!E.dados.valor_manual && E.res) E.dados.valor = E.res.valor;
  const ip = $('[data-k="n_paineis"]'); if (ip && !E.dados.n_manual) ip.value = E.dados.n_paineis;
  const ii = $('[data-k="inversor_id"]'); if (ii && !E.dados.inv_manual) ii.value = E.dados.inversor_id;
  const iv = $('[data-k="valor"]'); if (iv && !E.dados.valor_manual) iv.value = E.dados.valor;
  desenharResumo(); atualizarInfos();
}
function atualizarInfos() {
  const r = E?.res, c = S.cfg;
  const ci = $('#consumoInfo'); if (ci) ci.innerHTML = r ? `<div class="aviso ok"><i data-lucide="check-circle-2"></i><div>Consumo considerado: <b>${num(r.consumo)} kWh/mês</b> → sistema de <b>${r.kwp_txt} kWp</b> (${r.n_paineis} painéis de ${r.w_painel} W) gerando cerca de <b>${num(r.ger_media)} kWh/mês</b>.</div></div>` : '<div class="aviso"><i data-lucide="info"></i>Preencha o consumo para dimensionar o sistema.</div>';
  const pi = $('#precoInfo'); if (pi && r) {
    if (S.eu.papel === 'admin') pi.innerHTML = `<div class="rz" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))"><div><small>Solar (sugerido)</small><b>${rs(r.preco_solar, 0)}</b></div><div><small>Itens extras</small><b>${rs(r.preco_extras, 0)}</b></div><div><small>Preço sugerido</small><b>${rs(r.preco_sugerido, 0)}</b></div><div><small>Desconto</small><b style="color:${r.desconto_pct > 0 ? 'var(--amarelo)' : 'inherit'}">${brl(r.desconto_pct, 1)}%</b></div></div>`;
    else pi.innerHTML = `<div class="rz" style="grid-template-columns:1fr"><div><small>Valor do orçamento</small><b style="font-size:22px;color:var(--verde)">${rs(r.valor)}</b></div></div>${r.valor < r.preco_sugerido - .01 ? '<div class="aviso erro" style="margin-top:10px"><i data-lucide="alert-triangle"></i>O valor não pode ficar abaixo de ' + rs(r.preco_sugerido) + '.</div>' : ''}`;
  }
  const fi = $('#finInfo'); if (fi && r) {
    const fins = c.financeiras.filter(f => E.dados.financeiras_ids.includes(f.id));
    fi.innerHTML = fins.length ? `<div class="tbl-wrap"><table class="t"><thead><tr><th>Financeira</th><th>Prazo</th><th>Juros</th><th class="n">Parcela simulada</th></tr></thead><tbody>${fins.map(f => `<tr><td>${esc(f.nome)}</td><td>${f.prazo}×</td><td>${brl(f.taxa * 100, 2)}%</td><td class="n"><b>${rs(pmt(r.valor, f.taxa, f.prazo) * (S.cfg.fin_fator || 1))}</b></td></tr>`).join('')}</tbody></table></div><div class="aviso" style="margin-top:10px"><i data-lucide="info"></i>Apenas simulação: na aprovação a parcela pode subir conforme o score de crédito do cliente.</div>` : '<div class="aviso"><i data-lucide="info"></i>Marque pelo menos uma financeira.</div>';
  }
  icones();
}
function pmt(pv, i, n) { return i ? pv * i / (1 - Math.pow(1 + i, -n)) : pv / n; }
function desenharResumo() {
  const r = E?.res, el = $('#resumo'); if (!el) return;
  if (!r) { el.innerHTML = `<div class="card"><h3><i data-lucide="sparkles" style="color:var(--verde)"></i>Resumo ao vivo</h3><div class="vazio" style="padding:20px"><i data-lucide="gauge"></i><div>Informe o consumo do cliente e o sistema aparece aqui na hora.</div></div></div>`; icones(); return; }
  el.innerHTML = `<div class="card brilho"><h3><i data-lucide="sparkles" style="color:var(--verde)"></i>Resumo ao vivo</h3>
    <small class="mut">${r.opcoes.length > 1 ? 'Valores da proposta' : 'Investimento'}</small>
    ${r.opcoes.map((o, i) => `<div style="margin:4px 0 ${i === r.opcoes.length - 1 ? 12 : 4}px">${r.opcoes.length > 1 ? `<small class="mut">${esc(o.rotulo)}</small>` : ''}<div class="grande" style="${i ? 'font-size:22px;color:var(--texto)' : ''}">${rs(o.valor)}</div></div>`).join('')}
    ${r.parcela_min ? `<div class="pilula v" style="margin-bottom:14px">financiado a partir de ${rs(r.parcela_min)}/mês (simulação)</div>` : ''}
    <div class="rz">
      <div><small>Potência</small><b>${r.kwp_txt} kWp</b></div><div><small>Painéis</small><b>${r.n_paineis} × ${r.w_painel} W</b></div>
      <div><small>Inversor</small><b>${r.qtd_inversor > 1 ? r.qtd_inversor + ' × ' : ''}${esc(r.inversor)}</b></div><div><small>Geração</small><b>${num(r.ger_media)} kWh/mês</b></div>
      <div><small>Conta hoje</small><b>${rs(r.conta_sem, 0)}</b></div><div><small>Conta com solar</small><b class="verde">${rs(r.conta_com, 0)}</b></div>
      <div><small>Economia/mês</small><b class="verde">${rs(r.econ_mes, 0)}</b></div><div><small>Retorno (payback)</small><b>${r.payback_txt}</b></div>
      <div><small>Rentabilidade</small><b>${brl(r.tir_pct, 1)}% a.a.</b></div><div><small>Em 25 anos</small><b>${rsCurto(r.total25)}</b></div>
      <div><small>Área</small><b>≈ ${r.area_m2} m²</b></div><div><small>Ligação</small><b>${esc(r.ligacao)}</b></div>
    </div>
    ${r.doc_valido === false ? '<div class="aviso erro" style="margin-top:12px"><i data-lucide="alert-triangle"></i>O CPF/CNPJ não confere.</div>' : ''}
    </div>
    <div class="card" style="padding:14px"><div class="flex"><i data-lucide="keyboard" class="mut"></i><small class="mut">Dica: aperte <kbd>N</kbd> em qualquer tela para um orçamento novo.</small></div></div>`;
  icones();
}
async function previa() {
  const dd = prepararDados(E.dados); if (!dd.consumo) return toast('Informe o consumo primeiro', 'erro');
  const f = modal(`<h3><i data-lucide="eye"></i>Prévia da proposta<span class="esp" style="flex:1"></span><button class="bt fan" onclick="fecharModal()"><i data-lucide="x"></i></button></h3><iframe class="previa" id="ifPrevia"></iframe>`, 'g');
  try { const r = await api('POST', '/api/previa', { dados: dd, num: E.orc?.num }, true); $('#ifPrevia', f).srcdoc = await r.text(); } catch (e) { erro(e); }
}
async function salvar() {
  const dd = prepararDados(E.dados);
  if (!dd.cliente_nome) { irPasso(0); return toast('Falta o nome do cliente', 'erro'); }
  if (!dd.consumo) { irPasso(1); return toast('Falta o consumo', 'erro'); }
  const b = $('#btAvancar'); b.disabled = true;
  try {
    const o = E.id ? await api('PUT', '/api/orcamentos/' + E.id, { dados: dd }) : await api('POST', '/api/orcamentos', { dados: dd });
    toast(`<b>Orçamento ${o.num} salvo!</b>`); E.id = o.id; E.orc = o;
    if (location.hash !== '#/orcamento/' + o.id) history.replaceState(null, '', '#/orcamento/' + o.id);
    $('.topo h2').innerHTML = `<i data-lucide="file-pen" style="color:var(--verde)"></i>Orçamento ${o.num}`; icones();
    posSalvar(o);
  } catch (e) { erro(e); } finally { b.disabled = false; }
}
function acoesEnvio(o) {
  return `<div class="flex wrap" style="margin-top:6px">
    <button class="bt pri" data-acao="pdf" data-id="${o.id}"><i data-lucide="download"></i>Baixar PDF</button>
    <button class="bt wa" data-acao="wa" data-id="${o.id}"><i data-lucide="message-circle"></i>Enviar no WhatsApp</button>
    <button class="bt" data-acao="link" data-id="${o.id}"><i data-lucide="link"></i>Copiar link</button>
    <a class="bt" href="${o.link}" target="_blank"><i data-lucide="external-link"></i>Abrir como o cliente vê</a></div>
    <p class="mut" style="font-size:12.5px;margin-top:10px">Link do cliente: <a href="${o.link}" target="_blank">${o.link}</a> · aberto ${o.visualizacoes || 0}×</p>`;
}
function posSalvar(o) {
  const f = modal(`<div style="text-align:center"><div class="logo-q" style="margin-top:0"><i data-lucide="check"></i></div><h3 style="justify-content:center">Orçamento ${o.num} salvo</h3>
    <p class="mut">${esc(o.cliente_nome)} · ${rs(o.valor)}${o.valor_max > o.valor ? ' a ' + rs(o.valor_max) : ''}</p></div>${acoesEnvio(o)}
    <div class="acoes"><button class="bt" onclick="fecharModal()">Continuar editando</button><a class="bt" href="#/orcamentos" onclick="fecharModal()">Ver lista</a><a class="bt pri" href="#/novo" onclick="fecharModal()"><i data-lucide="plus"></i>Novo orçamento</a></div>`);
  $$('[data-acao]', f).forEach(ligarAcao);
  if (E && E.passo === PASSOS.length - 1) desenharPasso();
}
function ligarAcao(el) {
  el.onclick = async ev => {
    ev.stopPropagation(); $('.menu-acoes')?.remove();
    const id = +el.dataset.id, a = el.dataset.acao;
    let o = (E && E.orc && E.orc.id === id) ? E.orc : (S.cacheLista || []).find(x => x.id === id);
    if (!o) o = await api('GET', '/api/orcamentos/' + id);
    if (a === 'pdf') return baixar('/api/orcamentos/' + id + '/pdf');
    if (a === 'link') return copiar(o.link);
    if (a === 'wa') { const nome = (o.cliente_nome || '').split(' ')[0]; const msg = `Olá${nome ? ' ' + nome : ''}! Aqui é ${S.eu.nome.split(' ')[0]} da MS Energy. Segue a sua proposta de energia solar (${o.num}):\n${o.link}\n\nQualquer dúvida estou à disposição!`; window.open(waLink(o.cliente_tel, msg), '_blank'); if (o.status === 'rascunho') api('PUT', `/api/orcamentos/${id}/status`, { status: 'enviado' }).catch(() => { }); return; }
    if (a === 'editar') { location.hash = '#/orcamento/' + id; return; }
    if (a === 'detalhe') return abrirDetalhe(id);
    if (a === 'duplicar') { try { const n = await api('POST', `/api/orcamentos/${id}/duplicar`); toast('Cópia criada: ' + n.num); location.hash = '#/orcamento/' + n.id; } catch (e) { erro(e); } return; }
    if (a === 'apagar') { if (!confirm(`Apagar o orçamento ${o.num} de ${o.cliente_nome}?`)) return; try { await api('DELETE', '/api/orcamentos/' + id); toast('Orçamento apagado'); render(); } catch (e) { erro(e); } return; }
    if (a.startsWith('st:')) { const st = a.slice(3); let motivo = ''; if (st === 'perdido') { motivo = prompt('Por que perdeu? (preço, concorrente, desistiu, crédito negado…)') || ''; } try { await api('PUT', `/api/orcamentos/${id}/status`, { status: st, motivo }); toast('Status: ' + ROT_ST[st]); if (location.hash.startsWith('#/orcamentos')) telaLista($('#conteudo')); } catch (e) { erro(e); } }
  };
}

// ------------------------------------------------------------------ lista
async function telaLista(alvo) {
  const f = S.filtros; const qs = new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString();
  const lista = await api('GET', '/api/orcamentos?' + qs); S.cacheLista = lista; const adm = S.eu.papel === 'admin';
  const contagem = {}; lista.forEach(o => contagem[o.status] = (contagem[o.status] || 0) + 1);
  const { col, dir } = S.ordem;
  const ord = [...lista].sort((a, b) => { const x = a[col], y = b[col]; return (typeof x === 'number' ? x - y : String(x || '').localeCompare(String(y || ''), 'pt')) * dir; });
  const th = (c, t, n) => `<th class="ord ${n ? 'n' : ''}" data-col="${c}">${t}${col === c ? (dir > 0 ? ' ↑' : ' ↓') : ''}</th>`;
  const soma = lista.reduce((a, o) => a + (o.valor || 0), 0);
  alvo.innerHTML = topo('Orçamentos', 'file-text', `<a class="bt" href="/api/exportar.csv"><i data-lucide="sheet"></i><span class="esconde-mob">Exportar planilha</span></a><a class="bt pri" href="#/novo"><i data-lucide="plus"></i>Novo</a>`) + `
  <div class="card" style="margin-bottom:14px"><div class="linha" style="grid-template-columns:2fr repeat(auto-fit,minmax(150px,1fr))">
    <div class="inp-pre"><span><i data-lucide="search" style="width:15px;height:15px"></i></span><input class="inp" id="fQ" placeholder="Buscar por cliente, número, CPF, telefone, cidade…" value="${esc(f.q)}"></div>
    ${adm ? `<select class="inp" id="fVend"><option value="">Todos os vendedores</option>${S.vendedores.map(v => `<option value="${v.id}" ${String(v.id) === String(f.vendedor) ? 'selected' : ''}>${esc(v.nome)}</option>`).join('')}</select>` : ''}
    <select class="inp" id="fTipo"><option value="">Todos os tipos</option>${Object.entries(TIPOS).map(([k, t]) => `<option value="${k}" ${f.tipo === k ? 'selected' : ''}>${t}</option>`).join('')}</select>
    <input class="inp" type="date" id="fDe" value="${f.de}" title="De"><input class="inp" type="date" id="fAte" value="${f.ate}" title="Até">
  </div><div class="chips" style="margin-top:12px"><span class="chip ${!f.status ? 'on' : ''}" data-st="">Todos <small>${lista.length}</small></span>${S.status.map(s => `<span class="chip ${f.status === s ? 'on' : ''}" data-st="${s}">${ROT_ST[s]} ${f.status ? '' : `<small>${contagem[s] || 0}</small>`}</span>`).join('')}<span class="esp"></span><span class="pilula">${lista.length} orçamento(s) · ${rsCurto(soma)}</span></div></div>
  ${lista.length ? `<div class="tbl-wrap card" style="padding:0"><table class="t"><thead><tr>${th('num', 'Número')}${th('cliente_nome', 'Cliente')}${adm ? th('vendedor_nome', 'Vendedor') : ''}${th('consumo', 'Consumo', 1)}${th('kwp', 'kWp', 1)}${th('valor', 'Valor', 1)}${th('status', 'Status')}${th('visualizacoes', 'Vistas', 1)}${th('criado', 'Criado')}<th></th></tr></thead><tbody>
  ${ord.map(o => `<tr><td class="clic" data-abrir="${o.id}"><b>${o.num}</b><br><small class="mut">${TIPOS[o.tipo] || ''}</small></td><td class="clic" data-abrir="${o.id}"><b>${esc(o.cliente_nome || '—')}</b><br><small class="mut">${esc(o.cliente_cidade || o.cliente_tel || '')}</small></td>
    ${adm ? `<td><div class="flex"><div class="ava" style="width:26px;height:26px;font-size:11px;background:${corDe(o.vendedor_id)}">${iniciais(o.vendedor_nome)}</div>${esc(o.vendedor_nome)}</div></td>` : ''}
    <td class="n">${num(o.consumo)} kWh</td><td class="n">${brl(o.kwp, 2)}</td><td class="n"><b>${rs(o.valor, 0)}</b>${o.valor_max > o.valor ? `<br><small class="mut">até ${rs(o.valor_max, 0)}</small>` : ''}</td>
    <td><span class="st ${o.status}">${ROT_ST[o.status]}</span>${o.proximo_contato ? `<br><small class="mut">📅 ${dataBR(o.proximo_contato)}</small>` : ''}</td><td class="n">${o.visualizacoes ? `<span class="pilula" style="color:var(--azul)">👁 ${o.visualizacoes}</span>` : '<span class="mut">—</span>'}</td>
    <td><small>${dataBR(o.criado)}</small></td><td><div class="flex"><button class="bt peq wa" data-acao="wa" data-id="${o.id}" title="Enviar no WhatsApp"><i data-lucide="message-circle"></i></button><button class="bt peq" data-acao="pdf" data-id="${o.id}" title="PDF"><i data-lucide="download"></i></button><button class="bt peq fan" data-menu="${o.id}"><i data-lucide="more-vertical"></i></button></div></td></tr>`).join('')}
  </tbody></table></div>` : `<div class="card vazio"><i data-lucide="search-x"></i><div>Nenhum orçamento encontrado.</div></div>`}`;
  icones();
  const rel = deb(() => telaLista(alvo), 350);
  $('#fQ').oninput = e => { f.q = e.target.value; rel(); };
  if (f.q) { $('#fQ').focus(); $('#fQ').setSelectionRange(f.q.length, f.q.length); }
  $('#fVend') && ($('#fVend').onchange = e => { f.vendedor = e.target.value; telaLista(alvo); });
  $('#fTipo').onchange = e => { f.tipo = e.target.value; telaLista(alvo); };
  $('#fDe').onchange = e => { f.de = e.target.value; telaLista(alvo); }; $('#fAte').onchange = e => { f.ate = e.target.value; telaLista(alvo); };
  $$('[data-st]').forEach(el => el.onclick = () => { f.status = el.dataset.st; telaLista(alvo); });
  $$('th[data-col]').forEach(el => el.onclick = () => { const c = el.dataset.col; S.ordem = { col: c, dir: S.ordem.col === c ? -S.ordem.dir : -1 }; telaLista(alvo); });
  $$('[data-abrir]').forEach(el => el.onclick = () => abrirDetalhe(+el.dataset.abrir));
  $$('[data-acao]').forEach(ligarAcao);
  $$('[data-menu]').forEach(el => el.onclick = e => { e.stopPropagation(); menuAcoes(el, +el.dataset.menu); });
}
function menuAcoes(ancora, id) {
  $('.menu-acoes')?.remove(); const r = ancora.getBoundingClientRect(); const m = document.createElement('div'); m.className = 'menu-acoes';
  m.innerHTML = [['detalhe', 'panel-right-open', 'Detalhes e histórico'], ['editar', 'pencil', 'Editar'], ['link', 'link', 'Copiar link do cliente'], ['duplicar', 'copy', 'Duplicar'], ...S.status.map(s => ['st:' + s, 'circle-dot', 'Marcar ' + ROT_ST[s].toLowerCase()]), ['apagar', 'trash-2', 'Apagar']]
    .map(([a, ic, t]) => `<button data-acao="${a}" data-id="${id}" ${a === 'apagar' ? 'style="color:#f87171"' : ''}><i data-lucide="${ic}"></i>${t}</button>`).join('');
  document.body.appendChild(m); m.style.top = Math.min(window.scrollY + r.bottom + 4, window.scrollY + innerHeight - m.offsetHeight - 10) + 'px'; m.style.left = Math.max(8, r.right - 220) + 'px';
  icones(); $$('[data-acao]', m).forEach(ligarAcao);
}
async function abrirDetalhe(id) {
  const o = await api('GET', '/api/orcamentos/' + id); const r = o.resumo || {};
  const g = gaveta(`<div class="flex"><h3 style="margin:0;font-size:19px">${o.num}</h3><span class="st ${o.status}">${ROT_ST[o.status]}</span><span class="esp"></span><button class="bt fan" onclick="fecharGaveta()"><i data-lucide="x"></i></button></div>
    <p class="mut" style="margin:6px 0 16px">${esc(o.cliente_nome)} · ${esc(o.cliente_tel || '')} · ${esc(o.vendedor_nome)}</p>
    <div class="rz"><div><small>Valor</small><b>${rs(o.valor)}</b></div><div><small>Sistema</small><b>${r.kwp_txt || ''} kWp · ${r.n_paineis || ''} painéis</b></div><div><small>Economia/mês</small><b class="verde">${rs(r.econ_mes || 0, 0)}</b></div><div><small>Payback</small><b>${r.payback_txt || ''}</b></div><div><small>Visualizações</small><b>${o.visualizacoes || 0}</b></div><div><small>Última vez</small><b>${dataBR(o.ultima_visualizacao) || '—'}</b></div></div>
    ${acoesEnvio(o)}
    <div class="flex wrap" style="margin-top:12px"><a class="bt" href="#/orcamento/${o.id}"><i data-lucide="pencil"></i>Editar</a><button class="bt" data-acao="duplicar" data-id="${o.id}"><i data-lucide="copy"></i>Duplicar</button>
    <select class="inp" id="gSt" style="width:auto">${S.status.map(s => `<option value="${s}" ${s === o.status ? 'selected' : ''}>${ROT_ST[s]}</option>`).join('')}</select></div>
    <div class="sep"></div><h3 style="font-size:15px">Anotação / próximo contato</h3>
    <textarea class="inp" id="gNota" placeholder="Ex.: Cliente pediu para ligar depois do dia 10; quer ver com a esposa."></textarea>
    <div class="flex" style="margin-top:8px"><input class="inp" type="date" id="gData" value="${o.proximo_contato || ''}" style="width:auto"><span class="esp"></span><button class="bt pri" id="gSalvar"><i data-lucide="save"></i>Salvar anotação</button></div>
    <div class="sep"></div><h3 style="font-size:15px">Histórico</h3><div class="linha-tempo">${o.eventos.map(e => `<div class="ev ${e.tipo}"><b>${esc(e.texto || e.tipo)}</b><br><small>${esc(e.quem)} · ${dataBR(e.quando)}</small></div>`).join('')}</div>`);
  $$('[data-acao]', g).forEach(ligarAcao);
  $('#gSt', g).onchange = async e => { let motivo = ''; if (e.target.value === 'perdido') motivo = prompt('Por que perdeu?') || ''; await api('PUT', `/api/orcamentos/${id}/status`, { status: e.target.value, motivo }).catch(erro); toast('Status atualizado'); abrirDetalhe(id); if (location.hash.startsWith('#/orcamentos')) telaLista($('#conteudo')); };
  $('#gSalvar', g).onclick = async () => { const t = $('#gNota').value.trim(); await api('POST', `/api/orcamentos/${id}/nota`, { texto: t || 'Retorno marcado', proximo_contato: $('#gData').value }).catch(erro); toast('Anotação salva'); abrirDetalhe(id); };
}

// ------------------------------------------------------------------ clientes
async function telaClientes(alvo) {
  const l = await api('GET', '/api/clientes'); let q = '';
  const desenhar = () => {
    const f = l.filter(c => !q || [c.nome, c.doc, c.tel, c.cidade].join(' ').toLowerCase().includes(q.toLowerCase()));
    $('#tbCli').innerHTML = f.map(c => `<tr><td><div class="flex"><div class="ava" style="background:${corDe(c.nome.length)}">${iniciais(c.nome)}</div><div><b>${esc(c.nome)}</b><br><small class="mut">${esc(c.doc || '')}</small></div></div></td><td>${esc(c.tel || '')}</td><td>${esc(c.cidade || '')}</td><td class="n">${c.n}</td><td class="n">${rs(c.maior, 0)}</td><td>${c.fechado ? '<span class="st fechado">Cliente</span>' : '<span class="st negociando">Em aberto</span>'}</td><td><small>${dataBR(c.ultimo)}</small></td>
      <td><div class="flex">${c.tel ? `<a class="bt peq wa" target="_blank" href="${waLink(c.tel, 'Olá ' + c.nome.split(' ')[0] + '! Aqui é da MS Energy.')}"><i data-lucide="message-circle"></i></a>` : ''}<button class="bt peq" data-busca="${esc(c.nome)}"><i data-lucide="file-search"></i></button></div></td></tr>`).join('') || '<tr><td colspan="8" class="vazio">Nenhum cliente.</td></tr>';
    icones(); $$('[data-busca]').forEach(b => b.onclick = () => { S.filtros = { status: '', q: b.dataset.busca, vendedor: '', tipo: '', de: '', ate: '' }; location.hash = '#/orcamentos'; });
  };
  alvo.innerHTML = topo('Clientes', 'users', `<span class="pilula">${l.length} cliente(s)</span>`) + `<div class="card" style="margin-bottom:14px"><div class="inp-pre"><span><i data-lucide="search" style="width:15px;height:15px"></i></span><input class="inp" id="qCli" placeholder="Buscar cliente…"></div></div>
   <div class="tbl-wrap card" style="padding:0"><table class="t"><thead><tr><th>Cliente</th><th>WhatsApp</th><th>Cidade</th><th class="n">Orçamentos</th><th class="n">Maior valor</th><th>Situação</th><th>Último</th><th></th></tr></thead><tbody id="tbCli"></tbody></table></div>`;
  icones(); desenhar(); $('#qCli').oninput = e => { q = e.target.value; desenhar(); };
}

// ------------------------------------------------------------------ simulador rápido
async function telaSimulador(alvo) {
  const st = { modo: 'kwh', consumo: 500, conta: 600, tipo: 'ongrid' };
  alvo.innerHTML = topo('Simulador rápido', 'calculator') + `<div class="grade g12"><div class="card brilho"><h3><i data-lucide="zap" style="color:var(--verde)"></i>Simule em segundos</h3>
    <p class="mut" style="margin-top:-6px">Para responder rápido no WhatsApp. Nada é salvo até você criar o orçamento.</p>
    <div class="chips" style="margin-bottom:14px"><span class="chip on" data-m="kwh">Por kWh</span><span class="chip" data-m="conta">Pelo valor da conta</span></div>
    <div class="campo" id="sCampo"></div>
    <div class="chips" style="margin:14px 0">${Object.entries(TIPOS).map(([k, t]) => `<span class="chip ${k === 'ongrid' ? 'on' : ''}" data-t="${k}">${t}</span>`).join('')}</div>
    <button class="bt pri" id="sCriar" style="width:100%"><i data-lucide="file-plus"></i>Criar orçamento com isso</button>
    <button class="bt" id="sCopiar" style="width:100%;margin-top:8px"><i data-lucide="copy"></i>Copiar resumo para o WhatsApp</button></div>
    <div class="card" id="sRes"><div class="vazio">Calculando…</div></div></div>`;
  icones();
  const campoH = () => { $('#sCampo').innerHTML = st.modo === 'kwh' ? `<label>Consumo médio por mês</label><div class="inp-suf"><input class="inp" id="sV" type="number" value="${st.consumo}" style="font-size:22px;font-weight:800"><span>kWh</span></div><input type="range" id="sR" min="100" max="5000" step="50" value="${st.consumo}" style="width:100%;accent-color:#22c55e;margin-top:10px">`
    : `<label>Valor médio da conta de luz</label><div class="inp-pre"><span>R$</span><input class="inp" id="sV" type="number" value="${st.conta}" style="font-size:22px;font-weight:800"></div><input type="range" id="sR" min="100" max="6000" step="50" value="${st.conta}" style="width:100%;accent-color:#22c55e;margin-top:10px">`;
    const up = v => { if (st.modo === 'kwh') st.consumo = +v; else st.conta = +v; $('#sV').value = v; $('#sR').value = v; calc(); };
    $('#sV').oninput = e => up(e.target.value); $('#sR').oninput = e => up(e.target.value); };
  let ult = null;
  const calc = deb(async () => {
    const d = { consumo: st.modo === 'kwh' ? st.consumo : Math.round(st.conta / S.cfg.calculo.tarifa), tipo: st.tipo };
    try { ult = await api('POST', '/api/calcular', { dados: d }); } catch (e) { return erro(e); }
    const r = ult; const fins = S.cfg.financeiras.filter(f => f.ativo);
    $('#sRes').innerHTML = `<h3><i data-lucide="sparkles" style="color:var(--verde)"></i>Resultado</h3>
     <div class="grade g3"><div><small class="mut">Investimento</small><div class="grande" style="font-size:30px;font-weight:800;color:var(--verde)">${rs(r.valor, 0)}</div></div><div><small class="mut">Economia por mês</small><div style="font-size:26px;font-weight:800">${rs(r.econ_mes, 0)}</div></div><div><small class="mut">Se paga em</small><div style="font-size:22px;font-weight:800">${r.payback_txt}</div></div></div>
     <div class="rz" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin-top:16px"><div><small>Sistema</small><b>${r.kwp_txt} kWp</b></div><div><small>Painéis</small><b>${r.n_paineis} × ${r.w_painel} W</b></div><div><small>Inversor</small><b>${esc(r.inversor)}</b></div><div><small>Geração</small><b>${num(r.ger_media)} kWh/mês</b></div><div><small>Conta hoje → depois</small><b>${rs(r.conta_sem, 0)} → <span class="verde">${rs(r.conta_com, 0)}</span></b></div><div><small>Em 25 anos</small><b>${rsCurto(r.total25)}</b></div></div>
     <h3 style="margin-top:18px;font-size:14px">Parcelas simuladas</h3><div class="tbl-wrap"><table class="t"><tbody>${fins.map(f => `<tr><td>${esc(f.nome.split(' –')[0])}</td><td>${f.prazo}×</td><td class="n"><b>${rs(pmt(r.valor, f.taxa, f.prazo) * (S.cfg.fin_fator || 1))}</b></td></tr>`).join('')}
     ${S.cfg.pagamento.direto.ativo ? `<tr><td>Direto MS Energy (1ª parte)</td><td>${S.cfg.pagamento.direto.n1}×</td><td class="n"><b>${rs(r.valor * S.cfg.pagamento.direto.pct1 / 100 / S.cfg.pagamento.direto.n1)}</b></td></tr>` : ''}</tbody></table></div>
     <div class="aviso" style="margin-top:10px"><i data-lucide="info"></i>Apenas simulação: na aprovação a parcela pode subir conforme o score de crédito.</div>`;
    icones();
  }, 220);
  $$('[data-m]').forEach(el => el.onclick = () => { st.modo = el.dataset.m; $$('[data-m]').forEach(x => x.classList.toggle('on', x === el)); campoH(); calc(); });
  $$('[data-t]').forEach(el => el.onclick = () => { st.tipo = el.dataset.t; $$('[data-t]').forEach(x => x.classList.toggle('on', x === el)); calc(); });
  $('#sCriar').onclick = () => { sessionStorage.setItem('orc_sim', JSON.stringify({ modo_consumo: st.modo === 'kwh' ? 'kwh' : 'conta', consumo: st.consumo, conta_rs: st.conta, tipo: st.tipo })); location.hash = '#/novo'; };
  $('#sCopiar').onclick = () => { if (!ult) return; const r = ult; copiar(`☀️ *Simulação MS Energy*\nConsumo: ${num(r.consumo)} kWh/mês\nSistema: ${r.kwp_txt} kWp (${r.n_paineis} painéis de ${r.w_painel} W)\nInvestimento: ${rs(r.valor, 0)}\nEconomia: cerca de ${rs(r.econ_mes, 0)} por mês\nSe paga em ${r.payback_txt}\n${r.parcela_min ? 'Financiado a partir de ' + rs(r.parcela_min) + '/mês (simulação)*\n' : ''}\n*valores apenas simulados; podem mudar após visita técnica e análise de crédito`); };
  campoH(); calc();
}

// ------------------------------------------------------------------ catálogo e preços (admin)
async function telaCatalogo(alvo) {
  const c = clone(S.cfg);
  const tabela = (lista, cols, titulo, ic, novo) => `<div class="card" style="margin-top:14px"><h3><i data-lucide="${ic}" style="color:var(--verde)"></i>${titulo}<span class="esp"></span><button class="bt peq" data-add="${lista}"><i data-lucide="plus"></i>Adicionar</button></h3>
    <div class="tbl-wrap"><table class="t ed-tab"><thead><tr>${cols.map(([, t]) => `<th>${t}</th>`).join('')}<th></th></tr></thead><tbody>
    ${c[lista].map((row, i) => `<tr>${cols.map(([k, , tipo, w]) => `<td style="min-width:${w || 90}px">${tipo === 'bool' ? `<label class="chave"><input type="checkbox" data-cat="${lista}.${i}.${k}" ${row[k] ? 'checked' : ''}><i></i></label>` : tipo === 'sel' ? `<select class="inp" data-cat="${lista}.${i}.${k}">${['ongrid', 'hibrido', 'micro'].map(o => `<option ${row[k] === o ? 'selected' : ''}>${o}</option>`).join('')}</select>` : `<input class="inp" data-cat="${lista}.${i}.${k}" data-tipo="${tipo || 'txt'}" value="${esc(row[k] ?? '')}">`}</td>`).join('')}<td><button class="bt fan peq" data-rm="${lista}.${i}"><i data-lucide="trash-2"></i></button></td></tr>`).join('')}
    </tbody></table></div></div>`;
  const num2 = (k, t, suf, pre, dica) => `<div class="campo"><label>${t}</label><div class="${pre ? 'inp-pre' : 'inp-suf'}">${pre ? `<span>${pre}</span>` : ''}<input class="inp" type="number" step="any" data-cfg="${k}" value="${getP(c, k)}">${suf ? `<span>${suf}</span>` : ''}</div>${dica ? `<span class="dica">${dica}</span>` : ''}</div>`;
  alvo.innerHTML = topo('Catálogo e preços', 'package', `<button class="bt" id="btRest"><i data-lucide="rotate-ccw"></i><span class="esconde-mob">Restaurar padrão</span></button><button class="bt pri" id="btSalvarCat"><i data-lucide="save"></i>Salvar tudo</button>`) + `
   <div class="card brilho"><h3><i data-lucide="badge-dollar-sign" style="color:var(--verde)"></i>Regra de preço do sistema solar</h3>
     <p class="mut" style="margin-top:-6px">Preço sugerido = <b>fixo + (R$ por kWp × kWp)</b> + adicionais. Hoje: 3,75 kWp = <b>${rs(c.preco.fixo + c.preco.por_kwp * 3.75, 0)}</b> · 7,5 kWp = <b>${rs(c.preco.fixo + c.preco.por_kwp * 7.5, 0)}</b>.</p>
     <div class="linha">${num2('preco.fixo', 'Valor fixo', '', 'R$')}${num2('preco.por_kwp', 'Por kWp', '', 'R$')}${num2('preco.adicional_hibrido', 'Adicional híbrido', '', 'R$')}${num2('preco.adicional_micro', 'Adicional microinversor', '', 'R$')}${num2('preco.adicional_solo_por_kwp', 'Adicional solo (por kWp)', '', 'R$')}${num2('preco.arredondar', 'Arredondar para cima', '', 'R$', 'Ex.: 100')}</div><p class="mut" style="margin:10px 0 0">Vendedor não pode baixar preço: só aumentar o valor ou acrescentar itens. O acréscimo oculto de cada vendedor fica em <b>Vendedores</b>.</p></div>
   <div class="card" style="margin-top:14px"><h3><i data-lucide="sliders-horizontal" style="color:var(--verde)"></i>Premissas do cálculo</h3>
     <div class="linha">${num2('calculo.tarifa', 'Preço do kWh padrão', '', 'R$')}${num2('calculo.kwh_por_kwp_mes', 'Geração por kWp ao mês', 'kWh', '', '133,33 = 7,5 kWp gera 1.000 kWh')}${num2('calculo.reajuste_tarifa', 'Reajuste da tarifa ao ano', '', '', '0.04 = 4%')}${num2('calculo.poupanca', 'Rendimento da poupança ao ano', '', '', '0.0617 = 6,17%')}${num2('calculo.minimo_mono', 'Mínimo monofásico', 'kWh')}${num2('calculo.minimo_bi', 'Mínimo bifásico', 'kWh')}${num2('calculo.minimo_tri', 'Mínimo trifásico', 'kWh')}</div></div>
   <div class="card" style="margin-top:14px"><h3><i data-lucide="credit-card" style="color:var(--verde)"></i>Pagamento padrão dos novos orçamentos</h3>
     <div class="linha">${num2('pagamento.avista.desconto_pct', 'Desconto à vista', '%')}${num2('pagamento.direto.pct1', 'Direto: 1ª parte', '%')}${num2('pagamento.direto.n1', 'Direto: 1ª parte em', 'x')}${num2('pagamento.direto.boleto_n', 'Direto: 2ª no boleto', 'x')}${num2('pagamento.direto.cartao_n', 'Direto: 2ª no cartão', 'x')}${num2('pagamento.cartao.n', 'Cartão: parcelas', 'x')}${num2('pagamento.entrada.pct', 'Entrada', '%')}${num2('pagamento.financiamento.margem_pct', 'Margem de segurança nas parcelas', '%', '', 'Soma em toda parcela simulada (padrão 10%)')}</div>
     <div class="flex wrap" style="margin-top:12px">${[['avista', 'À vista'], ['direto', 'Parcelamento direto'], ['cartao', 'Cartão'], ['entrada', 'Entrada + financiamento'], ['financiamento', 'Financiamento']].map(([k, t]) => `<label class="chip"><input type="checkbox" data-cfgb="pagamento.${k}.ativo" ${c.pagamento[k].ativo ? 'checked' : ''}> ${t}</label>`).join('')}</div></div>
   ${tabela('financeiras', [['nome', 'Financeira', 'txt', 220], ['prazo', 'Prazo (x)', 'int', 80], ['taxa', 'Taxa a.m. (0.0215)', 'num', 110], ['carencia', 'Carência', 'int', 80], ['obs', 'Observação', 'txt', 220], ['ativo', 'Padrão', 'bool', 60]], 'Financeiras', 'landmark')}
   ${tabela('extras', [['nome', 'Item', 'txt', 260], ['desc', 'Descrição', 'txt', 220], ['preco', 'Preço (R$)', 'num', 100], ['unid', 'Unid.', 'txt', 60], ['icone', 'Ícone (ar/poste/carro/limpeza/monitor/protecao)', 'txt', 110]], 'Itens extras', 'package-plus')}
   ${tabela('baterias', [['nome', 'Bateria', 'txt', 260], ['desc', 'Descrição', 'txt', 260], ['preco', 'Preço (R$)', 'num', 100]], 'Baterias', 'battery-charging')}
   ${tabela('inversores', [['nome', 'Nome na proposta', 'txt', 260], ['curto', 'Nome curto', 'txt', 140], ['kw', 'kW', 'num', 60], ['tipo', 'Tipo', 'sel', 100], ['marca', 'Marca', 'txt', 80], ['desc', 'Descrição', 'txt', 220], ['garantia', 'Garantia', 'txt', 200]], 'Inversores', 'cpu')}
   ${tabela('paineis', [['nome', 'Painel', 'txt', 300], ['w', 'Watts', 'int', 70], ['desc', 'Descrição', 'txt', 260]], 'Painéis', 'panels-top-left')}
   ${tabela('estruturas', [['nome', 'Estrutura', 'txt', 300], ['desc', 'Descrição', 'txt', 300]], 'Estruturas', 'home')}`;
  icones();
  const ler = el => { const t = el.dataset.tipo; return el.type === 'checkbox' ? el.checked : t === 'num' ? parseFloat(String(el.value).replace(',', '.')) || 0 : t === 'int' ? parseInt(el.value) || 0 : el.value; };
  $$('[data-cfg]').forEach(el => el.oninput = () => setP(c, el.dataset.cfg, parseFloat(String(el.value).replace(',', '.')) || 0));
  $$('[data-cfgb]').forEach(el => el.onchange = () => setP(c, el.dataset.cfgb, el.checked));
  $$('[data-cat]').forEach(el => el.addEventListener(el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'input', () => setP(c, el.dataset.cat, ler(el))));
  $$('[data-rm]').forEach(el => el.onclick = () => { const [l, i] = el.dataset.rm.split('.'); if (!confirm('Remover este item do catálogo?')) return; c[l].splice(+i, 1); S.cfg = c; telaCatalogo(alvo); });
  $$('[data-add]').forEach(el => el.onclick = () => { const l = el.dataset.add; const base = { id: l.slice(0, 3) + Date.now().toString(36) }; const mod = { financeiras: { nome: 'Nova financeira', prazo: 60, taxa: 0.02, carencia: 3, obs: '', ativo: false }, extras: { nome: 'NOVO ITEM', desc: '', preco: 0, unid: 'PC', icone: 'protecao' }, baterias: { nome: 'NOVA BATERIA', desc: '', preco: 0 }, inversores: { nome: 'NOVO INVERSOR', curto: 'Novo', kw: 5, tipo: 'ongrid', marca: '', desc: '', garantia: '' }, paineis: { nome: 'NOVO PAINEL', w: 600, desc: '' }, estruturas: { nome: 'NOVA ESTRUTURA', desc: '', img: 'prod_estrutura.jpg' } }[l]; c[l].push({ ...base, ...mod }); S.cfg = c; telaCatalogo(alvo); });
  $('#btSalvarCat').onclick = async () => { try { const r = await api('PUT', '/api/config', { cfg: c }); S.cfg = r.cfg; toast('Catálogo e preços salvos'); telaCatalogo(alvo); } catch (e) { erro(e); } };
  $('#btRest').onclick = async () => { if (!confirm('Voltar todos os preços e o catálogo para o padrão?')) return; const r = await api('POST', '/api/config/restaurar'); S.cfg = r.cfg; toast('Padrão restaurado'); telaCatalogo(alvo); };
}

// ------------------------------------------------------------------ empresa (admin)
async function telaEmpresa(alvo) {
  const c = clone(S.cfg); const e = c.empresa;
  const f = (k, t, span) => `<div class="campo" ${span ? 'style="grid-column:1/-1"' : ''}><label>${t}</label><input class="inp" data-emp="${k}" value="${esc(e[k] ?? '')}"></div>`;
  alvo.innerHTML = topo('Dados da empresa', 'building-2', `<button class="bt pri" id="btEmp"><i data-lucide="save"></i>Salvar</button>`) + `
   <div class="card brilho"><h3><i data-lucide="building-2" style="color:var(--verde)"></i>Aparece em todas as propostas</h3><div class="linha">
   ${f('nome', 'Nome da empresa')}${f('cnpj', 'CNPJ')}${f('telefone', 'Telefone / WhatsApp')}${f('email', 'E-mail')}${f('endereco', 'Endereço', 1)}${f('sede', 'Linha da sede (rodapé)', 1)}${f('responsavel', 'Quem assina pela empresa')}${f('validade_dias', 'Validade padrão (dias)')}${f('garantia_instalacao', 'Garantia da instalação')}${f('prazo_entrega', 'Prazo de entrega', 1)}
   </div></div>`;
  icones();
  $$('[data-emp]').forEach(el => el.oninput = () => { e[el.dataset.emp] = el.dataset.emp === 'validade_dias' ? (parseInt(el.value) || 10) : el.value; });
  $('#btEmp').onclick = async () => { try { const r = await api('PUT', '/api/config', { cfg: c }); S.cfg = r.cfg; toast('Dados da empresa salvos'); } catch (er) { erro(er); } };
}

// ------------------------------------------------------------------ vendedores (admin)
async function telaVendedores(alvo) {
  S.vendedores = await api('GET', '/api/vendedores');
  alvo.innerHTML = topo('Vendedores', 'user-cog', `<button class="bt pri" id="btNovoV"><i data-lucide="user-plus"></i>Novo vendedor</button>`) + `
   <div class="grade g3">${S.vendedores.map(v => { const m = v.mes || {}; const pc = v.meta ? (m.fechado || 0) / v.meta * 100 : 0; return `<div class="card vend-card" style="${v.ativo ? '' : 'opacity:.5'}">
     <div class="topo-v"><div class="ava" style="width:46px;height:46px;font-size:16px;background:${corDe(v.id, v.cor)}">${iniciais(v.nome)}</div><div class="esp"><b style="font-size:16px">${esc(v.nome)}</b><br><small class="mut">@${esc(v.usuario)} · ${v.papel === 'admin' ? 'Administrador' : 'Vendedor'}${v.ativo ? '' : ' · desativado'}${v.papel !== 'admin' ? ' · <b style="color:var(--amarelo)">+' + num(v.acrescimo_pct || 0, 1) + '% material · +' + num(v.acrescimo_ar_pct ?? 10, 1) + '% ar (oculto)</b>' : ''}</small></div></div>
     <div class="rz"><div><small>Orçamentos no mês</small><b>${m.n || 0}</b></div><div><small>Valor orçado</small><b>${rsCurto(m.total || 0)}</b></div><div><small>Fechado no mês</small><b class="verde">${rsCurto(m.fechado || 0)}</b></div><div><small>Comissão (${num(v.comissao_pct, 1)}%)</small><b>${rs((m.fechado || 0) * (v.comissao_pct || 0) / 100, 0)}</b></div></div>
     ${v.meta ? `<div><small class="mut">Meta ${rs(v.meta, 0)}</small><div class="barra-h" style="margin-top:6px"><i style="width:${Math.min(pc, 100)}%"></i></div></div>` : ''}
     <small class="mut">📱 ${esc(v.telefone || 'sem telefone')} · último acesso ${dataBR(v.ultimo_login) || 'nunca'}</small>
     <div class="flex wrap"><button class="bt peq" data-ed="${v.id}"><i data-lucide="pencil"></i>Editar</button><button class="bt peq" data-senha="<SEGREDO_REMOVIDO>"><i data-lucide="key-round"></i>Nova senha</button>${v.id !== S.eu.id ? `<button class="bt peq ${v.ativo ? 'perigo' : ''}" data-ativo="${v.id}">${v.ativo ? 'Desativar' : 'Reativar'}</button>` : ''}</div></div>`; }).join('')}</div>`;
  icones();
  $('#btNovoV').onclick = () => formVendedor();
  $$('[data-ed]').forEach(b => b.onclick = () => formVendedor(S.vendedores.find(v => v.id === +b.dataset.ed)));
  $$('[data-senha]').forEach(b => b.onclick = async () => { if (!confirm('Gerar uma senha nova? A antiga para de funcionar.')) return; const r = await api('PUT', '/api/vendedores/' + b.dataset.senha, { nova_senha: true }).catch(erro); if (r) modal(`<h3><i data-lucide="key-round"></i>Senha nova</h3><p>Passe esta senha ao vendedor:</p><div class="card" style="font-size:24px;font-weight:800;text-align:center;letter-spacing:.05em">${esc(r.senha)}</div><div class="acoes"><button class="bt" onclick="navigator.clipboard.writeText('${esc(r.senha)}');toast('Copiada')">Copiar</button><button class="bt pri" onclick="fecharModal()">Pronto</button></div>`); });
  $$('[data-ativo]').forEach(b => b.onclick = async () => { const v = S.vendedores.find(x => x.id === +b.dataset.ativo); await api('PUT', '/api/vendedores/' + v.id, { ativo: !v.ativo }).catch(erro); telaVendedores(alvo); });
}
function formVendedor(v) {
  const n = !v; v = v || { nome: '', usuario: '', telefone: '', email: '', meta: 0, comissao_pct: 0, papel: 'vendedor', cor: '' };
  const f = modal(`<h3><i data-lucide="${n ? 'user-plus' : 'pencil'}"></i>${n ? 'Novo vendedor' : 'Editar ' + esc(v.nome)}</h3><div class="linha">
    <div class="campo" style="grid-column:1/-1"><label>Nome (aparece na proposta)</label><input class="inp" id="vNome" value="${esc(v.nome)}"></div>
    <div class="campo"><label>Usuário (para entrar)</label><input class="inp" id="vUsu" value="${esc(v.usuario)}" ${n ? '' : 'disabled'} placeholder="ex.: joao"></div>
    <div class="campo"><label>WhatsApp (o cliente fala com ele)</label><input class="inp" id="vTel" value="${esc(v.telefone)}" placeholder="(91) 90000-0000"></div>
    <div class="campo"><label>E-mail</label><input class="inp" id="vEmail" value="${esc(v.email)}"></div>
    <div class="campo"><label>Meta mensal (R$ fechado)</label><input class="inp" id="vMeta" type="number" value="${v.meta || 0}"></div>
    <div class="campo"><label>Comissão (%)</label><input class="inp" id="vCom" type="number" step="0.1" value="${v.comissao_pct || 0}"></div>
    <div class="campo"><label>Acréscimo oculto no material (%)</label><input class="inp" id="vAcr" type="number" step="0.5" min="0" value="${v.acrescimo_pct || 0}"><span class="dica">Placas, inversor, baterias e itens. Ele não vê.</span></div>
    <div class="campo"><label>Login do FluxIA (WhatsApp com robô)</label><input class="inp" id="vFxL" value="${esc(v.fluxia_login || '')}" placeholder="vazio = sem WhatsApp"></div>
    <div class="campo"><label>Senha do FluxIA</label><input class="inp" id="vFxS" type="password" placeholder="${v.fluxia_login ? '(guardada — só preencha para trocar)' : ''}"></div>
    <div class="campo"><label>Acréscimo oculto no ar-condicionado (%)</label><input class="inp" id="vAcrAr" type="number" step="0.5" min="0" value="${v.acrescimo_ar_pct ?? 10}"><span class="dica">Somado ao preço que ele digita. Ele não vê.</span></div>
    <div class="campo"><label>Permissão</label><select class="inp" id="vPapel"><option value="vendedor" ${v.papel !== 'admin' ? 'selected' : ''}>Vendedor (vê só os dele)</option><option value="admin" ${v.papel === 'admin' ? 'selected' : ''}>Administrador (vê tudo)</option></select></div>
    <div class="campo"><label>Cor</label><input class="inp" id="vCor" type="color" value="${v.cor || corDe(v.id || 1)}" style="height:44px;padding:4px"></div>
    ${n ? '<div class="campo" style="grid-column:1/-1"><label>Senha (vazio = gero uma)</label><input class="inp" id="vSenha" placeholder="mínimo 6 caracteres"></div>' : ''}</div>
    <div class="acoes"><button class="bt" onclick="fecharModal()">Cancelar</button><button class="bt pri" id="vOk"><i data-lucide="save"></i>Salvar</button></div>`);
  $('#vTel', f).oninput = e => e.target.value = mascTel(e.target.value);
  $('#vOk', f).onclick = async () => {
    const b = { nome: $('#vNome').value.trim(), telefone: $('#vTel').value, email: $('#vEmail').value, meta: +$('#vMeta').value || 0, comissao_pct: +$('#vCom').value || 0, acrescimo_pct: +$('#vAcr').value || 0, acrescimo_ar_pct: +$('#vAcrAr').value || 0, fluxia_login: $('#vFxL').value.trim(), fluxia_senha: $('#vFxS').value, papel: $('#vPapel').value, cor: $('#vCor').value };
    try {
      if (n) { b.usuario = $('#vUsu').value.trim(); b.senha = $('#vSenha').value; const r = await api('POST', '/api/vendedores', b); modal(`<h3><i data-lucide="check"></i>Vendedor criado</h3><p>Mande para ${esc(b.nome)}:</p><div class="card"><b>Endereço:</b> ${location.origin}<br><b>Usuário:</b> ${esc(b.usuario)}<br><b>Senha:</b> ${esc(r.senha)}</div><div class="acoes"><button class="bt wa" onclick="window.open(waLink('${esc(b.telefone)}', 'Seu acesso ao painel de orçamentos da MS Energy:\\n${location.origin}\\nUsuário: ${esc(b.usuario)}\\nSenha: ${esc(r.senha)}'),'_blank')"><i data-lucide="message-circle"></i>Enviar no WhatsApp</button><button class="bt pri" onclick="fecharModal()">Pronto</button></div>`); }
      else { await api('PUT', '/api/vendedores/' + v.id, b); fecharModal(); toast('Vendedor atualizado'); }
      telaVendedores($('#conteudo'));
    } catch (e) { erro(e); }
  };
}

// ------------------------------------------------------------------ minha conta
async function telaConta(alvo) {
  const u = S.eu;
  alvo.innerHTML = topo('Minha conta', 'user') + `<div class="grade g2"><div class="card brilho"><h3><i data-lucide="id-card" style="color:var(--verde)"></i>Meus dados (aparecem na proposta)</h3>
    <div class="linha"><div class="campo" style="grid-column:1/-1"><label>Nome</label><input class="inp" id="cNome" value="${esc(u.nome)}"></div>
    <div class="campo"><label>WhatsApp</label><input class="inp" id="cTel" value="${esc(u.telefone || '')}" placeholder="(91) 90000-0000"></div><div class="campo"><label>E-mail</label><input class="inp" id="cEmail" value="${esc(u.email || '')}"></div></div>
    <button class="bt pri" id="cSalvar" style="margin-top:14px"><i data-lucide="save"></i>Salvar dados</button></div>
    <div class="card"><h3><i data-lucide="lock" style="color:var(--verde)"></i>Trocar senha</h3><div class="grade" style="gap:12px">
    <div class="campo"><label>Senha atual</label><input class="inp" type="password" id="cAtual" autocomplete="current-password"></div><div class="campo"><label>Senha nova</label><input class="inp" type="password" id="cNova" autocomplete="new-password"></div><div class="campo"><label>Repita a senha nova</label><input class="inp" type="password" id="cNova2" autocomplete="new-password"></div></div>
    <button class="bt" id="cSenha" style="margin-top:14px"><i data-lucide="key-round"></i>Trocar senha</button></div></div>`;
  icones(); $('#cTel').oninput = e => e.target.value = mascTel(e.target.value);
  $('#cSalvar').onclick = async () => { try { S.eu = await api('PUT', '/api/eu', { nome: $('#cNome').value, telefone: $('#cTel').value, email: $('#cEmail').value }); toast('Dados salvos'); montarCasca('conta'); } catch (e) { erro(e); } };
  $('#cSenha').onclick = async () => { if ($('#cNova').value !== $('#cNova2').value) return toast('As senhas novas não são iguais', 'erro'); try { await api('PUT', '/api/eu', { senha_atual: $('#cAtual').value, senha_nova: $('#cNova').value }); toast('Senha trocada'); ['#cAtual', '#cNova', '#cNova2'].forEach(s => $(s).value = ''); } catch (e) { erro(e); } };
}

// ------------------------------------------------------------------ orçamento fácil (conversa em etapas, estilo agente do Hermes)
let F = null;
const TELHADOS = [['ceramico', 'Telha de barro'], ['fibrocimento', 'Telha Eternit'], ['metalico', 'Telha de metal'], ['laje', 'Laje'], ['solo', 'No chão']];
function passosFacil() {
  const d = F.dados, pn = (d.cliente_nome || '').split(' ')[0] || 'o cliente';
  return [
    { k: 'nome', p: 'Oi! Vamos montar o orçamento juntos, é rapidinho. 😊<br><b>Qual é o nome do cliente?</b>', tipo: 'texto', ph: 'Nome completo', obrig: true, set: v => d.cliente_nome = v },
    { k: 'tel', p: `<b>Qual o WhatsApp de ${esc(pn)}?</b><br><small class="mut">Para mandar a proposta depois.</small>`, tipo: 'texto', ph: '(91) 90000-0000', masc: mascTel, pular: true, set: v => d.cliente_tel = v },
    { k: 'cidade', p: '<b>Em qual cidade vai ser a instalação?</b>', tipo: 'texto', ph: 'Ex.: Capitão Poço', pular: true, set: v => d.cliente_cidade = v },
    { k: 'modo', p: '<b>Como você sabe quanto ele gasta de luz?</b>', tipo: 'botoes', ops: [['conta', '💵 Pelo valor da conta (R$)'], ['kwh', '⚡ Pelo kWh da conta']], set: v => d.modo_consumo = v },
    { k: 'consumo', p: d.modo_consumo === 'conta' ? '<b>Quanto vem a conta de luz por mês, em média?</b>' : '<b>Quantos kWh ele gasta por mês?</b><br><small class="mut">Está escrito na conta de luz, perto do valor.</small>', tipo: 'numero', pre: d.modo_consumo === 'conta' ? 'R$' : '', suf: d.modo_consumo === 'conta' ? '' : 'kWh', obrig: true, set: v => { if (d.modo_consumo === 'conta') d.conta_rs = v; else d.consumo = v; } },
    { k: 'telhado', p: '<b>Onde as placas vão ficar?</b>', tipo: 'botoes', ops: TELHADOS.map(([v, t]) => [v, t]), set: v => d.estrutura_id = v },
    { k: 'bateria', p: '<b>Ele quer ter energia quando faltar luz?</b><br><small class="mut">Para isso precisa de bateria.</small>', tipo: 'botoes', ops: [['nao', 'Não precisa'], ['basica', 'Sim, só o básico (geladeira, luz, TV)'], ['mb48314', 'Sim, a casa toda'], ['as2', 'Mostrar as duas opções']],
      set: v => { d.tipo = v === 'nao' ? 'ongrid' : 'hibrido'; d.baterias = v === 'basica' ? [{ id: 'basica5', qtd: 1 }] : v === 'mb48314' ? [{ id: 'mb48314', qtd: 1 }] : v === 'as2' ? [{ id: 'basica5', qtd: 1 }, { id: 'mb48314', qtd: 1 }] : []; } },
    { k: 'extras', p: '<b>Vai incluir mais alguma coisa?</b><br><small class="mut">Toque no + para adicionar. Se não for nada, é só continuar.</small>', tipo: 'extras' },
    ...d.extras.filter(e => { const x = S.cfg.extras.find(y => y.id === e.id); return x && (x.preco_livre || x.icone === 'ar'); }).map(e => {
      const x = S.cfg.extras.find(y => y.id === e.id);
      return { k: 'arpreco_' + e.id, p: `<b>Quanto você vai cobrar por cada ${esc(x.nome.replace('SPLIT INVERTER ', '').toLowerCase())}?</b><br><small class="mut">Valor de 1 aparelho, com instalação.</small>`, tipo: 'numero', pre: 'R$', obrig: true,
        set: v => { const it = F.dados.extras.find(y => y.id === e.id); if (it) { it.preco_vendedor = Number(v); if (S.eu.papel === 'admin') it.preco = Number(v); } } };
    }),
    { k: 'outro', p: '<b>Quer somar algum outro custo?</b><br><small class="mut">Ex.: frete, material a mais, mão de obra extra.</small>', tipo: 'botoes', ops: [['nao', 'Não'], ['sim', 'Sim, quero somar']], set: v => { F.querOutro = v === 'sim'; } },
    ...(F.querOutro ? [{ k: 'outro_desc', p: '<b>O que é esse custo?</b>', tipo: 'texto', ph: 'Ex.: Frete até o sítio', obrig: true, set: v => F.outroDesc = v },
      { k: 'outro_valor', p: '<b>Quanto é?</b>', tipo: 'numero', pre: 'R$', obrig: true, set: v => { d.extras = d.extras.filter(e => !String(e.id).startsWith('outro_')); d.extras.push({ id: 'outro_' + Date.now(), nome: (F.outroDesc || 'OUTROS CUSTOS').toUpperCase(), desc: 'Custo adicional', preco: Number(v), qtd: 1, unid: 'SV', icone: 'protecao' }); } }] : []),
    { k: 'fim', tipo: 'fim' }
  ];
}
async function telaFacil(alvo) {
  F = { i: 0, dados: dadosPadrao(), msgs: [], hist: [], querOutro: false, outroDesc: '' };
  alvo.innerHTML = topo('Orçamento fácil', 'sparkles', `<a class="bt" href="#/novo"><i data-lucide="sliders-horizontal"></i><span class="esconde-mob">Modo completo</span></a>`) + `
    <div class="chat card"><div class="chat-cab"><div class="ava" style="background:var(--verde)"><i data-lucide="sun"></i></div><div><b>Assistente de orçamentos</b><small class="mut">Responda as perguntas e eu monto tudo</small></div><span class="esp"></span><button class="bt peq fan" id="fRec" title="Começar de novo"><i data-lucide="rotate-ccw"></i></button></div>
    <div class="chat-msgs" id="fMsgs"></div><div class="chat-resp" id="fResp"></div></div>`;
  $('#fRec').onclick = () => telaFacil(alvo);
  perguntar();
}
function fMsg(html, quem = 'bot') { F.msgs.push({ html, quem }); const m = document.createElement('div'); m.className = 'msg ' + quem; m.innerHTML = html; const box = $('#fMsgs'); box.appendChild(m); icones(); requestAnimationFrame(() => { box.scrollTop = box.scrollHeight; m.scrollIntoView({ block: 'nearest' }); }); }
function perguntar() {
  const ps = passosFacil(); const p = ps[F.i]; const r = $('#fResp');
  if (p.tipo === 'fim') return finalFacil();
  fMsg(p.p);
  const voltar = F.i ? '<button class="bt fan peq" id="fVoltar"><i data-lucide="undo-2"></i>Voltar</button>' : '';
  if (p.tipo === 'texto' || p.tipo === 'numero') {
    r.innerHTML = `<form class="chat-form" id="fForm">${p.pre ? `<div class="inp-pre" style="flex:1"><span>${p.pre}</span>` : p.suf ? '<div class="inp-suf" style="flex:1">' : '<div style="flex:1">'}<input class="inp" id="fIn" ${p.tipo === 'numero' ? 'type="number" inputmode="decimal" min="0" step="any"' : 'type="text"'} placeholder="${esc(p.ph || '')}" autocomplete="off">${p.suf ? `<span>${p.suf}</span>` : ''}</div>
      <button class="bt pri"><i data-lucide="send"></i></button></form><div class="flex" style="margin-top:8px">${voltar}<span class="esp"></span>${p.pular ? '<button class="bt fan peq" id="fPular">Pular</button>' : ''}</div>`;
    const inp = $('#fIn'); if (p.masc) inp.oninput = () => inp.value = p.masc(inp.value);
    setTimeout(() => inp.focus(), 60);
    $('#fForm').onsubmit = e => { e.preventDefault(); const v = inp.value.trim(); if (p.obrig && (!v || (p.tipo === 'numero' && !(Number(v) > 0)))) { inp.classList.add('erro'); return toast('Preciso dessa resposta para continuar', 'erro'); } responder(p, v, p.tipo === 'numero' ? (p.pre ? rs(v) : num(v) + ' ' + (p.suf || '')) : v); };
    if (p.pular) $('#fPular').onclick = () => responder(p, '', '<i>pulou</i>');
  } else if (p.tipo === 'botoes') {
    r.innerHTML = `<div class="qbts">${p.ops.map(([v, t]) => `<button class="qbt" data-v="${v}">${t}</button>`).join('')}</div><div class="flex" style="margin-top:8px">${voltar}</div>`;
    $$('.qbt', r).forEach(b => b.onclick = () => responder(p, b.dataset.v, b.textContent));
  } else if (p.tipo === 'extras') {
    const des = () => {
      r.innerHTML = `<div class="grade" style="gap:8px;max-height:280px;overflow:auto">${S.cfg.extras.map(x => { const e = F.dados.extras.find(y => y.id === x.id); return `<div class="item-ex ${e ? 'on' : ''}"><div class="esp"><b>${esc(x.nome.replace('SPLIT INVERTER ', ''))}</b></div><div class="qtd"><button data-m="${x.id}">−</button><span>${e ? e.qtd : 0}</span><button data-p="${x.id}">+</button></div></div>`; }).join('')}</div>
        <div class="flex" style="margin-top:10px">${voltar}<span class="esp"></span><button class="bt pri" id="fCont">Continuar<i data-lucide="arrow-right"></i></button></div>`;
      icones();
      $$('[data-p],[data-m]', r).forEach(b => b.onclick = () => { const id = b.dataset.p || b.dataset.m; let e = F.dados.extras.find(y => y.id === id); if (b.dataset.p) { if (e) e.qtd++; else F.dados.extras.push({ id, qtd: 1 }); } else if (e) { e.qtd--; if (e.qtd <= 0) F.dados.extras = F.dados.extras.filter(y => y.id !== id); } des(); });
      $('#fCont').onclick = () => { const ls = F.dados.extras.filter(e => !String(e.id).startsWith('outro_')).map(e => `${e.qtd}× ${(S.cfg.extras.find(x => x.id === e.id) || {}).nome || e.id}`); responder(p, null, ls.length ? ls.map(esc).join('<br>') : 'Nada a mais'); };
      $('#fVoltar') && ($('#fVoltar').onclick = voltarFacil);
    };
    des(); return;
  }
  icones(); $('#fVoltar') && ($('#fVoltar').onclick = voltarFacil);
}
function responder(p, v, rotulo) {
  F.hist.push({ i: F.i, dados: clone(F.dados), n: F.msgs.length, querOutro: F.querOutro, outroDesc: F.outroDesc });
  if (p.set && v !== null) p.set(v);
  fMsg(esc(String(rotulo).replace(/<[^>]+>/g, m => m === '<br>' ? '\n' : '')).replace(/\n/g, '<br>'), 'eu');
  F.i++; perguntar();
}
function voltarFacil() {
  const h = F.hist.pop(); if (!h) return;
  F.i = h.i; F.dados = h.dados; F.querOutro = h.querOutro; F.outroDesc = h.outroDesc;
  F.msgs = F.msgs.slice(0, h.n - 1); $('#fMsgs').innerHTML = ''; const ms = F.msgs; F.msgs = []; ms.forEach(m => fMsg(m.html, m.quem));
  perguntar();
}
async function finalFacil() {
  const r = $('#fResp'); r.innerHTML = '<div class="vazio" style="padding:14px">Montando o orçamento…</div>';
  let res; try { res = await api('POST', '/api/calcular', { dados: prepararDados(F.dados) }); } catch (e) { return erro(e); }
  const pn = (F.dados.cliente_nome || '').split(' ')[0];
  fMsg(`Pronto! Este é o orçamento de <b>${esc(pn)}</b>: ☀️
    <div class="fim-card">
      ${res.opcoes.map((o, i) => `<div class="fim-valor ${i ? 'sec' : ''}"><small>${res.opcoes.length > 1 ? esc(o.rotulo) : 'Valor do sistema'}</small><b>${rs(o.valor)}</b></div>`).join('')}
      <div class="rz" style="margin-top:10px">
        <div><small>Placas solares</small><b>${res.n_paineis} placas</b></div><div><small>Gera por mês</small><b>${num(res.ger_media)} kWh</b></div>
        <div><small>Conta hoje</small><b>${rs(res.conta_sem, 0)}</b></div><div><small>Conta depois</small><b class="verde">${rs(res.conta_com, 0)}</b></div>
        <div><small>Economia por mês</small><b class="verde">${rs(res.econ_mes, 0)}</b></div><div><small>Se paga em</small><b>${res.payback_txt}</b></div>
      </div>
      ${res.parcela_min ? `<p class="mut" style="margin:10px 0 0;font-size:12.5px">Financiado a partir de <b>${rs(res.parcela_min)}/mês</b> — apenas simulação, pode subir na aprovação.</p>` : ''}
    </div>`);
  r.innerHTML = `<div class="flex wrap"><button class="bt pri" id="fGerar" style="flex:1;padding:14px"><i data-lucide="file-check-2"></i>Gerar a proposta</button>
    <button class="bt" id="fMais"><i data-lucide="trending-up"></i>Aumentar o valor</button><button class="bt" id="fAjustar"><i data-lucide="sliders-horizontal"></i>Ajustar detalhes</button></div>
    <div class="flex" style="margin-top:8px"><button class="bt fan peq" id="fVoltar"><i data-lucide="undo-2"></i>Voltar</button></div>`;
  icones();
  $('#fVoltar').onclick = voltarFacil;
  $('#fAjustar').onclick = () => { sessionStorage.setItem('orc_sim', JSON.stringify(F.dados)); location.hash = '#/novo'; };
  $('#fMais').onclick = () => {
    const f = modal(`<h3><i data-lucide="trending-up"></i>Aumentar o valor</h3><p class="mut">Hoje: <b>${rs(res.valor)}</b>. Digite o novo valor (só pode ser maior).</p>
      <div class="inp-pre"><span>R$</span><input class="inp" id="fNovo" type="number" value="${res.valor}" step="100" style="font-size:20px;font-weight:800"></div>
      <div class="acoes"><button class="bt" onclick="fecharModal()">Cancelar</button><button class="bt pri" id="fOkV">Usar este valor</button></div>`);
    $('#fOkV', f).onclick = () => { const v = Number($('#fNovo').value); if (!(v >= res.valor)) return toast('O valor não pode ser menor que ' + rs(res.valor), 'erro'); F.dados.valor_manual = true; F.dados.valor = v; fecharModal(); fMsg('Aumentar o valor para ' + rs(v), 'eu'); finalFacil(); };
  };
  $('#fGerar').onclick = async () => {
    const b = $('#fGerar'); b.disabled = true; b.textContent = 'Gerando…';
    try {
      const o = await api('POST', '/api/orcamentos', { dados: prepararDados(F.dados) });
      fMsg(`✅ Proposta <b>${o.num}</b> criada! Agora é só mandar para ${esc(pn)}:`);
      r.innerHTML = acoesEnvio(o) + `<div class="flex wrap" style="margin-top:10px"><a class="bt" href="#/orcamento/${o.id}"><i data-lucide="pencil"></i>Abrir orçamento</a><button class="bt pri" id="fNovoOrc"><i data-lucide="sparkles"></i>Fazer outro</button></div>`;
      icones(); $$('[data-acao]', r).forEach(ligarAcao); $('#fNovoOrc').onclick = () => telaFacil($('#conteudo'));
    } catch (e) { erro(e); b.disabled = false; b.innerHTML = '<i data-lucide="file-check-2"></i>Gerar a proposta'; icones(); }
  };
}

// ------------------------------------------------------------------ meu WhatsApp (FluxIA + Hermes): conectar, robô e conversas
const W = { timer: null, qrTimer: null, vend: '', aberta: null, lista: [], st: null };
const wq = () => W.vend ? '?vendedor=' + W.vend : '';
const TIPOS_MSG = { audio: '🎤 Áudio', ptt: '🎤 Áudio', image: '📷 Foto', video: '🎬 Vídeo', document: '📄 Documento', sticker: '🙂 Figurinha', location: '📍 Localização', contact: '👤 Contato', poll: '📊 Enquete', reaction: '👍 Reação' };
function horaWa(ms) { if (!ms) return ''; const d = new Date(ms); const h = new Date(); return d.toDateString() === h.toDateString() ? d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }); }
async function telaWhatsapp(alvo) {
  const adm = S.eu.papel === 'admin';
  const vends = S.vendedores.filter(v => v.fluxia_login);
  if (adm && !W.vend && vends[0]) W.vend = String(vends[0].id);
  if (adm && !vends.length) { alvo.innerHTML = topo('WhatsApp dos vendedores', 'message-circle') + `<div class="card vazio"><i data-lucide="message-circle"></i><div>Nenhum vendedor com WhatsApp ligado. Em <b>Vendedores → Editar</b>, preencha o login do FluxIA.</div></div>`; icones(); return; }
  alvo.innerHTML = topo(adm ? 'WhatsApp dos vendedores' : 'Meu WhatsApp', 'message-circle', adm ? `<select class="inp" id="waVend" style="width:auto">${vends.map(v => `<option value="${v.id}" ${String(v.id) === W.vend ? 'selected' : ''}>${esc(v.nome)}</option>`).join('')}</select>` : '') +
    `<div id="waTopo"><div class="card vazio">Verificando o WhatsApp…</div></div>
     <div class="wa-chat card" style="margin-top:16px"><div class="wa-lista"><div class="wa-busca"><div class="inp-pre"><span><i data-lucide="search" style="width:15px;height:15px"></i></span><input class="inp" id="waQ" placeholder="Buscar conversa…"></div></div><div id="waLista"><div class="vazio">Carregando conversas…</div></div></div>
     <div class="wa-conv" id="waConv"><div class="vazio" style="margin:auto"><i data-lucide="messages-square"></i><div>Escolha uma conversa</div></div></div></div>`;
  icones();
  $('#waVend') && ($('#waVend').onchange = e => { W.vend = e.target.value; W.aberta = null; telaWhatsapp(alvo); });
  $('#waQ').oninput = () => desenharListaWa();
  await atualizarWa(true);
  W.timer = setInterval(() => atualizarWa(false), 9000);
}
async function atualizarWa(primeira) {
  try { W.st = await api('GET', '/api/wa/status' + wq()); } catch (e) { $('#waTopo').innerHTML = `<div class="aviso erro"><i data-lucide="alert-triangle"></i>${esc(e.message)}</div>`; icones(); return; }
  desenharTopoWa();
  if (W.st.whatsapp.status === 'connected' || primeira) {
    try { W.lista = await api('GET', '/api/wa/conversas' + wq()); desenharListaWa(); } catch (e) { if (primeira) $('#waLista').innerHTML = `<div class="vazio">${esc(e.message)}</div>`; }
    if (W.aberta) abrirConversaWa(W.aberta, true);
  }
}
function desenharTopoWa() {
  const s = W.st, w = s.whatsapp; const con = w.status === 'connected';
  const rot = { connected: ['Conectado', 'var(--verde)', 'check-circle-2'], offline: ['Conectado, mas o celular está sem internet', 'var(--amarelo)', 'wifi-off'], disconnected: ['Desconectado', '#f87171', 'x-circle'], unknown: ['Sem resposta do WhatsApp', 'var(--amarelo)', 'help-circle'] }[w.status] || ['?', 'var(--mut)', 'help-circle'];
  $('#waTopo').innerHTML = `<div class="grade g3">
    <div class="card ${con ? 'brilho' : ''}"><h3><i data-lucide="smartphone" style="color:var(--verde)"></i>WhatsApp</h3>
      <div class="flex"><i data-lucide="${rot[2]}" style="color:${rot[1]};width:28px;height:28px"></i><div><b style="font-size:18px;color:${rot[1]}">${rot[0]}</b><br><small class="mut">${w.phone ? '+' + esc(w.phone) : 'nenhum número ligado'}</small></div></div>
      <div class="flex wrap" style="margin-top:14px">${con ? `<button class="bt perigo peq" id="waDesc"><i data-lucide="unplug"></i>Desconectar</button>` : `<button class="bt pri" id="waQr"><i data-lucide="qr-code"></i>Conectar com QR code</button><button class="bt" id="waCod"><i data-lucide="hash"></i>Conectar com código</button>`}</div></div>
    <div class="card"><h3><i data-lucide="bot" style="color:var(--verde)"></i>Robô de atendimento<span class="esp"></span><label class="chave"><input type="checkbox" id="waRobo" ${s.robo_ligado ? 'checked' : ''}><i></i></label></h3>
      <b style="font-size:18px;color:${s.robo_ligado ? 'var(--verde)' : '#f87171'}">${s.robo_ligado ? 'Ligado' : 'Desligado'}</b><br><small class="mut">${s.robo_ligado ? 'O robô responde os clientes sozinho. Quando você responde uma conversa pelo celular, ele pausa nela.' : 'Ninguém responde automaticamente. Ligue para o robô atender.'}</small></div>
    <div class="card"><h3><i data-lucide="activity" style="color:var(--verde)"></i>Hoje</h3><div class="rz"><div><small>Mensagens recebidas</small><b>${s.hoje.messages || 0}</b></div><div><small>Clientes</small><b>${s.hoje.clients || 0}</b></div></div>
      <button class="bt peq" id="waAviso" style="margin-top:12px"><i data-lucide="bell"></i>Aviso de cliente novo</button></div></div>`;
  icones();
  $('#waRobo').onchange = async e => { try { await api('PUT', '/api/wa/robo' + wq(), { ligado: e.target.checked }); toast(e.target.checked ? 'Robô ligado' : 'Robô desligado'); atualizarWa(false); } catch (er) { erro(er); e.target.checked = !e.target.checked; } };
  $('#waQr') && ($('#waQr').onclick = conectarQrWa);
  $('#waCod') && ($('#waCod').onclick = conectarCodigoWa);
  $('#waDesc') && ($('#waDesc').onclick = async () => { if (!confirm('Desconectar o WhatsApp do robô? Para voltar vai ser preciso ler o QR code de novo.')) return; if (!confirm('Tem certeza? O robô para de atender até reconectar.')) return; try { await api('POST', '/api/wa/desconectar' + wq()); toast('WhatsApp desconectado'); atualizarWa(true); } catch (e) { erro(e); } });
  $('#waAviso').onclick = () => {
    const c = s.config || {};
    const f = modal(`<h3><i data-lucide="bell"></i>Aviso de cliente novo</h3><p class="mut">O robô manda um aviso neste número quando chega um cliente interessado.</p>
      <div class="campo"><label>WhatsApp que recebe o aviso</label><input class="inp" id="waNot" value="${esc(mascTel(c.notify_phone || ''))}" placeholder="(91) 90000-0000"></div>
      <div class="campo" style="margin-top:12px"><label>Mensagem quando estiver fechado</label><textarea class="inp" id="waFech">${esc(c.closed_message || '')}</textarea></div>
      <div class="acoes"><button class="bt" onclick="fecharModal()">Cancelar</button><button class="bt pri" id="waSalvarCfg">Salvar</button></div>`);
    $('#waNot', f).oninput = e => e.target.value = mascTel(e.target.value);
    $('#waSalvarCfg', f).onclick = async () => { try { await api('PUT', '/api/wa/config' + wq(), { notify_phone: digitos($('#waNot').value), closed_message: $('#waFech').value }); fecharModal(); toast('Salvo'); atualizarWa(false); } catch (e) { erro(e); } };
  };
}
async function conectarQrWa() {
  const f = modal(`<h3><i data-lucide="qr-code"></i>Conectar o WhatsApp</h3>
    <ol class="mut" style="padding-left:18px;margin:0 0 12px;line-height:1.7"><li>No celular, abra o <b>WhatsApp</b></li><li>Toque em <b>⋮ (ou Configurações) → Dispositivos conectados → Conectar dispositivo</b></li><li>Aponte a câmera para o código abaixo</li></ol>
    <div id="waQrBox" class="wa-qr"><div class="vazio">Gerando o código… (até 25 s)</div></div>
    <p class="mut" style="text-align:center;font-size:12.5px">O código muda sozinho a cada 20 segundos.</p>
    <div class="acoes"><button class="bt" onclick="fecharModal()">Fechar</button></div>`);
  const gerar = async () => {
    try {
      const r = await api('POST', '/api/wa/qr' + wq());
      if (!$('#waQrBox')) return;
      if (window.qrcode) { const q = qrcode(0, 'M'); q.addData(r.qr); q.make(); $('#waQrBox').innerHTML = q.createSvgTag({ cellSize: 6, margin: 4, scalable: true }); }
      else $('#waQrBox').innerHTML = '<div class="aviso erro">Não carreguei o gerador de QR. Use "Conectar com código".</div>';
    } catch (e) { if ($('#waQrBox')) $('#waQrBox').innerHTML = `<div class="aviso ${String(e.message).includes('já está conectado') ? 'ok' : 'erro'}">${esc(e.message)}</div>`; }
  };
  await gerar();
  W.qrTimer = setInterval(async () => {
    if (!$('#waQrBox')) { clearInterval(W.qrTimer); W.qrTimer = null; return; }
    try { const st = await api('GET', '/api/wa/status' + wq()); if (st.whatsapp.status === 'connected') { clearInterval(W.qrTimer); W.qrTimer = null; fecharModal(); toast('<b>WhatsApp conectado!</b>'); atualizarWa(true); return; } } catch (e) { /* segue */ }
    if (!W._qrN) W._qrN = 0; if (++W._qrN % 4 === 0) gerar();
  }, 5000);
}
function conectarCodigoWa() {
  const f = modal(`<h3><i data-lucide="hash"></i>Conectar com código</h3><p class="mut">Use quando não der para ler o QR code (por exemplo, se o WhatsApp está no mesmo celular).</p>
    <div class="campo"><label>Número do WhatsApp que vai ser conectado</label><input class="inp" id="waTel" placeholder="(91) 90000-0000" inputmode="tel"></div>
    <div id="waCodBox" style="margin-top:14px"></div>
    <div class="acoes"><button class="bt" onclick="fecharModal()">Fechar</button><button class="bt pri" id="waGerCod">Gerar código</button></div>`);
  $('#waTel', f).oninput = e => e.target.value = mascTel(e.target.value);
  $('#waGerCod', f).onclick = async () => {
    const b = $('#waGerCod'); b.disabled = true;
    try { const r = await api('POST', '/api/wa/codigo' + wq(), { telefone: $('#waTel').value });
      $('#waCodBox').innerHTML = `<div class="card" style="text-align:center"><small class="mut">Digite este código no WhatsApp</small><div style="font-size:34px;font-weight:800;letter-spacing:.12em;color:var(--verde)">${esc(r.code)}</div></div>
        <ol class="mut" style="padding-left:18px;line-height:1.7"><li>No WhatsApp: <b>Dispositivos conectados → Conectar dispositivo</b></li><li>Toque em <b>“Conectar com número de telefone”</b></li><li>Digite o código acima</li></ol>`;
    } catch (e) { $('#waCodBox').innerHTML = `<div class="aviso erro">${esc(e.message)}</div>`; } finally { b.disabled = false; }
  };
}
function desenharListaWa() {
  const q = ($('#waQ')?.value || '').toLowerCase(); const el = $('#waLista'); if (!el) return;
  const l = W.lista.filter(c => !q || (c.nome + ' ' + c.numero + ' ' + c.ultima).toLowerCase().includes(q));
  el.innerHTML = l.map(c => `<div class="wa-it ${W.aberta === c.jid ? 'on' : ''}" data-jid="${esc(c.jid)}"><div class="ava" style="background:${c.grupo ? 'var(--azul)' : corDe(c.total)}">${c.grupo ? '👥' : iniciais(c.nome || c.numero || '?')}</div>
    <div class="esp"><div class="flex"><b>${esc(c.nome || (c.numero ? '+' + c.numero : 'Contato ·' + c.jid.split('@')[0].slice(-4)))}</b><span class="esp"></span><small class="mut">${horaWa(c.quando)}</small></div>
    <small class="mut">${c.minha ? '✓ ' : ''}${esc(c.ultima || TIPOS_MSG[c.tipo] || '')}</small>${c.ia_desligada ? ' <span class="pilula" style="font-size:10px;padding:1px 6px">robô off</span>' : ''}</div></div>`).join('') || '<div class="vazio">Nenhuma conversa ainda.</div>';
  $$('.wa-it', el).forEach(d => d.onclick = () => abrirConversaWa(d.dataset.jid));
}
async function abrirConversaWa(jid, silencioso) {
  W.aberta = jid; const c = W.lista.find(x => x.jid === jid) || { jid, nome: '', numero: '' };
  const box = $('#waConv'); if (!box) return;
  if (!silencioso) { desenharListaWa(); box.innerHTML = '<div class="vazio" style="margin:auto">Carregando…</div>'; $('.wa-chat')?.classList.add('aberta'); }
  let ms; try { ms = await api('GET', `/api/wa/conversas/${encodeURIComponent(jid)}/mensagens` + wq()); } catch (e) { if (!silencioso) box.innerHTML = `<div class="vazio">${esc(e.message)}</div>`; return; }
  if (W.aberta !== jid) return;
  const rascunho = $('#waTxt')?.value || '';
  const fundo = box.querySelector('.wa-msgs'); const noFim = !fundo || fundo.scrollTop + fundo.clientHeight >= fundo.scrollHeight - 40;
  box.innerHTML = `<div class="wa-cab"><button class="bt fan peq wa-volta" id="waVolta"><i data-lucide="arrow-left"></i></button><div class="ava" style="background:${corDe(c.total)}">${iniciais(c.nome || c.numero || '?')}</div><div class="esp"><b>${esc(c.nome || (c.numero ? '+' + c.numero : 'Contato ·' + jid.split('@')[0].slice(-4)))}</b><br><small class="mut">${c.numero ? '+' + esc(c.numero) : (c.grupo ? 'Grupo' : 'Número oculto pelo WhatsApp')}</small></div>
      ${c.conv_id ? `<label class="flex mut" style="font-size:12.5px" title="Robô nesta conversa">🤖 <label class="chave"><input type="checkbox" id="waIa" ${c.ia_desligada ? '' : 'checked'}><i></i></label></label>` : ''}</div>
    <div class="wa-msgs">${ms.map(m => `<div class="wa-m ${m.minha ? 'eu' : ''}">${m.texto ? esc(m.texto).replace(/\n/g, '<br>') : `<i class="mut">${TIPOS_MSG[m.tipo] || m.tipo}</i>`}<small>${horaWa(m.quando)}${m.texto && TIPOS_MSG[m.tipo] ? ' · ' + TIPOS_MSG[m.tipo] : ''}</small></div>`).join('') || '<div class="vazio">Sem mensagens.</div>'}</div>
    <form class="wa-env" id="waEnv"><textarea class="inp" id="waTxt" rows="1" placeholder="Escreva uma mensagem…">${esc(rascunho)}</textarea><button class="bt pri"><i data-lucide="send"></i></button></form>`;
  icones();
  const mm = box.querySelector('.wa-msgs'); if (noFim || !silencioso) mm.scrollTop = mm.scrollHeight;
  $('#waVolta').onclick = () => { W.aberta = null; $('.wa-chat')?.classList.remove('aberta'); desenharListaWa(); };
  $('#waIa') && ($('#waIa').onchange = async e => { try { await api('PUT', `/api/wa/conversas/${c.conv_id}/robo` + wq(), { ligado: e.target.checked }); c.ia_desligada = !e.target.checked; toast(e.target.checked ? 'Robô ligado nesta conversa' : 'Robô desligado nesta conversa'); desenharListaWa(); } catch (er) { erro(er); } });
  const txt = $('#waTxt'); txt.onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#waEnv').requestSubmit(); } };
  $('#waEnv').onsubmit = async e => { e.preventDefault(); const t = txt.value.trim(); if (!t) return; txt.disabled = true;
    try { await api('POST', `/api/wa/conversas/${encodeURIComponent(jid)}/enviar` + wq(), { texto: t }); txt.value = ''; setTimeout(() => abrirConversaWa(jid, true), 1200); } catch (er) { erro(er); } finally { txt.disabled = false; txt.focus(); } };
}

iniciar();
