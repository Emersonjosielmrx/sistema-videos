// ── Moldura das páginas (mesmo visual em todos os fluxos grátis) ──
function pagina(titulo, corpo, script) {
  const css = `
:root{--fundo:#f6f5f2;--cartao:#fff;--texto:#1d1d1b;--suave:#6b6b66;--linha:#e3e1db;--acento:#0f766e;--acento2:#115e59;--erro:#b42318;--ok:#067647}
@media (prefers-color-scheme:dark){:root{--fundo:#121412;--cartao:#1b1e1c;--texto:#ecebe7;--suave:#a3a39d;--linha:#2c302d;--acento:#2dd4bf;--acento2:#5eead4;--erro:#f97066;--ok:#47cd89}}
*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--texto);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:760px;margin:0 auto;padding:20px 16px 48px}h1{font-size:1.45rem;margin:.2em 0 .1em}h2{font-size:1.1rem;margin:1.2em 0 .5em}
.sub{color:var(--suave);margin:0 0 18px}.cartao{background:var(--cartao);border:1px solid var(--linha);border-radius:14px;padding:16px;margin:12px 0}
label{display:block;font-weight:600;margin:12px 0 6px}textarea,input,select{width:100%;padding:11px 12px;border:1px solid var(--linha);border-radius:10px;background:var(--fundo);color:var(--texto);font:inherit}
textarea{min-height:120px;resize:vertical}.linha{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
button,.botao{display:inline-block;background:var(--acento);color:#fff;border:0;border-radius:10px;padding:12px 18px;font:600 1rem system-ui,sans-serif;cursor:pointer;text-decoration:none;margin-top:14px}
@media (prefers-color-scheme:dark){button,.botao{color:#04211e}}
button[disabled]{opacity:.55;cursor:wait}.botao.sec{background:transparent;color:var(--acento);border:1px solid var(--acento)}
.aviso{color:var(--suave);font-size:.9rem}.erro{color:var(--erro);font-weight:600}.ok{color:var(--ok);font-weight:600}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}.grade img,.grade video{width:100%;border-radius:10px;border:1px solid var(--linha);background:#000}
video,audio{width:100%;margin-top:10px;border-radius:10px}pre{white-space:pre-wrap;background:var(--fundo);border:1px solid var(--linha);border-radius:10px;padding:12px;font-size:.9rem}
.barra{height:8px;background:var(--linha);border-radius:99px;overflow:hidden;margin:10px 0}.barra i{display:block;height:100%;background:var(--acento);width:0;transition:width .6s}
.selo{display:inline-block;font-size:.78rem;border:1px solid var(--linha);border-radius:99px;padding:2px 9px;color:var(--suave);margin:2px 4px 2px 0}
footer{color:var(--suave);font-size:.82rem;margin-top:28px}`;
  return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta name="robots" content="noindex"><title>' + titulo + '</title><style>' + css + '</style></head><body><main>' + corpo +
    '<footer>Feito com serviços grátis e sem chave (Hugging Face, Pollinations, Bing/Google Tradutor). Pode demorar ou falhar quando eles estão cheios.</footer>' +
    '</main>' + (script ? '<script>' + script + '</script>' : '') + '</body></html>';
}
const escHtml = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
