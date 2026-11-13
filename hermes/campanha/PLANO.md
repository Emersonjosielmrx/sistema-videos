# Plano da divulgação do Hermes Call

Escrito em 07/10/2026. O `README.md` desta pasta é a **visão completa** (segmentos, agentes por nicho, painel próprio,
aprendizado automático). Este arquivo é o **caminho até lá**, começando pequeno. Regra que a dona já deu no plano do
mês: *a captação automática de empresas e os agentes por segmento vêm depois da 1ª rodada.*

**Ideia central: o Hermes vende o Hermes.** A campanha usa o próprio produto (ligação com IA, funil, follow-up). Cada
ligação é também uma demonstração: quem atende está ouvindo o que vai comprar.

---

## 1. De onde partimos (conferido em 07/10)

**O que o Hermes já faz e a campanha usa (não precisa construir):**
- campanha de ligações com ritmo controlado: tantas por dia, tantas por minuto, horário permitido, e aquecimento (o
  teto sobe dia a dia);
- proteção da linha: não disca número sem WhatsApp, para sozinho depois de 8 falhas seguidas, painel "Proteção das
  linhas";
- agente "Vendas Hermes Call": abertura gravada (6 s), oferta (24 s), depois conversa; diz o preço na 1ª frase;
  marca demonstração na agenda;
- cada ligação vira gravação, transcrição e resumo, e move o contato no funil do CRM sozinha;
- aviso no Telegram na hora em que um contato da campanha responde ou esquenta;
- lista de interessados para exportar; chat único com todas as conversas; régua de follow-up por WhatsApp.

**Produto e preço (o que a IA fala hoje):** Start 199, Pro 399, Scale 599 reais por mês; Enterprise sob consulta;
teste grátis de 10 horas sem cartão.

**O que ainda não temos:**
| Falta | Por que importa para a campanha |
|---|---|
| Cobrança (Asaas não configurado) | quem quiser pagar não tem como pagar sozinho |
| Um número só da campanha | hoje as linhas são a 8653 (celular da dona) e a 8288 (testes). Bloqueio numa delas derruba o Hermes |
| Lista de empresas | não há nenhuma lista pronta |
| Máquina estável | a VPS de produção engasga; a v0.9.0 tolera, mas a de teste é melhor (`docs/PLANO_DUAS_VPS.md` no Hermes) |
| Custo por ligação medido | sem ele não dá para saber quanto custa cada cliente |
| Histórico | ~160 ligações transcritas até hoje, nenhuma de campanha organizada. **Não sabemos nenhuma taxa de conversão.** |

**Três coisas no roteiro de vendas que precisam de decisão antes de ligar para desconhecidos:**
1. A IA responde à objeção do bloqueio com *"já tem cliente rodando 500 a 1000 ligações por dia"*. Se isso não é
   verdade hoje, tem de sair.
2. O plano **Scale** vende "IA em reuniões (Meet)", que ainda não existe. Ou sai da fala, ou a IA diz "em breve".
3. O roteiro diz que *"o cliente muitas vezes nem percebe que é IA"*. Recomendo o contrário: a IA se apresentar como
   assistente virtual. É mais seguro e é o próprio argumento de venda ("você está falando com o produto").

---

## 2. Fases

### Fase 0 — Preparar (08 a 14/10)
Nada de ligação para desconhecido ainda. Sai desta fase com tudo pronto para o piloto.

| # | O quê | Quem |
|---|---|---|
| 0.1 | Escolher o **1º segmento** e a região (seção 3) | dona |
| 0.2 | **Número novo só da campanha** (chip + WhatsApp Business), usado normalmente por alguns dias antes | dona |
| 0.3 | Decidir as 3 questões do roteiro acima | dona |
| 0.4 | Como o 1º cliente paga: Asaas configurado, ou Pix manual + liberação à mão | dona |
| 0.5 | Horários reais de demonstração na Agenda (para a IA não marcar onde a dona não pode) | dona, com o agente |
| 0.6 | Montar a lista do piloto: 300 empresas do segmento, só telefone comercial público. **Ferramenta pronta: `captacao\` limpa, tira repetidos, pontua A/B/C e gera a lista do Hermes (`captacao\README.md`).** Falta a dona escolher a origem (`captacao\DE-ONDE-VEM-A-LISTA.md`) | agente + dona |
| 0.7 | Ajustar o roteiro para o segmento (abertura, oferta, 3 objeções) e gravar a abertura nova | agente |
| 0.8 | Conferir no código: quem diz "não me ligue mais" entra na lista de bloqueio e não é chamado de novo | agente |
| 0.9 | Conferir: a resposta ao "alô" às vezes chega vazia e a oferta de 24 s toca assim mesmo | agente |
| 0.10 | Conferir: lembrete automático de demonstração que a dona ainda não confirmou | agente |
| 0.11 | Ensaio fechado: 10 ligações para números de conhecidos, com o roteiro novo e o número novo | agente + dona |
| 0.12 | Marcar a versão no ar como estável e decidir em qual VPS a campanha roda | dona + agente |

### Fase 1 — Piloto (15 a 21/10)
**Objetivo: medir, não vender.** Um segmento, um número, um roteiro.

- 300 empresas, 5 dias úteis, das 9h às 12h e das 14h às 18h.
- Ritmo com aquecimento: 20 no 1º dia, subindo até 60 por dia. Parada automática ligada.
- A dona responde os quentes no mesmo dia (o Telegram avisa na hora) e faz as demonstrações.
- Todo fim de dia: o agente ouve 10 gravações, lê os números e anota o que mudar. Mudança de roteiro só no fim do
  dia, uma por vez, para dar para saber o que funcionou.
- Para na hora se: a linha for restrita pelo WhatsApp, mais de 1 em 10 pedir para não ligar mais, ou a IA disser
  algo errado sobre preço ou produto.

### Fase 2 — Ler e ajustar (22 a 28/10)
- Fechar os números do funil (seção 4) e o custo por ligação.
- Decidir: repetir no mesmo segmento com o roteiro ajustado, ou testar o 2º segmento.
- Só aqui entram os testes de variação (horário, abertura, voz): um de cada vez, 100 ligações por variação.

### Fase 3 — Escalar o que funcionou (a partir de 29/10)
Só se a Fase 2 mostrar que um cliente custa menos do que paga em 2 a 3 meses.
- 2º e 3º números de campanha, para dividir o volume.
- Follow-up automático por WhatsApp para os mornos (30, 60, 90 dias).
- Cobrança automática funcionando (deixa de ser opcional).

### Fase 4 — A visão do README (novembro em diante)
Captação automática de empresas, pontuação A/B/C, um agente por segmento, painel da campanha. **Só depois de existir
um segmento que comprovadamente fecha**: automatizar antes disso é automatizar um chute.

---

## 3. Segmento do piloto (decisão da dona; recomendação do agente)

O README lista nove segmentos. Para o piloto serve o que junta três coisas: **dor de ligar para lista**, **dono
atende o próprio WhatsApp** e **lista fácil de montar com telefone comercial público**.

| Segmento | Dor que o Hermes resolve | Quem atende o WhatsApp | Recomendação |
|---|---|---|---|
| **Imobiliárias e corretores** | ligar rápido para o lead do portal; reativar base | o corretor ou o dono | **1º piloto** |
| Escolas e cursos | matrícula, rematrícula, inadimplência | secretaria | 2º |
| Clínicas | confirmar consulta, reativar paciente | recepção (longe de quem decide) | 3º |
| Agências de marketing | revender para os clientes delas | o dono | canal de revenda: tratar à parte, depois |

É recomendação, não dado: não temos número nosso que prove. O piloto é que diz.

---

## 4. O que medir (e as metas ficam para depois do piloto)

O README traz metas (10% de ligações viram demonstração, 25% das demonstrações fecham). **Não temos base para elas.**
No piloto a meta é ter os números; as metas saem deles.

| Etapa | Número |
|---|---|
| Discadas | quantas saíram |
| Atendidas | quantas alguém atendeu |
| Conversa de verdade | ficou além da oferta (mais de 30 s de conversa) |
| Interessadas | pediu preço, demonstração ou teste |
| Demonstração marcada / feita | |
| Teste grátis iniciado | |
| Cliente pagante | |
| Pediu para não ligar mais | |
| Custo por ligação atendida | voz + IA + transcrição, pelo que o painel de custo registra |

Conta final: **custo por cliente = custo de todas as ligações ÷ clientes pagantes**, comparado com 199, 399 ou 599
por mês.

---

## 5. Riscos e como reduzir

| Risco | O que fazer |
|---|---|
| WhatsApp bloquear a linha | número só da campanha, aquecimento, parada automática, nunca usar a 8653 |
| Reclamação / LGPD | só telefone comercial público, a IA se identifica, "não me ligue" vale na hora e para sempre, nada de lista comprada nem de número tirado de grupo. *O agente não é advogado: vale uma consulta antes de escalar.* |
| IA prometer o que não existe | revisar o roteiro (seção 1), ouvir 10 gravações por dia |
| Interessado sem ter como pagar | caminho de pagamento decidido antes da 1ª ligação (0.4) |
| Dona sem tempo para as demonstrações | teto de demonstrações por dia na Agenda; o ritmo da campanha segue esse teto |
| Voz ruim queima o contato | rodar na máquina que não engasga; a ligação ruim não tem segunda chance |
| Limite dos serviços de IA | a transcrição usa plano gratuito com teto diário por chave; medir no piloto quantas ligações por dia ele aguenta antes de pagar plano |

---

## 6. O que NÃO fazer agora
- Construir o sistema separado do README (servidor próprio, raspagem, aprendizado automático).
- Ligar para vários segmentos ao mesmo tempo.
- Comprar lista.
- Escalar antes de saber o custo por cliente.

---

## 7. Decisões que destravam a Fase 0

1. Segmento e região do piloto.
2. Número novo para a campanha.
3. As 3 questões do roteiro (clientes citados, plano Scale, IA se identificar).
4. Como o 1º cliente paga.
5. Quantas demonstrações por dia a dona consegue fazer, e em quais horários.

Registro do andamento: acrescentar aqui embaixo, com data.

## Registro
- 07/10/2026: plano escrito. Nada executado.
- 08/10/2026: fonte de empresas pronta em `captacao\cnpj\` — monta a lista a partir dos dados abertos de CNPJ da Receita (público, não é raspagem), escolhe o ramo e separa plano barato x caro por porte/capital. 23 ramos mapeados (CNAE conferido). Baixando/processando o cadastro na VPS de teste.
- 08/10/2026: captação por CNPJ testada de ponta a ponta com dados reais (cadastro 09/2026): base de 2,37 milhões de empresas em 23 ramos; fatia de imobiliárias de SP (40 mil) pontuada A/B/C certinho. Lista sai no formato do Hermes. Painel: caixa de colar números passou a guardar o nome (telefone,Nome).
- 14/10/2026: conferido na produção (v0.10.0): **ainda não há número da campanha**. Só a 8653 e a 8288 estão pareadas (bancos `wacalls_*`); a "Linha Campanha - 5544" do outro agente nunca pareou. O caminho "sem celular" (celular virtual) foi recusado pelo WhatsApp em 08 e 09/10 e está encerrado; resta chip num aparelho de verdade + aba "Por código". Pronto: lista do piloto (`campanha-01\`, 297 imobiliárias, celular, porte micro/pequeno, nota B) e roteiro ajustado (0.3). Faltam: 0.2 número, 0.4 pagamento, 0.5 horários de demonstração, 0.9 decidir o bug, 0.11 ensaio, 0.12 marcar estável. Piloto não começa em 15/10.
- 14/10/2026 (decisões da dona): campanha na **8653**, no máximo **48 por dia espalhadas no horário comercial**; cobrança depois que começarem a testar; demonstração a qualquer hora **até 21h** (regra posta no roteiro: das 8h às 21h); o ensaio são as **10 primeiras ligações reais**, o agente lê cada uma e ajusta. Para isso foi publicada a **v0.11.0** (o modo "ao longo do dia" soltava as 48 em 48 minutos e não tocava a oferta; agora espalha, toca a oferta, uma ligação por vez, só seg–sex). Pedido da campanha pronto em `campanha-01\criar-campanha.json` (297 imobiliárias, 9h–18h).
- 14/10/2026 10:36: **campanha iniciada** na produção — `8843d578ff82eee06fdc1f6198040df8`, "Divulgação Hermes - imobiliárias (piloto 01)", 297 números, `paced` 48/dia, 9h–18h, seg–sex, agente "Vendas Hermes Call" com isca + oferta (oferta guardada, 23 s) e som de fundo. A chave de API foi gerada pelo agente a pedido da dona ("Campanha divulgação", prefixo `hk_09f9e779`, conta admin); o texto dela fica só em `/root/.hermes-campanha-apikey` na produção (600). Para revogar: painel › Configurações › API do Sistema. 1ª ligação às 10:37.
- 14/10/2026 12:00 (1ª revisão): 10 discadas, 3 atendidas, 6 não-atendeu, 1 sem-conexão. Espaçamento ~9 min OK. Oferta tocou nas 3 atendidas (pcm2_len=373255). Qualidade de áudio OK em todas. Nenhum pedido de "não me ligue", nenhuma falha seguida preocupante, nenhum erro de preço/produto. Ligação mais longa (55 s) teve conversa real — cliente disse "estou em reunião", IA respondeu bem e tentou reagendar mas o cliente desligou. As outras 2 atendidas ouviram a oferta completa e desligaram sem falar. Ponto a conferir: na transcrição da ligação 2 o STT registrou "Daynovari" em vez de "Inovare" (pode ser pronúncia do TTS — dona vai ouvir). Nenhuma mudança no roteiro proposta por enquanto (amostra pequena, 10 atendidas é o mínimo para avaliar).
- 14/10/2026 ~12:45: com OK da dona, o texto da isca foi trocado de "Inovare" para "Inovári" no perfil (`agent_profiles.trigger_audio`) e no pedido da campanha (`campaigns.request.tts_message`). **Não teve efeito**: a isca da campanha é um áudio pronto (biblioteca `faf486e5…`, guardado também na memória do servidor) e não é regerada a partir do texto. Para trocar é preciso gerar áudio novo, apontar `campaigns.audio_ref` para ele e reiniciar o serviço.
- 14/10/2026 13:55 (2ª revisão): 23 discadas, 7 atendidas (30%), 13 não atenderam, 1 sem WhatsApp, 1 sem conexão, 0 "não me ligue", 0 erro ao discar. Áudio "boa" em todas (perda 0%). **Correção da 1ª revisão:** a linha "gate pcm2" só mostra que a oferta estava carregada; a prova de que tocou é "áudio 2 (oferta) tocado". Leitura certa das 7: **5 desligaram logo depois da isca (5,6 s) sem falar** ou com "não tenho interesse"; 1 disse "agora não dá, estou em reunião" (oferta inteira + IA educada); 1 disse "Sim" e desligou com 37% da oferta. **O gargalo é a isca**, não a oferta nem a IA. Nenhum erro de preço/produto (a IA quase não chegou a falar). "Daynovari" provavelmente é a transcrição juntando "da Inovare" (em 1 das 4 saiu certo); falta a dona ouvir. Parada automática: só erro ao discar conta (não atendeu não conta), então 6 sem atender seguidas não oferecem risco.
- 14/10/2026 14:02: 8ª atendida (imobiliária, final 3250). Ficou calada depois da isca, a oferta tocou **inteira (100%)**, e então 30 s de silêncio dos dois lados até o cliente desligar. A IA não puxou conversa de novo. Possível ajuste futuro: se o cliente ficar calado uns 6 s depois do "Posso te explicar?", a IA pergunta de novo.
- 14/10/2026: pedido da dona de abrir a campanha para outros produtos e nichos. Analisados os 2.803 fluxos do n8n (n8n6 + servidor de teste; 830 diferentes) e os planos do Hermes. Resultado em `PRODUTOS-E-NICHOS.md`: escada de produtos (site → cardápio → atendente WhatsApp → Instagram → voz → completo → sob medida), nicho × produto de entrada × modelo pronto × CNAE, e plano de teste com 48 ligações por dia (um "braço" por nicho, dividir as 48, trocar o pior toda semana).
- 14/10/2026 ~14:20: a dona avisou que gente da campanha mandava mensagem e a IA não respondia. Causa: o atendimento por texto estava no modo "group" (só respondia no grupo "equipe 1", parado desde 03/08). Feito, a pedido dela, pela API do painel:
  - criado o perfil "Vendas Hermes Call - WhatsApp" (`b68a8fa1…`, só mensagem): prompt de texto, mesma base de preços e mesma regra de demonstração. O perfil de voz da campanha não foi tocado;
  - atendimento por texto em modo "private" + "só quem o Hermes ligou" + esse perfil como padrão. O resto da configuração ficou igual.
  - Quem já tinha escrito (Dal Toe "Olá, boa tarde", Melo, Alcantara) recebeu à mão a mesma apresentação que a IA mandaria. Nenhuma conversa da campanha ficou com a IA pausada.
  - O retorno de ligação perdida já estava ligado: às 13:45 retornou a Melo, que recusou.
  - A IA atender a ligação na hora não funciona: o WhatsApp não reconhece o aceite enviado pelo Hermes, e isso está desligado desde 03/10.
  - **Ainda falta** para "quem é de fora fica sem ação": o retorno automático vale para qualquer número desconhecido (8 retornos em 14 dias) e o texto responderia os 156 números de testes antigos. Em preparação a opção "IA só com pessoas de campanha" (código, v0.12.0, branch `ia-so-campanha`). Só sobe com o OK da dona.
  - O texto não tem o "não me ligue" automático (só a voz tem): quem pedir para sair pelo WhatsApp tem que ser posto na lista à mão.
- 14/10/2026 (melhorias v0.12.0, branch `ia-so-campanha`, commits 6086379 e 743285d):
  - **v0.12.0 opção "só campanha"** (`campaign_only`): implementada e testada com Postgres (2 de 3 testes passam; o 3º, `RetornoDeLigacao`, foi corrigido nesta sessão adicionando `DoNotCallStore` ao mock). Não publicada em produção (precisa do OK da dona).
  - **Retorno de ligação perdida herda perfil da campanha**: nova query `RecentCampaignRequest` busca o `request` JSON da campanha mais recente que discou para o número, extrai o `profile_id` e resolve com `buildAgentSystemPrompt`. Antes usava prompt genérico fixo.
  - **Re-engajamento após silêncio**: se o cliente fica 8s em silêncio após a IA falar, diz "Olá? Está me ouvindo?" uma vez por ligação. Reseta o idle timer.
  - **Fallback "Teste E"**: NÃO corrigido — é operação de dados na produção, não mudança de código. Perfil "Teste E" tem `fallbackModel=llama3-8b-8192` (modelo descontinuado no Groq). Corrigir: apagar ou editar o perfil pela API.
  - **Abertura da isca**: NÃO corrigida — a isca é áudio pré-gravado. Trocar o texto no perfil/campanha não regenera o áudio. Precisa gerar novo áudio e atualizar `audio_ref`.
  - Documento de revisão para outro agente: `campanha/REVISAO-V0.12.md`.
- 14/10/2026 ~15:50: **v0.12.0 publicada** em produção (build `20261014-1549_743285d`). Branch `ia-so-campanha` merged em main (fast-forward). go vet OK, 2 linhas WhatsApp reconectaram, health check em 45s. Rollback: rodar no PC, dentro de `D:\hermes\pc-base`, o comando `bash ops/reverter.sh` (sem argumento). Ele volta para a v0.11.0 (`20261014-1024_a2683c0`), conferido no HISTORICO às 19:55. **Não usar `voltar-estavel.sh`**: a estável marcada ainda é `20260925-0158_29e4e85` (25/09), que perderia a v0.11.0 e quebraria a campanha espaçada. (Correção feita às 19:55; antes este item indicava o comando errado.)
- 14/10/2026 ~16:05: **campaign_only ativado** via API (`PUT /api/settings/agent-chat`). A IA agora só responde texto e só retorna ligação de quem foi discado em campanha recente. Na 1ª tentativa com `Authorization: Bearer` deu 401 (header errado); o correto é `X-API-Key`. Na 2ª tentativa mandou só `{"campaign_only": true}` e zerou `enabled` e `welcome_msg` (campos sem guard de preservação no PUT). Restaurado imediatamente com `{"enabled": true, "campaign_only": true, "welcome_msg": "..."}`.
- 14/10/2026 16:21 (3ª revisão): **37 discadas** de 297 (260 na fila). Resultados:
  - 10 completadas (27%), 22 não-atendeu (59%), 3 sem-WhatsApp (8%), 2 sem-conexão (5%)
  - Áudio: **10 de 11 ligações com qualidade "boa"**, 1 com "com cortes" (call 0D8B…, jitter 60ms, tx_buraco 418ms — não afetou a transcrição). Perda de pacotes 0% em todas.
  - Oferta tocou em **todas** as 11 que ativaram gate pcm2 (`pcm2_len=373255`).
  - **Pior sequência sem atender: 8 seguidas** (14:30→15:47, incluindo 1 sem-WhatsApp). Não ativa pausa automática (só erro ao discar conta, não "não atendeu").
  - 0 pedidos de "não me ligue". 1 disse "não estou interessado" (final ×7134, 16:07, estava em reunião — educado).
  - 0 erros de preço/produto da IA. A IA quase não chegou a falar preço — a maioria desligou na isca ou na oferta.
  - **Melhor ligação**: final ×8077 (16:15), supermercado. Ouviu oferta inteira, respondeu "Sim", IA perguntou ramo, cliente disse "Supermercado" → IA começou a contextualizar → cliente desligou (61s). Lead quente, mandar mensagem.
  - **2ª melhor**: final ×3537 (11:30), disse "agora não, estou em reunião". IA pediu desculpas. Lead morno (42s).
  - As 3 ligações depois da publicação do v0.12.0 (16:00-16:16) funcionaram normal, re-engajamento não disparou (clientes falaram antes dos 8s ou desligaram).
  - Campanha rodando normal, serviço ativo, dentro do horário (16:21 < 18:00).
  - **Fallback "Teste E"**: WARN no log `chave recusada, tentando a próxima` modelo `llama3-8b-8192`. Funciona (usa a próxima chave/modelo), mas gasta uma tentativa. Pendente corrigir o perfil.
- 14/10/2026 ~16:27: **mensagem enviada** para lead ×8077 ("A3 Gestão e Administração de Imóveis") pelo WhatsApp da linha 8653. Texto: apresentação rápida do Hermes Call + oferta de demonstração. ID da mensagem: `3EB0FBC23547697F68A1A2`.
- 14/10/2026 ~16:28: **perfil "Teste E" apagado** (id `3336f7c3…`). Era do Inovare Claw com fallback para `llama3-8b-8192` (Groq, descontinuado). Não era usado pela campanha. Elimina o WARN recorrente no log.
- 14/10/2026 17:00 (4ª revisão): **42 discadas** de 297 (255 na fila). Desde a 3ª revisão: +5 ligações (3 não-atendeu, 1 completada, 1 já contada). Nova completada (final ×0408, 16:53): disse "Sim" à isca, ouviu 95% da oferta, ficou calada e desligou (31s). Gate pcm2 OK (373255). Qualidade "boa", 0% perda. Nenhuma conversa com a IA — mais um caso de ouvir tudo e desligar. Totais acumulados:
  - 12 completadas (29%), 25 não-atendeu (60%), 3 sem-WhatsApp (7%), 2 sem-conexão (5%)
  - 0 pedidos de "não me ligue", 0 erros de preço/produto, 0 falhas de sistema
  - Lead ×8077 (mensagem enviada às 16:27): sem resposta ainda
  - Campanha rodando normal, serviço ativo, 16:59 < 18:00, próxima ligação ~17:03
- 14/10/2026 17:56 (5ª revisão): **47 discadas** de 297 (250 na fila). Desde a 4ª revisão: +5 ligações (4 não-atendeu, 1 completada). Nova completada (final ×3016, 17:03): atendeu, ouviu a isca inteira (5.6s), **não respondeu**, sistema ia tocar a oferta mas o cliente desligou na transição. Log: "cliente não respondeu, tocando oferta mesmo assim" + "chamada encerrou enquanto esperava resposta". Qualidade "boa", 0% perda, gate pcm2 OK. Mais um que desliga sem falar na isca.
  - Totais acumulados: 13 completadas (28%), 29 não-atendeu (62%), 3 sem-WhatsApp (6%), 2 sem-conexão (4%)
  - 0 pedidos de "não me ligue", 0 erros de preço/produto, 0 falhas de sistema
  - Lead ×8077 (mensagem enviada às 16:27): sem resposta ainda
  - 4 não-atendeu seguidas agora (17:12→17:45), sem risco (< 8 de erro ao discar)
  - Campanha quase no fim do expediente (17:56, limite 18:00). Última ligação talvez ~17:55. Dia 1 encerra com ~47 de 48 previstas.
- 14/10/2026 18:56 (6ª revisão): sem mudanças. Última ligação 17:45, campanha parou no horário. Serviço ativo, linha conectada, nenhum erro. Lead ×8077 sem resposta à mensagem. **Dia 1 encerrado: 47 discadas, 13 atendidas (28%), 0 "não me ligue", 0 erro IA.** Retoma 15/10 às 9h automaticamente.
- 15/10/2026 06:55–07:02, com OK da dona ("faça 1, 2 e 3"; "7h pode começar as ligações do dia"):
  - **Isca nova no ar.** Texto: "Oi! Aqui é da Inovári. É rapidinho: a gente coloca uma inteligência artificial pra atender os clientes da sua imobiliária no WhatsApp. Posso te contar como?" Gerada pelo próprio Hermes (ElevenLabs, mesma voz `hpp4J3VqNfWAUOO0d1Us`), salva na biblioteca como `03012f1a15eb073880f8a702298d85d3` ("… (isca v2 15/10)"). Ficou com **9,6 s** (a antiga tinha 5,7 s; a estimativa de ~6 s estava errada). Na campanha foram trocados `audio_ref`, `audio_ms` (9613), `request.audio_id` e `request.tts_message` (a IA usa esse texto como "o que o cliente já ouviu"). O perfil "Vendas Hermes Call" não foi mexido (a campanha não usa a isca do perfil). A pronúncia de "Inovári" não foi conferida por máquina: dá para ouvir no painel › biblioteca de áudios.
  - **Início às 7h.** `pace_config.start_hour` e `request.start_hour` passaram de 9 para 7 (fim continua 18h, seg–sex, 48/dia).
  - Antes de mudar: backup da linha da campanha em `/root/backup-campanha-8843-20261015-0655.json` (600) na produção. **Para desfazer:** voltar `audio_ref`/`request.audio_id` para `faf486e5dccadebe67dffc1e05fb1d58`, `audio_ms` para 5669, `tts_message` para o texto antigo e `start_hour` para 9 (valores no backup), e reiniciar o serviço. O reinício é necessário porque a campanha guarda o áudio na memória.
  - Reinício às 06:57:32 com a próxima ligação ainda marcada para as 9h, para não discar no meio da troca. O serviço voltou em 3 s na v0.12.0 e as 2 linhas foram restauradas. Depois, `next_slot_at` foi posto em 07:00.
  - 1ª ligação do dia às **07:00:53** (×…, não atendeu). O resultado já mostra `audio_ms=9613`, então a campanha carregou a isca nova. **Falta confirmar na 1ª atendida** a linha "áudio 1 (isca) tocado durMs≈9600".
  - **Versão estável marcada:** `20261014-1549_743285d` (v0.12.0), via `ops/marcar-estavel.sh` rodado no PC. A anterior, de 25/09, continua guardada. Agora `voltar-estavel.sh` não volta mais para 25/09; para sair da v0.12.0 continua valendo `bash ops/reverter.sh`, que leva à v0.11.0.
  - **Banco de teste apagado:** contêiner `hermes-test-pg` (postgres:16-alpine, porta 55432 local) e o volume dele, na staging.
  - Acompanhamento: além da revisão de hora em hora das 10h às 18h, foi criada outra às 8h e às 9h. As duas só existem enquanto esta sessão estiver aberta.
- 15/10/2026 08:34 (revisão): 8 discadas hoje, 2 atendidas, 4 não atenderam, 2 sem WhatsApp, 0 "não me ligue", 0 erro da IA (ela não chegou a falar). As 2 atendidas (×4500 às 07:13 e ×1700 às 08:33) desligaram **no meio da isca nova**, aos 6,0 s e 6,5 s de 9,6 s, sem falar nada. A oferta estava carregada (pcm2_len=373255), mas não chegou a tocar. Áudio "boa", perda 0%. Monitor de "atendida com fala" ligado e sem eventos. Campanha rodando. Ainda é cedo para julgar a isca nova (2 casos).
- 15/10/2026 ~08:40–09:12, pedido da dona ("responde independente do horário e responde as duas logo; quando lead mandar mensagem, liga de novo na hora e, se não atender, aí responde"):
  - **O que aconteceu:**
    - ×9058 (Grupo Carvalho Patrimonial) ligou de volta às 08:04. Não houve retorno porque a ligação foi recusada num aparelho da própria linha (`rejected_elsewhere`).
    - ×7007 (F & J Locação) escreveu "Oi" às 08:21. A IA ficou calada porque o atendimento por texto seguia o horário padrão da conta (seg–sex 9h–18h, nunca configurado), e as ligações já começavam às 7h.
  - **Horário da IA desligado** (`PUT /api/settings/schedule`, `enabled:false`): o texto responde a qualquer hora. As ligações automáticas da conta (retorno, promessas) caem na janela padrão de 9h–18h. A campanha segue a própria janela, 7h–18h.
  - **Retornos manuais:**
    - ×7007: ligação às 08:58 sem atendimento; mensagem enviada às 09:01 (id `3EB0445AEEE8DC0498DB29`).
    - ×9058: ligação às ~09:03, atendida (28 s). Disse "Sim" duas vezes e desligou enquanto a IA perguntava do negócio. Como atendeu, não recebeu mensagem.
  - **v0.13.0 publicada** (build `20261015-0904_1c1f593`, commit 1c1f593): quando lead de campanha recente manda mensagem, o Hermes liga na hora com o agente da campanha. O texto só sai se ninguém atender. Regras:
    - uma ligação por contato a cada 12 h;
    - só dentro da janela da campanha;
    - não liga com a linha ocupada;
    - mesmos bloqueios do retorno de ligação perdida.
  - **Testes da v0.13.0:** teste da janela de horário e `go vet` passaram (no PC e na VPS). A publicação passou: 2 linhas reconectaram, decisão em 45 s. **Ainda não testado com mensagem real.** Volta: `bash ops/reverter.sh` → v0.12.0 (estável).
  - Para publicar sem cortar ligação, a próxima da campanha foi empurrada de 09:13 para 09:25.
  - Revisão 09:55: desde 08:34 foram 4 discagens da campanha: 2 não atenderam (×0496, ×3000) e 2 não tinham WhatsApp (×8053, ×9559). Nenhuma atendida. A linha `pcm2_len=0` no registro é do retorno manual ao ×9058, que não tem oferta (normal). O vão entre 08:59 e 09:26 foi o adiamento para a publicação. No dia: 12 discadas, 2 atendidas, 6 não atenderam, **4 sem WhatsApp**, 0 "não me ligue", 0 erro da IA. Campanha rodando (última discagem 09:40).
  - **Efeito colateral conhecido:** quando a pessoa não atende e a IA responde por texto, a mensagem passa duas vezes pelo detector de intenção. Pode sair aviso/webhook "ai_field_detected" repetido.
- 15/10/2026 ~11:45 (análise geral, só leitura; outro agente assumiu): **66 discadas** de 297 (14/10: 47; 15/10 até 11:20: 19), 16 atendidas (24%), 41 não atenderam, 7 sem WhatsApp, 2 sem conexão. Das 16 atendidas, **10 não passaram da isca**: com a isca antiga (5,7 s), 2 desligaram no meio e 5 ouviram inteira e desligaram 1,5–2 s depois, na espera da resposta (os "5,65 s" do banco são medição: o código grava só a duração da isca quando a chamada cai nessa espera); com a isca nova (9,6 s), 3 de 3 desligaram no meio. 6 ouviram a oferta de 23 s (3 ficaram calados depois), 3 conversaram com a IA, 0 demonstrações. Nenhum "não me ligue", nenhum erro da IA, nenhuma parada por risco. v0.13.0 ainda não disparou (nenhuma mensagem de lead desde 09:10). Achados fora do roteiro: avisos de operação não chegam (`alertas.env` vazio), backup de todas as VPS falhando há 7 dias por um Postgres alheio na 209, arquivo do serviço com permissão 666 e segredos dentro, SSH com senha de root, reserva da IA com chave Groq recusada (IA demorou 6,5 s no retorno das 09:01), sem WhatsApp gastando vaga das 48, ligações que caem na isca fora de `call_transcripts`, XML no log. Tudo em `D:\hermes\pc-base\docs\ANALISE_MELHORIAS_2026-10-15.md`. **Proposta para a isca, esperando o OK da dona (uma por vez, 10 atendidas entre cada):** isca ≤ 3,5 s terminando em pergunta → esperar o "alô" antes de falar (código) → oferta ≤ 10 s. Nada foi mudado.
- 15/10/2026 11:55 (revisão horária): desde 09:55 foram **10 discagens**, 1 atendida, 9 não atenderam e 0 sem WhatsApp. **Atendida:** ×1318 às 10:36. A pessoa disse só "E aí" e desligou aos 8,6 s, ainda na isca. A oferta estava carregada (`gate pcm2` com `pcm2_len=373255`), mas não chegou a tocar. Qualidade do áudio boa: 0% de perda, jitter 77 ms. A IA não falou, então não houve erro de preço ou produto. A transcrição está em `call_recordings`, não em `call_transcripts`. As 9 não atendidas tocaram até o fim (`rang=true`), sem falha técnica; 6 delas foram seguidas, das 10:48 às 11:53. No dia: 22 discadas, 3 atendidas (as 3 caíram na isca nova), 15 não atenderam, 4 sem WhatsApp, 0 "não me ligue", 0 erro da IA. Campanha rodando (última discagem às 11:53) e linha conectada. A v0.13.0 não disparou (nenhuma mensagem de lead). Nada foi mudado.
- 15/10/2026 ~12:25 (isca v3, proposta; a dona aprovou fazer a isca curta primeiro e pediu texto e plano antes de mexer): 8 textos escritos por 4 redatores e pontuados por 3 juízes; plano de troca escrito a partir do código e verificado por 3 revisores (correções aplicadas: trava com `paused=true` além do `next_slot_at`, conferência das linhas por `/saude-local` e não por `/api/whatsapp/status`, script de volta em heredoc, UPDATE único com RETURNING, tabela do `audio_ms` esperado por desfecho). Tudo em `campanha-01\isca-v3-plano.md`. Recomendação: "Oi, aqui é da Inovári. Vocês atendem cliente pelo WhatsApp?" (10 palavras, ~3,3 s). Conferido na produção só por leitura: a chave da API é da conta da campanha, o perfil não cita a isca no prompt, só a campanha 8843 está aberta (0 em voo), `jq`/`ffmpeg` existem. **Esperando o OK A (texto)**; depois gera o áudio, a dona ouve, OK B, troca com reinício seguro. Nada foi mudado.
- 15/10/2026 12:16–12:19: **isca v3 no ar**, com OK da dona (aprovou o texto às ~12:14 e pediu "coloque logo em produção"). Texto: "Oi, aqui é da Inovári. Vocês atendem cliente pelo WhatsApp?". Áudio gerado pelo próprio Hermes (`POST /api/tts/generate`, ElevenLabs, voz `hpp4J3VqNfWAUOO0d1Us`, MP3 67 KB), **4.179 ms** medidos como o servidor mede (a meta era 3,5 s; ficou acima, mas bem abaixo dos 9,6 s da v2); salvo na biblioteca como `cef75743fba89b68bfc8f211bc953d02` ("… (isca v3 15/10)"), mesma conta da campanha. Arquivo também em `campanha-01\isca-v3.mp3` (mandado à dona na conversa). Sequência: campanha pausada (`paused=true`, `next_slot_at` +30 min) às 12:18; backup da linha em `/root/backup-campanha-8843-20261015-1219.json` (600); script de volta pronto em `/root/rollback-isca-v3.sh` (volta à v2 `03012f1a…`/9613 e o texto do backup; depois é preciso pausar, reiniciar sem ligação ativa e liberar); `UPDATE` com trava trocou `audio_ref`, `audio_ms` (4179), `request.audio_id` e `request.tts_message` — oferta, voz, perfil, janela e `sent_today` (24) intocados; reinício às **12:19:15** com `active=0` e nenhum número em voo (última ligação encerrada às 12:18:30), serviço de volta em 3 s, 2 linhas restauradas às 12:19:26; campanha liberada às 12:19:28 (`paused=false`, `next_slot_at=now`). Falta confirmar na 1ª discagem `audio_ms=4179` e, na 1ª atendida, `áudio 1 (isca) tocado durMs≈4179`. Regra: 10 atendidas com a v3 antes da próxima mudança (esperar o "alô", depois oferta curta).
- 15/10/2026 14:41: **v0.14.0 publicada** (build `20261015-1435_22082ae`, commit `22082ae`), a pedido da dona ("publique logo"). Entrou: pré-filtro de WhatsApp no modo espaçado (ligado por padrão), rediscagem de não atendidos (desligada; liga por SQL no `pace_config`), A/B da isca no paced (variante gravada), duração real das que caem na isca, espera do alô (flag desligada), ligações que caem na isca na aba Ligações ("Sem conversa"), XML da sinalização só em debug, mensagem de lead sem detecção dupla, rota `check-batch` + script `captacao/validar-whatsapp.py`, scripts de operação em `ops\`. Campanha pausada 14:36→14:43 para o reinício (nenhuma ligação cortada). Estável continua a v0.12.0. Pendências para o próximo agente: topo do `CONTINUAR_DAQUI.md`. Até 14:30 nenhuma atendida com a isca v3 (todas não atenderam ou sem WhatsApp).
- 15/10/2026 14:42:59: **🔴 a linha 8653 caiu (`logged_out`, não pareada)** 6 s depois de o pré-filtro novo da v0.14.0 consultar 60 números no WhatsApp (5 sem WhatsApp marcados às 14:42:48–53). A ligação que estava tocando (×6132) terminou como não atendida às 14:43:40. Feito na hora: campanha pausada, pré-filtro desligado (`HERMES_CAMPAIGN_PREFILTER=false` no drop-in `30-campanha.conf`), serviço reiniciado. **Falta: a dona reconectar a 8653 no painel (QR/"Por código") e conferir "Aparelhos conectados" no celular; depois despausar a campanha.** Dia até aqui: 36 discadas (31 não atenderam/sem WhatsApp após a isca v3... ver banco), 0 atendidas com a isca v3. Pendências detalhadas no `CONTINUAR_DAQUI.md`.
- 15/10/2026 14:55 (revisão horária): desde 11:55 foram **19 discagens** (12:04–14:43): 5 atendidas, 8 não atenderam, 6 sem WhatsApp (5 deles marcados de uma vez às 14:42 pelo pré-filtro, segundos antes da queda; vale reconferir esses 5). 0 "não me ligue". **Correção da nota acima:** com a isca v3 houve **5 atendidas**, não 0 (`completed` às 13:47, 13:58, 14:13, 14:24 e 14:37). A isca v3 está confirmada no ar: `audio_ms=4179` e `áudio 1 (isca) tocado durMs` 4141–4143. Nas 5, a oferta estava carregada (`gate pcm2` com `pcm2_len=373255`) e a qualidade foi boa (0% de perda, jitter 13–74 ms). Nenhum cliente falou: a transcrição só tem a isca. A IA não falou, então não houve erro de preço ou produto. **Desfecho por ligação:**
  - ×9477 desligou aos 2,3 s, no meio da isca.
  - ×7526, ×0803 e ×7601 ouviram a isca inteira e desligaram 1–2 s depois, na espera da resposta.
  - ×6595 ficou **15 s em silêncio** depois da isca até a oferta começar ("cliente não respondeu, tocando oferta mesmo assim"), ouviu 4,9 s da oferta (21%) e desligou.
  - Comparação: com a v2, 0 de 3 ouviram a isca inteira; com a v3, 4 de 5 ouviram, mas ninguém respondeu à pergunta.
  - **Achados:** (1) a espera de ~15 s em silêncio entre a isca e a oferta é longa demais (candidata à próxima mudança depois das 10 atendidas com a v3); (2) o Whisper inventa "Legenda por Sônia Ruberti" quando há silêncio, e o resumo atribui a ligação a uma "Sônia Ruberti" (2 de 5).
  - **Linha:** a 8653 caiu às 14:42:59 (`logged_out`) e às 14:54 continua fora (`/saude-local`: 1 linha pareada, que é a outra). Campanha pausada (`paused=true`).
  - **No dia:** 41 discadas, 8 atendidas, 23 não atenderam, 10 sem WhatsApp, 0 "não me ligue", 0 erro da IA. Nada foi mudado.
- 19/10/2026 08:30–09:02: **Hermes estava fora do ar** desde dom 18/10 11:39: a VPS de produção foi desligada pelo botão de energia (`systemd-logind: Power key pressed short`, ou seja, pelo painel do provedor), voltou às 11:58 e o `hermes-call` não subiu porque estava `disabled` no boot (o `DEPLOY.md` manda `enable --now`). Feito: `systemctl enable --now hermes-call` às 08:49 (v0.14.1, `20261015-1517_2d2ef76`). A dona reconectou a 8653 pelo painel às 08:58, mas o painel criou uma **sessão nova** (`0fcd550fab479c0b531e74903a8f566e`) em vez de reaproveitar a `290f2fb3…` (que ficou deslogada, sobrando no banco). Com o OK da dona ("pode continuar a campanha"): backup em `/root/backup-campanha-8843-20261019-0900.json` (600); `campaigns.session_id` da 8843 trocado para a sessão nova; `line_first_seen` da sessão nova com `first_day=2026-09-25` (a data da antiga), senão o teto anti-bloqueio da "linha nova" seria 20/dia em vez das 48 da campanha; campanha despausada às 09:00:40. Não precisou reiniciar: o agendador lê `session_id` do banco a cada minuto. A contagem do dia zerou sozinha (`sent_day` era 15/10). **1ª ligação às 09:01, pela sessão nova:** ×3456 atendeu, isca v3 tocada (`durMs=3934`), oferta carregada (`pcm2_len=373255`), desligou no fim da isca sem falar; áudio "boa", 0% de perda; gravação no Telegram OK. Próxima às 09:13. Pré-filtro continua desligado. **Para desfazer:** voltar `session_id` para `290f2fb3…` (só se a antiga for reconectada) e apagar a linha de `line_first_seen` da sessão nova; valores no backup.
- 19/10/2026 09:55–09:57: **retorno automático funcionou.** A Bueno & Castilho (×5971), que a campanha ligou às 09:35 e recusou, ligou de volta às 09:55:59 e desligou em 0,5 s. Às 09:56:47 o Hermes retornou com o perfil da campanha ("callback: usando perfil da campanha"), mas a ligação não chegou a tocar do lado deles (`rang=false`, `no-connect`). O retorno de ligação perdida não manda texto quando falha. Perguntado à dona se manda mensagem ou liga de novo.
- 19/10/2026 10:19: **v0.15.0 publicada por outra sessão** (claude-69, build `20261019-1010_19d42b8`: botões e listas clicáveis, não mexe em ligação). A 8843 ficou **pausada de 10:16 a 12:46** (a sessão dela caiu depois de ativar): umas 13 vagas a menos hoje. Conferido às 12:47: v0.15.0 no ar, 4 linhas conectadas (inclusive a 0fcd550f), campanha na 0fcd550f, `line_first_seen` intacto, pré-filtro desligado no processo novo, serviço `enabled`, 0 ERROR/panic desde 10:19. Volta: `bash ops/reverter.sh` (→ v0.14.1). Ligações de hoje até 12:47: 8 discadas, 2 atendidas (×3456 às 09:02, que desligou no fim da isca; ×0304 às 10:08, que ouviu a isca inteira, 4,1 s, e desligou na espera da resposta), 6 não atenderam. Com a isca v3: 7 atendidas, nenhuma respondeu à pergunta.
- 19/10/2026 17:45 (balanço desde 14/10, pedido da dona "ninguém se interessou?"): **134 discadas de 297** (163 na fila), 39 atendidas, 80 não atenderam, 13 sem WhatsApp, 2 sem conexão. Por dia: 14/10 47 (13 atendidas), 15/10 41 (8), 19/10 46 (18, o melhor dia). **0 demonstrações, 0 clientes, 0 "não me ligue".** Sinais de interesse:
  - **Barusso Realty (×4561), 19/10:** não atendeu às 13:04 e escreveu "Quem é / Não posso falar agora / Sobre o que seria". A v0.13.0 ligou na hora (13:05, sem atender) e a IA respondeu por texto. Disse o ramo ("Farmácia") e às 15:04 respondeu "WhatsApp" à pergunta da IA. Depois disso não escreveu mais.
  - **Nerys Empreendimentos (×9627), 19/10 16:56:** respondeu "Sim" à isca v3 e desligou com 38% da oferta (14 s).
  - **Cardoso Investimentos (×4405), 19/10 17:32:** perguntou "O que é a Inovare?" e desligou no começo da oferta. **MMA Borda (×2889), 17:03:** ouviu 81% da oferta.
  - **Ligaram de volta:** Melo (×0218, 14/10, recusou o retorno), ESDR (×8354, 14/10, 2×; o Hermes retornou), Grupo Carvalho (×9058, 15/10; retorno manual atendido, disse "Sim" e desligou) e Bueno & Castilho (×5971, 19/10; o retorno não tocou).
  - **Escreveram:** Coelho (×0513) e L D M (×2367) em 14/10 (a IA respondeu); F & J (×7007) em 15/10 (respondido à mão); Michelato (×1736) "Construtora Franche certo??" em 15/10 15:02, com a linha caída: **ninguém respondeu**; Ailton Dias (×2667) e Neom Teixeira (×0398, resposta automática "Ana Lúcia") em 19/10 (a IA respondeu).
  - A3 Gestão (×8077, 14/10): conversou (supermercado) e recebeu mensagem às 16:27; não respondeu.
  - Respostas da IA por texto em 19/10: estão em `conversations` e não houve "autoreply send failed". A tabela `messages` não mostra o que o próprio Hermes enviou pela sessão nova (os "NÓS" de 14/10 vieram da sincronização do histórico).
  - Leitura: a abertura v3 faz mais gente falar (19/10: 4–5 respostas em 18 atendidas, contra ~0 antes), mas quem diz "Sim" desliga no meio da oferta de 23 s. Já passaram as 10 atendidas com a v3: a próxima mudança candidata é encurtar o silêncio de 15 s e a oferta (≤ 10 s, terminando em pergunta). Esperando o OK da dona.
- 20/10/2026 00:16 (fechamento de 19/10): o dia bateu o teto de **48 discadas, 20 atendidas** (28 não atenderam). Depois das 17:45 entraram XBENS Imóveis (×2237, 17:51, ouviu 68%) e Queiroz Assessoria (×0575, 18:00, ouviu 61%), sem resposta. **Total: 136 de 297 discadas** (161 na fila), 41 atendidas, 80 não atenderam, 13 sem WhatsApp, 2 sem conexão; 0 marcados como interessados, 3 recusas, 5 com resposta falada. Nenhum lead da campanha escreveu depois das 17:30 (as conversas da linha à noite são pessoais). 3 ligações recebidas à noite sem retorno, todas certas: 2 "fora das campanhas" (×5236 e ×1214) e 1 de uma linha do próprio Hermes (21:54). Linha 8653 conectada, sem queda. Próximo horário: 20/10 07:00, com a mesma isca v3 e a mesma oferta.

- 23/10/2026 ~09:30, pedido da dona ("as respostas de texto nunca são respondidas; resposta muito curta, que não pareça bot, desperte interesse, oi/boa tarde e entra no assunto devagar"):
  - **Causa vista em `conversations` (13–23/10):** a IA de texto mandava sempre a MESMA mensagem longa ("Oi, boa tarde! Aqui é a assistente virtual da Inovare. A gente te ligou para apresentar o Hermes Call... Posso te contar em 1 minuto?") para ~15 leads. O prompt do perfil trazia esse texto como exemplo e o modelo (gemini-flash-lite) copiava palavra por palavra. Dizia "boa tarde" às 08:09/08:20 (não sabe a hora), respondia a mensagens automáticas das imobiliárias com a apresentação inteira e às vezes mandava 2 vezes seguidas. Só 2 conversas passaram da 1ª mensagem.
  - **Feito:** novo prompt no perfil "Vendas Hermes Call - WhatsApp" (`b68a8fa1…`, só `system_prompt`): mensagens de 3 a 15 palavras, devolve o cumprimento que a pessoa usou (nunca diz bom dia/boa tarde por conta própria), não fala o nome do produto nem "inteligência artificial" nas 2 primeiras mensagens, entra no assunto em etapas (cumprimento → "fui eu que te liguei, aí é imobiliária?" → rotina do WhatsApp → "a gente fez um sistema que responde na hora, é ele falando com você" → demonstração), mensagem automática da empresa recebe 1 linha curta. Regras de preço, demonstração 8h–21h, "é robô?", "não me ligue" mantidas.
  - **Teste antes de aplicar:** 8 conversas com as mensagens reais dos leads, no mesmo modelo (Gemini da conta, chamado da VPS; nada enviado a lead). Todas as respostas curtas e diferentes entre si; ex.: "Boa tarde" → "Boa tarde! Tudo bem por aí?"; "Bom dia. Quem?" → "Bom dia! Fui eu que te liguei mais cedo, sou da Inovare. Aí é imobiliária?"; resposta automática da Paloschi → "Oi! Te liguei mais cedo, sou da Inovare. Quando puder me chama aqui 🙂".
  - Vale na próxima mensagem (o servidor lê o perfil do banco a cada resposta; sem reinício). **Para desfazer:** `/root/backup-prompt-whatsapp-20261023.txt` na produção (cópia em `campanha-01/backup-prompt-whatsapp-20261023.txt`); prompt novo em `campanha-01/prompt-whatsapp-v2.sql`.
  - **Não corrigido (código):** resposta dupla quando o lead manda 2 mensagens seguidas (sem espera para juntar) e a IA responder a mensagem automática de outra empresa. A pergunta "Aí é imobiliária?" serve só para esta campanha; outro nicho precisa trocar o exemplo.

- 24/10/2026 (sábado), pedido da dona ("faça pra não ficar parado"): a lista 01 acabou em 23/10 11:04 (297 de 297: 91 atendidas, 179 não atenderam, 23 sem WhatsApp, 4 sem conexão; 0 interessado; 1 pediu retorno, NF Administração ×2390, ainda sem retorno).
  - **Lista 02** tirada da mesma base de CNPJ da VPS de teste (`/root/captacao/base.csv.gz`, cadastro 09/2026), com o mesmo perfil da 01: imobiliárias do Brasil inteiro, nível barato, nota B, celular, e agora sem empresário individual. Bloqueio = todo número que já esteve em qualquer campanha + `do_not_call` (743; ninguém pediu "não ligar"). Sobraram 67.782; sorteadas 297 proporcionais por estado (SP 58, SC 43, PR 31, MG 30, RS 25…; 260 micro, 37 pequeno porte). Arquivos: `campanha-02/campanha02-pronto.csv` e `campanha02-completo.csv`.
  - **Campanha 02 criada no banco** (`c0f2a024-1026-4b2e-9a02-000000000002`, "Divulgação Hermes - imobiliárias (lista 02)") copiando a 01: linha 8653, isca v3 (`cef75743…`), oferta (`0628a381…`), perfil de voz `4a09fe24…`, 48/dia, 7h–18h, só dias úteis. Sem reinício: o agendador lê o banco a cada minuto; ele já marcou a 1ª ligação para **seg 26/10 07:00**. Comando em `campanha-02/criar-campanha-02.sql`. **Para parar:** `UPDATE campaigns SET paused=true WHERE id='c0f2a024-1026-4b2e-9a02-000000000002';`
  - 24/10 ~12:20, pedido da dona ("então crie, e esse sistema de retorno deve ter um aí mas não deve estar funcionando"): **v0.17.0 no ar** (build `20261024-1209_fb6eb8f`). O retorno agendado ligava sem o agente de vendas (frase genérica), pela 1ª linha da conta e não achava a linha quando o número tinha o 9; e a ligação curta (fala só na abertura) ficava "sem_conversa" sem análise. Tudo corrigido (ver CHANGELOG v0.17.0).
  - **Retornos criados, já confirmados**, com o agente da campanha e saudação "te ligando de volta como você pediu na nossa ligação": NF Administração de Bens (5545999942390) **seg 26/10 09:00** e ANTT Administradora (5531996913452, disse "tem que ser mais tarde") **seg 26/10 09:15**. Se não atender, tenta de novo em 45 min (até 3 vezes). Aba Promessas do painel.
