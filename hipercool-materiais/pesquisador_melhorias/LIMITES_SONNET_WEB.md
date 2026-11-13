# Limites do Sonnet 5.5 web (contas claude.ai das empresas) — para o motor do pesquisador

Pesquisa do argon-pesquisa em 04/11/2026 (fontes oficiais abaixo) + medição nossa. Atualizar aqui quando medir algo novo.

## Regras oficiais (claude.ai, plano grátis)
- Janela de SESSÃO de 5 horas: começa na 1ª mensagem e zera 5 h depois. Também existe limite SEMANAL
  (claude.com/pricing: "Limited usage every 5 hours and every week").
- Não é número fixo de mensagens: conta o processamento. Conversa longa (reenvia o histórico a cada passo), arquivos e
  ferramentas gastam mais. Relato de usuários: ~15–35 mensagens curtas por janela no grátis; 3–8 com conversa longa.
- Horário de pico (desde 27/03/2026): seg–sex 10h–16h de Brasília a janela gasta mais rápido no chat web.
- Quando bate o limite, o site mostra a hora exata de volta (o OmniRoute guarda como limitada_ate; o MonitorSonnet lê).
Fontes: support.claude.com/en/articles/8114491-getting-started-with-claude ; .../11647753-how-do-usage-and-length-limits-work ;
.../9797557-usage-limit-best-practices ; claude.com/pricing ; promoclock.co/pt/blog/claude-peak-hours/

## O que isso quer dizer para nós
- Temos ~45 contas no provedor claude-web do OmniRoute (MonitorSonnet: `D:\sonnet web\monitor_sonnet.json`, 10/10 min).
  O OmniRoute troca de conta quando uma bate 429 (a conta fica 10 min de lado e o sonnet-oi confere a volta).
- Uma pesquisa do motor = ~10–15 passos com ferramentas numa conversa que cresce: pode gastar a janela de 1 conta grátis.
  Teoria: 45 contas x ~4,8 janelas/dia = ~200 janelas/dia, divididas com os outros robôs que usam o Sonnet web.
- Dona 04/11: "não precisa ficar 5 h fora, só até os tokens voltarem". Por isso: com cota o motor emenda pesquisas;
  sem cota agenda a próxima para a hora de volta do MonitorSonnet. Exige 8 contas prontas (16 no pico). Teto 48/dia só
  de segurança (sobe sozinho se batido sem falha). Registra contas prontas antes/depois de cada pesquisa
  (motor_registro.jsonl) para medirmos quanto cada uma gasta.

## Medido por nós
- **Contas do plano grátis voltam em 3 a 10 minutos, não em 5 horas** (medido em monitor_sonnet.log de 29/10 a 04/11,
  20+ eventos). O OmniRoute roda com ~45 contas, marca cada uma com `limitada_ate` (poucos minutos à frente) quando
  bate `429`, e o `sonnet-oi` da VPS confirma a volta mandando um "oi" real na conta. Exemplos:
  30/10 22:04 -> 22:09 (5 min); 01/11 00:04 -> 00:07 (3 min); 03/11 11:44 -> 11:47 (3 min).
- Isso quer dizer que 45 contas girando com 5 min fora = praticamente cota contínua para 1 pesquisa por vez.
  O gargalo real é o tempo que cada pesquisa leva (~8–14 min), não a cota.
- Dona 04/11: "não precisa ficar 5 h fora, só até os tokens voltarem". Por isso: com cota o motor emenda pesquisas;
  sem cota agenda a próxima para a hora de volta do MonitorSonnet. Exige 5 contas prontas (8 no pico). Teto 48/dia só
  de segurança (sobe sozinho se batido sem falha). Registra contas prontas antes/depois de cada pesquisa
  (motor_registro.jsonl) para medirmos quanto cada uma gasta.
- 04/11: rodada manual do sonnet-ajudante = 451 s, 12 ferramentas, resposta completa.
- 04/11 1ª pesquisa automática = 803 s (13 min), 16 ferramentas, 16 repos novos (15 inéditos). Área: narração humana.
- 04/11: "API Error: Claude Web stream protocol error" em 9–13 s, 2 vezes seguidas; causa: o Sonnet tentava carregar
  WebFetch/ToolSearch (ferramenta "deferida") e o proxy claude-web quebrava no 3º passo. Solução: só ferramentas
  locais (Read/Grep/Glob/Bash/PowerShell), internet por python/curl no Bash. O motor tenta de novo até 3x.
