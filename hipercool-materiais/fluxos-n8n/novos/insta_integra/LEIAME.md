# D:\hipercool-materiais\fluxos-n8n\novos\insta_integra\LEIAME.md

# 🔗 Instagram: Diagnóstico ➜ Produção (26/11/2026)

Liga os 2 fluxos do n8n6 para trabalharem juntos:

| Papel | Fluxo | id | Webhook |
|---|---|---|---|
| 🔎 Diagnóstico | 📸 INSTAGRAM · Relatório do Perfil com IA | `Zj1EwQeAGBTwpShB` | `/webhook/insta-relatorio?senha=publica-5b514a` |
| 🏭 Produção | 📸 INSTAGRAM · 30 Dias de Posts Prontos com IA | `Cy1QZOsj5WimgWnC` | `/webhook/posts30` (`?diag=1` já marca o diagnóstico) |

## Como funciona
1. O **Relatório** lê o perfil e os últimos 30 posts da conta conectada ao n8n (`_lucrocomia_`), calcula as métricas e a IA analisa.
   Agora a IA também devolve o **plano do mês**: `mix_formatos` (carrossel/post/reels, soma 30, mín. 4 e máx. 16 cada),
   `hora_sugerida`, `pilares_que_funcionam`, `evitar`, `regras_para_legenda`.
2. O Relatório grava um **diagnóstico enxuto** em `ig:diagnostico` (Redis redis2 DB 4, validade 30 dias) — nó
   `💾 Guarda o diagnóstico (30 dias)`. A página ganhou o cartão **📅 Plano para o próximo mês** com o botão
   **Criar 30 dias de posts com base neste diagnóstico** (abre `posts30?diag=1`).
3. No **30 Dias**, o formulário tem **🔎 Usar o diagnóstico** e **⏰ Publicar no melhor horário do diagnóstico**.
   Depois de responder o link (página abre na hora), o fluxo:
   `📖 Lê o diagnóstico` ➜ `🧩 O diagnóstico serve?` ➜ `🔀 E o diagnóstico?`
   - **pronto**: tem até 7 dias e é da mesma conta ➜ usa
   - **pedir**: não tem / velho ➜ `🌐 Pede um diagnóstico novo` (GET no insta-relatorio com `atualizar=1`) ➜ `⏳ Espera 25 s` ➜ lê de novo
   - **esperar**: até 7 voltas (~2,5 min); se não ficar pronto usa o antigo, ou segue sem
   - **sem**: o dono não marcou, ou o @ do formulário é outra conta (o diagnóstico só existe da conta conectada)
   ➜ `🧩 Prepara o diagnóstico` ➜ 🤖 Estrategista (usa a mistura de formatos, ataca cada "o que melhorar" em ≥3 dias,
   usa as ideias nos 10 primeiros dias, escreve `motivo` por dia) ➜ Organiza (horário do diagnóstico, nunca 3 formatos
   iguais seguidos, guarda `cal.diagnostico`) ➜ 🤖 Redatora (segue `regras_para_legenda`; o "Refazer com IA" também).
4. A página do calendário mostra o cartão **🔎 Mês planejado em cima do diagnóstico** e, em cada dia, **🎯 Por que este post**.
5. **Ciclo fechado**: o Relatório agora lê os calendários (`🗂️ Lê os calendários de 30 dias`, chaves `p30cal:*`), marca
   os posts que vieram do calendário pelo link publicado e mede **interações por pilar** e **calendário x outros posts**.
   O próximo diagnóstico usa isso.

## Arquivos
- `baixa.py` — baixa os 2 fluxos como `original_<id>.json` (**cópia de antes da mudança = backup para voltar**)
- `integra.py` — parte SEMPRE dos `original_*.json`, aplica tudo (trocas conferidas com assert) e gera `novo_*.json`;
  `--publicar` faz PUT + ativa. A API recusa `binaryMode` em settings: o script reenvia sem ele e o servidor mantém `separate`.
- `js/` — códigos dos nós Code novos/reescritos (diag_calcula, diag_junta, p30_serve, p30_prepara, p30_organiza)
- `sim.js` — teste offline dos códigos com dados falsos (`node sim.js`)
- `testa.py diag|p30|tudo` — teste de ponta a ponta pelos webhooks públicos (não publica nada)
- `depois_*.json` — como ficou no servidor depois de publicar

## Teste feito em 26/11/2026
- Diagnóstico novo: nota 60, plano 🎠7 📷7 🎬16, publicar 07:00 (IA tinha pedido 22 reels; o teto de 16 segurou).
- Calendário `teste-integracao-apagar-9d20` (chave 8375bd33b495, publicação automática DESLIGADA): diag "usado",
  30/30 dias com motivo, 0 erros, horário trocado para 07:00, pronto em ~4 min. Mix feito pela IA 14/9/7 (pedido 16/7/7):
  a IA segue a mistura de perto, não à risca (não forçamos para não desalinhar tema e formato).
- Prints conferidos: formulário com as 2 opções, relatório com o cartão do plano, calendário com o cartão do diagnóstico.

## Para voltar atrás
`python ..\..\ferramentas\n8n_servidor.py importa original_<id>.json` não serve (o importa casa pelo nome); use um PUT
com o conteúdo de `original_<id>.json` (mesmo código do `publica()` do integra.py).
