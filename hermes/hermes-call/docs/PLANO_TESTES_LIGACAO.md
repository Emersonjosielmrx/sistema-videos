# Plano de testes da ligação (Laboratório de Ligações)

> Ideia da dona (03/10/2026): testar o agente de ligação em níveis, do mais barato ao mais real.
> Em cada etapa o agente tem que **passar** no critério; o que aparecer no caminho é corrigido na hora
> e a etapa roda de novo. Quando o problema for **limite do modelo de IA** (e não do prompt/código),
> isso é registrado aqui e avisado à dona.

## Onde roda

- **Laboratório** (`POST /api/agents/{id}/call-lab`, código em `cmd/server/call_lab.go`): conversa
  vendedor IA × cliente IA, com juiz; opcionalmente pronúncia. O vendedor usa exatamente o caminho da
  ligação (agente de ligação em modo voz, prompt da ligação, isca/oferta no histórico, dica de turno).
  Ações simuladas, interlocutor externo de laboratório, nada entra no log de inteligência.
- **Bancada de teste** (cópia separada do Hermes na VPS de produção, `hermes-bancada.service`, banco
  `bancada_*`, porta 127.0.0.1:8091, Telegram desligado): o **8288** está conectado nela e atende **só
  ligações do 8653** como "Cliente Simulado" (voz Edge, diferente da ElevenLabs do vendedor). Script de
  operação: `/root/lab-bancada.sh` (`preparar <release>` / `rodar <agente> <persona> <turnos> <pron> ...`).
  Atualizar a bancada: `bash ops/publicar.sh --so-compilar` e depois `lab-bancada.sh preparar <ID>`.

## Modelos por etapa

| Etapa | Motor do vendedor | Por quê |
|---|---|---|
| 1 (texto) | chaves **grátis** do Gemini (`cli 1 gemini free`), modelos lite | barato; se passa no grátis/antigo, tende a passar no pago/novo |
| 1 (confirmação) | o modelo **pago da ligação** (`call_ai`) | é o que roda na ligação |
| 2 (pronúncia) | o da ligação | só as falas do vendedor viram áudio |
| 3 (ligação real) | o **pago, direto** (sem proxy) | latência e comportamento reais |

Modelos que a chave enxerga (03/10): `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`,
`gemini-3.5-flash-lite`, `gemini-flash-lite-latest` (atual da ligação), `gemini-3.8-flash`.
`gemini-3.8-flash-lite` (texto) dá 404 nesta chave; existe `gemini-3.8-flash-lite-tts` (VOZ) — candidato
a teste na etapa 2 como alternativa ao ElevenLabs.

## Etapa 1 — Texto (roteiro e regras)

Personas: `curioso`, `preco`, `desconfiado`, `apressado`, `sem_interesse` (agentes que LIGAM) e
`atendimento` (agentes que ATENDEM — secretária). 3 rodadas por persona.

**Passa quando**, em 3 de 3 rodadas: nota do juiz ≥ 8; `disse_preco` quando o cliente pergunta;
`respostas_curtas`; `inventou_algo` = falso; nenhuma promessa impossível na ligação (mandar link "agora",
desconto que não existe, "vai aparecer na sua tela"); encerra/conduz ao próximo passo.

Correção, nesta ordem: (1) regra geral de ligação no código (`applyCallGuards`) quando vale pra todo
agente; (2) prompt do agente (testado na bancada; aplicado na produção com OK da dona); (3) se persistir
em todos os modelos com o prompt certo → **limite do modelo** (anotar abaixo).

## Etapa 2 — Pronúncia

Falas do vendedor das conversas aprovadas + frases-chave (preços, nome do produto, siglas) → voz real →
transcrição → palavras que não bateram. **Passa quando** nenhuma palavra-chave sai trocada. Palavra
problemática → dicionário de pronúncia, reteste até zerar. A transcrição também erra: confirmar por
amostragem ouvindo (dona).

## Etapa 3 — Ligação real (bancada)

8653 (produção) liga pro 8288 (bancada). O cliente simulado fala por cima ~8 s depois de fala contínua
(gatilho de teste). **Passa quando**: isca e oferta tocam; a oferta para em < 1 s quando o cliente fala
por cima (log `voice barge-in`); fim da fala → 1º áudio ≤ 2,5 s em média (`voice latência real`);
nenhuma queda; preço falado certo. Disparo: chat do painel da produção ("liga pro 5591992438288"),
precisa de login da dona no navegador do app.

## Etapa 4 — Validação da dona

Uma ligação com a dona pra ouvir a voz e o jeito. Aprovou → `bash ops/marcar-estavel.sh`.

## Registro

### 03/10 noite — bateria completa (v0.7.0) e 1ª ligação real IA × IA

**Etapa 1 (texto, bancada, 6 perfis × 3 rodadas, cliente+juiz `gemini-3.5-flash-lite`):**

| Vendedor | Nota média vendas | Atendimento | Inventou | Notas ≤ 4 | 1ª frase |
|---|---|---|---|---|---|
| Gemini `gemini-flash-lite-latest` (atual da ligação) | **9,3** | 7,3 | 0 | 0 | ~0,75 s |
| Groq `qwen/qwen3.8-27b` (rodízio 3 chaves) | 7,1 | 5,7 | 3 | 4 | ~0,25 s |

Conclusão: **ligação continua no Gemini**; qwen só como reserva. Erros do qwen: termos técnicos ("RAG básica",
"instância") pra cliente apressado, "voy", "Perdeu, me desculpa", palavra corrompida ("Açoitai"), inventou
horários/consulta no atendimento → regra nova `callPlainLanguageRule`. Atendimento (perfil "Teste E") fraco
nos dois motores = problema do roteiro desse perfil (não responde "marcar horário" de cara; preço R$ 99 não vem
na 1ª frase) — sugestão pra dona, não alterado.

**Etapa 2 (pronúncia, voz ElevenLabs → Whisper):** preços por extenso, "WhatsApp", "Inovare" saem certos.
Único problema real: "Pro + IA em reuniões (Meet)" ouvido "PROBI… MIT" → "+" entre palavras agora vira "mais".
O comparador do laboratório passou a normalizar a transcrição (antes acusava "R$ 199,00" × "cento e noventa…").

**Etapa 3 (ligação real, bancada 8288 → produção 8653):**
- Painel sem login → gatilho = bancada liga (`/root/ligacao-teste.sh`); conta de teste da bancada com senha de
  teste própria (só na bancada, root-only) e trial estendido NA BANCADA.
- **Achado 1 — codec derrubava o servidor:** a bancada abortou (SIGABRT, `silk/resampler.c:101`) ao decodificar o
  áudio da produção; a produção já tinha caído assim em 25/09. Lib recompilada com `OPUS_HARDENING=OFF`
  (reproduzido com pacotes aleatórios: lib antiga aborta em 0,03 s; nova passa 200 mil) e instalada.
- **Achado 2 — "atender automaticamente" nunca atendeu:** só registrava "auto-accepted". Aceite real implementado,
  mas o WhatsApp não reconhece o aceite do Hermes (quem liga segue "chamando", o celular da dona segue tocando,
  quem ligou desliga em 40 s) → desligado de novo (`HERMES_AUTO_ANSWER_ACEITAR`), vale o retorno automático.
  **Pendente:** formato do aceite (`signaling.BuildAcceptStanza`). Enquanto isso, ligação Hermes × Hermes só
  funciona "pela metade" (áudio passa por relay sem aceite).
- **Achado 3 — persona da ligação RECEBIDA:** sem agente escolhido pra ligações (VoiceProfileID), quem atende é o
  prompt padrão do ASSISTENTE da dona ("posso gerenciar suas conversas, disparar campanhas"). Só importa quando o
  aceite funcionar — antes disso, escolher um agente de atendimento pras ligações recebidas.
- Latência medida (produção, Gemini): fim da fala → 1º áudio **2,4–4,3 s (média ~3,0 s)** = VAD 0,84 s + STT
  0,2–0,75 s + IA 0,73–0,91 s + voz 0,38–1,84 s (1ª fala da ligação mais lenta). Meta ≤ 2,5 s: maiores ganhos
  possíveis no VAD (840 ms fixos) e na 1ª voz da ElevenLabs. Barge-in funcionou (respostas cortadas quando o
  outro lado falou).

### 03/10 — chaves e modelos
- Chaves Gemini do cofre: `cli 1 gemini free` = **inválida**; `cli 2 free gemini` = **projeto bloqueado**
  pelo Google (403); `LLM Padrão` = ok (o `gemini-2.5-flash-lite` foi desativado pra contas novas).
- **omniroute** (`http://157.173.207.22:20128/v1`, compatível OpenAI, só streaming) responde **sem chave**
  (qualquer um com o endereço usa — recomendado pôr senha). Cadastrado só na bancada como chave
  `omniroute`. Serve pra testar CONTEÚDO; a latência dele (~15 s com modelo lite) não serve pra ligação.
- Comparação (Vendas Hermes Call, cliente "preço", 6 turnos; juiz cortado → notas lidas do texto):

| Vendedor | Via | ms/resposta | Nota |
|---|---|---|---|
| gemini-2.5-flash | omniroute | 5637 | 5 |
| gemini-3.1-flash-lite | omniroute | 15267 | 5 |
| gemini-flash-lite-latest | omniroute | 14721 | 3 |
| gemini-3.5-flash-lite | paga direto | 834 | 4 |
| gemini-flash-lite-latest (atual) | paga direto | 812 | 4 |
| gemini-3.8-flash | paga direto | 4388 | 6 |

  Conclusão: só lite pago direto (~0,8 s) serve pra ligação; 3.8-flash é melhor mas lento (4,4 s); notas
  baixas em todos = problema de prompt/regra, não de modelo. O juiz punia a oferta GRAVADA → corrigido
  (avalia só falas ao vivo). Juiz agora = `gemini-3.5-flash-lite` (não "pensa", não corta o JSON).
- 1º teste: o modelo atual disse "teste de **10 dias**" — a base diz **10 horas** (inventou).

### 03/10 — ranking de velocidade (1ª palavra, medido da VPS, prompt real, 3 rodadas)

| Modelo | Via | 1ª palavra | Total | Resposta ao "quanto custa?" |
|---|---|---|---|---|
| qwen/qwen3.8-27b (sem raciocínio) | Groq direto | 0,29 s | 0,33 s | ✅ |
| qwen/qwen3.8-27b | Groq direto | 0,31 s | 0,37 s | ✅ |
| openai/gpt-oss-20b (raciocínio baixo) | Groq direto | 0,32 s | 0,37 s | ✅ |
| openai/gpt-oss-120b (raciocínio baixo) | Groq direto | 0,48 s | 0,61 s | ❌ errou o Pro (499; certo 399) |
| allam-2-7b | Groq direto | 0,50 s | 0,59 s | ⚠️ enrola, "R$199" cru |
| **gemini-flash-lite-latest (atual)** | Gemini direto | **0,79 s** | 0,88 s | ✅ |
| antigravity/gemini-2.5-flash-thinking | omniroute :20133 | 0,97 s | 1,11 s | ✅ (1/3 falhou) |
| antigravity/gemini-2.5-flash-lite | omniroute :20133 | 1,30 s | 1,48 s | ✅ (1/3 falhou) |
| antigravity/claude-sonnet-4-6 | omniroute :20133 | 1,66 s | 2,33 s | ✅ |
| kr/qwen3-coder-next | omniroute :20133 | 2,67 s | — | instável |
| gemini-2.5-flash / 3.1-flash-lite / claude-haiku | omniroute | — | — | ❌ erro 400 |

Groq (3 chaves) = plano GRATUITO: 1.000 req/dia e 8.000 tokens/min por chave → serve de reserva e
testes; pra principal precisa do plano pago. omniroute (portas 20128/20133) não pede chave; latência e
erros o tornam inviável como principal — usar nas etapas de texto.

### 03/10 — achados de infraestrutura (valem pra produção)
- **Chave da IA da LIGAÇÃO** (`call_ai`, começa `AQ.Ab8RN…`, termina `…kZ4A`): o Google respondeu
  `generate_content_free_tier_requests` (15 req/min por modelo) quando o laboratório apertou. Na
  produção nunca bateu (0 erros de cota desde 26/09, volume baixo), mas 2 ligações simultâneas + análises
  podem bater. A dona diz que paga → conferir no AI Studio o PROJETO da chave …kZ4A (Free × Tier 1).
- `gemini-flash-lite-latest` hoje = `gemini-3.5-flash-lite` (visto no erro de cota).
- **Groq aposentou toda a linha Llama** (inclusive `llama-3.1-8b-instant`). O motor RESERVA da ligação
  (perfil "Teste E": groq/`llama3-8b-8192`) estava morto → `deadModelRemap` manda pro
  `qwen/qwen3.8-27b` (212 ms) / `openai/gpt-oss-120b`. Groq em produção = Whisper + esse reserva.
- O Gemini às vezes TRAVA (sem erro) até o prazo da tentativa: na ligação o streaming chama o reserva
  se a 1ª palavra não vem em ~2,5 s; o laboratório passou a usar esse mesmo caminho e mede a 1ª frase.
- Bateria com a regra nova (`callPromiseRule`): curioso 10, apressado 9, desconfiado 9, sem interesse 8,
  preço 7 (as 2 últimas respostas vieram do reserva após o Gemini travar 20 s — caminho sem streaming).

### 03/10 — 1º teste (Vendas Hermes Call, persona preço, modelo da ligação)
- ✅ preço por extenso na 1ª frase ("cento e noventa e nove reais"); IA ~0,8 s por resposta.
- ❌ inventou desconto ("um empurrãozinho no plano Start"); ❌ prometeu "o link vai aparecer na sua
  tela agora" (na ligação não manda link); ⚠️ a oferta gravada ignora quem pergunta o preço logo após a
  isca (formato de 2 áudios — decisão da dona).
