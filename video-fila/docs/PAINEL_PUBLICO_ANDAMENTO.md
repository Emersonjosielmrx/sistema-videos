# Painel :8790 acessível de qualquer lugar + melhorias (pedido da dona 25/10/2026 ~00:10)

> "coloque o meu painel tb na vps o dos videos do youtube e tal de qualquer lugar da internet e nao so nesse pc e
> faças todas as melhorias possíveis no meu painel tb"

## FEITO (25/10 00:20–03:20)
1. [x] `tunel_painel.py` (túnel SSH reverso PC1:8790 → hermes-prod 127.0.0.1:8099), tarefa PainelTunel a cada 5 min
   com trava (só 1 cópia). Log `logs\tunel_painel.log`.
2. [x] Traefik `/opt/traefik-config/dynamic/videos.yml` (cópia em `vps\videos.yml`) → https://videos.opus-sem-limites.com.br.
   Testado: sem chave 401, cookie errado 401, link com chave → cookie Secure → /api/geral 200 em ~2 s.
3. [x] Cookie `Secure` em HTTPS, SameSite=Lax (abrir pelo link do Telegram/WhatsApp funciona).
4. [x] Link em `estado\painel_link_publico.txt`.
5. [x] Melhorias: app instalável no celular (manifest, ícones, service worker com aviso "sem conexão"); atalho no menu
   para o Painel de Clientes. (Os itens antigos de MELHORIAS_PAINEL.md — ficha do vídeo, segurar/liberar por vídeo,
   narrador no "o que dá mais view" — continuam pendentes lá.)
6. [x] Prints públicos desktop/celular (`logs\prints_painel\publico_*.png`): dados carregam, 0 erro de JS, sem rolagem lateral.

## Limite
O painel roda no PC1: se o PC1 desligar ou ficar sem internet, o endereço público mostra "sem conexão".
