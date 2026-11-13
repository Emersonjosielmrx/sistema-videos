// Service worker mínimo (25/10): só para o painel poder ser "instalado" no celular (PWA). Não guarda dado nenhum:
// tudo vai direto para a rede; sem internet mostra um aviso em vez da tela de erro do navegador.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(fetch(e.request).catch(() => new Response(
    '<meta name=viewport content="width=device-width"><body style="background:#000;color:#eee;font-family:sans-serif;padding:24px">' +
    '<h3>Central de Vídeos</h3><p>Sem conexão com o painel agora. Confira a internet do celular; se estiver ok, o PC1 pode estar desligado ou sem internet.</p></body>',
    {headers: {'Content-Type': 'text/html; charset=utf-8'}})));
});
