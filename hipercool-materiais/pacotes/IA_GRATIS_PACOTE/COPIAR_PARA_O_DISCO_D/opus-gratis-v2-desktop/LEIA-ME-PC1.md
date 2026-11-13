# opus-gratis v2 DESKTOP (cópia enviada do desktop em 31/10/2026)

É a v2 que roda em produção no desktop: base do pc1 (créditos reais, contas sem Opus, reuso de conversa, zelador,
login_fila, og_manter) + o modo SEM NAVEGADOR do desktop (genspark_http_puro.py, genspark_pagina.py, genspark_api.py).
Leia LEIA-ME-V2.md e SEM_NAVEGADOR.md.

Nesta máquina (pc1) ela NÃO está ligada: o D:\opus-gratis do pc1 continua o que roda aqui. Antes de usar:
- `pip install curl_cffi` (o modo PURO precisa);
- os cookies em cookies\ foram capturados no desktop; se o PURO não responder aqui, recapture:
  `python genspark_http_puro.py capturar`;
- contas_genspark.json é a do pc1 (de 31/10), então já tem os logins e marcas de Opus daqui;
- proxy_cc\manter.ps1 já aponta para D:\opus-gratis-v2-desktop, mas o pc1 usa o og_manter.py e o túnel para a VPS.
