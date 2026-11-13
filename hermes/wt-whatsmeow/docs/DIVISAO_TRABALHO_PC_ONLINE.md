# Divisão de trabalho: agente do PC × agente online (nuvem)

> Combinado com a dona em 04/10/2026. **Leia antes de mexer em qualquer coisa.**
> Ramo de trabalho comum: **`pc/v0.8.0`**. Ele contém todo o v0.8.0 da nuvem (`claude/gallant-mendel-f1xney`) mais as
> correções feitas no PC depois da revisão (`docs/REVISAO_RAMO_ONLINE_2026-10-04.md`).
> **A produção continua na v0.7.0 (`af7413e`).** Nada do v0.8.0 foi publicado.

## 1. Quem faz o quê

| | Agente ONLINE (nuvem) | Agente do PC |
|---|---|---|
| Acesso | só o repositório (sem VPS, sem banco de produção, sem ligação real) | VPS de produção e bancada, banco, logs, ligações reais, publicação |
| Faz | código, testes de unidade e de banco descartável, CI, painel, documentação, revisão | compila na VPS, instala na **bancada**, roda **ensaios IA × IA**, confere logs/banco, publica com `ops/publicar.sh`, combina ligação com a dona |
| Nunca faz | publicar, mexer na `main`, mudar segredos, apagar teste de `docs/REGRESSOES_LIGACAO.md` | escrever feature grande sem o online (fica com as partes que precisam da VPS) |

**Fluxo:**
1. O online trabalha **sempre em ramo a partir de `pc/v0.8.0`**, com commits pequenos e testes.
2. Quando precisar de algo que só o PC faz (testar na bancada, ver log, consultar banco, ligação real), escreve o pedido
   em **`docs/PEDIDOS_AO_PC.md`** (uma linha por pedido: data, o que testar, como saber se passou) e avisa a dona.
3. O PC junta o ramo do online em `pc/v0.8.0`, compila na VPS, instala **só na bancada**, roda o ensaio e grava o
   resultado em **`docs/ensaios/AAAA-MM-DD_HHMM.md`** (tempos, transcrições, cortes, erros), e marca o pedido como feito.
4. Quando os ensaios estiverem bons, o PC publica (com a volta pronta) e marca a ligação de validação com a dona.

## 2. O que o PC já fez em 04/10 (não refazer)

- **Revisão** do v0.8.0: `docs/REVISAO_RAMO_ONLINE_2026-10-04.md`. O banco foi conferido na produção e as migrações são seguras.
- **Configuração na produção** (sem código, com backup em `/opt/hermes-call/releases/config-backups/`):
  - agente padrão de ligação = "Vendas Hermes Call", com a voz, o fundo e o modelo do antigo "Teste E";
  - fim de fala `vad_silence_ms` 800 → 600.
- **Janela de ensaio IA × IA:** `ops/vps/ensaio.sh` (instalado na VPS em `/opt/hermes-call/ops/ensaio.sh`).
  - A **bancada** (linha 8288, versão em teste) é a **vendedora**.
  - A **produção** (linha 8653) vira **cliente** ("Cliente Simulado (ensaio)") só para ligações do 8288, sem som de fundo e
    sem palavras de apoio.
  - Desliga sozinha em 30 min.
  - Uso: `ensaio.sh completo` (liga, espera, relatório, desliga).
- **Bancada** com os agentes e as chaves da produção e com a configuração de voz igual à da dona (interrupção, palavras
  de apoio, fundo, 600 ms).
- **Correções commitadas em `pc/v0.8.0`.** Confira no `git log` antes de começar; as frentes do PC podem ter
  acrescentado mais depois deste texto.
  - Voz:
    - marcar horário só gasta a vez se gravou;
    - lembrete só depois de a dona confirmar;
    - aviso da marcação sem deixar a IA muda;
    - transcrição antecipada com prazo de 3 s e cancelada quando é superada;
    - saúde da ligação em segundo plano;
    - "pare de me ligar" não é lead quente;
    - recepcionista não apaga o roteiro próprio.
  - Publicação:
    - **a volta de versão não se desfaz mais** (o crítico);
    - bancada só com `PUBLICAR_COM_BANCADA=1`, com o aceite conferido antes;
    - conferência de pânico depois da troca;
    - conferência de linhas diz qual linha caiu.

## 3. ACHADO PRINCIPAL: o aceite da ligação recebida

Ensaio de 04/10 14:12 (`docs/ensaios/` vai ter o detalhe):
- Numa ligação **Hermes → Hermes**, quem liga **nunca recebe o `accept`**: o WhatsApp não reconhece o aceite enviado pelo Hermes.
- Por isso a campanha não chega a "remote accepted", **não toca isca nem oferta** e não carrega a persona.
- Mesmo assim o áudio passa pelo relay, e a IA responde com o prompt padrão de assistente.
- Com o v0.8.0 (`HoldUntilAccepted`), a IA de quem liga ficaria **surda**.

**Consertar o aceite destrava duas coisas:** o atendimento automático de clientes (hoje só toca e depois vem o retorno)
e o ensaio IA × IA completo.

### Tarefas do ONLINE (código)

- **A1. Duas chaves só de teste** (se as frentes do PC ainda não tiverem feito; conferir no `git log`):
  - `HERMES_VOICE_ESPERA_ACEITE=false` não trava a escuta;
  - `HERMES_TESTE_ACEITE_POR_RELAY=true` trata "relay conectado + áudio chegando por ~1 s sem accept/reject/terminate"
    como aceito, só na ligação que o Hermes FAZ, com log bem visível;
  - as duas desligadas por padrão e documentadas como "só bancada".
- **A2. Variantes do aceite atrás de chave** (`HERMES_ACEITE_VARIANTE=1..N`), a partir de
  `docs/REGRESSOES_LIGACAO.md` §5 e `internal/voip/signaling/signaling_build.go`. Hipóteses:
  1. mandar o `<accept>` para o APARELHO exato de quem liga (`peerJid` com device), igual ao `<preaccept>`, e não para o `CleanJID`;
  2. anunciar `audio rate=8000` e `16000` e incluir `<capability>` como na oferta;
  3. depois do accept, mandar `transport` (tipo 1), `mute_v2` e o recibo, como o Hermes faz quando é ele que liga;
  4. combinações.

  Cada variante tem que ter teste de unidade do XML gerado. O PC testa cada uma na bancada e registra o resultado.
- **A3. Comparar com um aceite de verdade.**
  - O PC vai capturar, com o `call_trace` do v0.8.0, um celular real ATENDENDO uma ligação do Hermes
    (depende de a dona atender num celular; pedido feito em 04/10).
  - Quando o arquivo aparecer em `docs/ensaios/`, comparar campo a campo com o que o Hermes manda e ajustar a variante.

### Outras tarefas do ONLINE

Itens da revisão, se ainda não estiverem no `git log` de `pc/v0.8.0`:
- **Voz:**
  - lead quente: entrar pelo card arma a ponte silenciosa (a IA cala) e sair não derruba a ligação;
  - memória da ligação: DDD+número normalizado, últimos 90 dias e busca em paralelo, nada síncrono no tratador de eventos;
  - **filtro de confiança do Whisper:** `verbose_json`, descartar `no_speech_prob` alto / `avg_logprob` baixo /
    `compression_ratio` alto, e letras de outros idiomas. Caso real: "Ég komstu hjá hana." numa ligação da dona.
- **Publicação e painel:**
  - CSV de exportar contatos (telefone como texto e proteção contra fórmula);
  - `internal/testpg` recusa banco que não seja de teste;
  - Chatwoot busca só nas sessões do usuário;
  - tela de configuração mascara usuário e senha em URLs;
  - teste do catálogo de variáveis tolera CRLF;
  - painel: não reenviar `default_profile_id`/`voice_profile_id` velhos e não salvar a "API Key Manual" do agente;
  - CI com `govulncheck` em versão fixa e `permissions: contents: read`.
- **Latência** (meta ≤ 2,5 s; o ensaio deu 2,3 s com 600 ms): 1ª voz da ElevenLabs mais lenta; avaliar Groq/qwen só como reserva.
- **Ensaio IA × IA (o que ainda falta):** as duas IAs se interrompiam (barulho virando fala). O lado cliente agora vai
  sem fundo; se continuar, revisar o barge-in e o eco para ligação Hermes × Hermes.

## 4. O que o PC faz a seguir (em ordem)

1. Juntar o que as frentes locais terminarem em `pc/v0.8.0`, compilar na VPS (`ops/publicar.sh --so-compilar`) e
   instalar na bancada (`/root/lab-bancada.sh preparar <ID>` com `PUBLICAR_COM_BANCADA` desligado), com as chaves de teste no `bancada.env`.
2. Rodar ensaios (`ensaio.sh completo`) e gravar em `docs/ensaios/`.
3. Capturar o aceite real (depende da dona) e testar as variantes do online.
4. Publicar quando os ensaios estiverem bons, e fazer a ligação de validação com a dona.

## 5. Avisos importantes

- **O repositório `Emersonjosielmrx/hermes-call` ficou PÚBLICO** (conferido em 04/10) e o histórico tem senhas e tokens
  antigos. Só a dona pode deixar privado e trocar os segredos (item S1 do plano). Não pôr segredo nem telefone
  completo em arquivo novo.
- **Não seguir** os passos "juntar na `main` e publicar" da passagem da nuvem de 04/10 (ver aviso no `CONTINUAR_DAQUI.md`).
- **Antes de mexer na voz:** `docs/REGRESSOES_LIGACAO.md`. Testes listados lá não podem ser apagados nem afrouxados.
