# Fish Audio — como operar (voz do narrador do "Todo Mundo Odeia o Chris")

Atualizado em 19/11/2026 (madrugada). A dona ouviu e disse: "realmente é outro nível de clone de voz".

> **19/11 — FISH É O PADRÃO DE VOZ (dona).** Ordem em todo vídeo, no `anime_tts.preparar_clone`:
> 1. **Fish Speech na GPU do Kaggle** (`_narrar_fish_nuvem` -> `bin/fish_nuvem.py`), para longos e Shorts. Copia a
>    `referencia_fish.wav/.txt` da pasta da voz no Drive (`manhwa-drive:colab_recap/vozes/<voz>/`). Sem RVC por cima.
>    O trabalhador da VPS instala (Py3.11 + torch/torchaudio **2.4.1 travados** + portaudio) e grava
>    `"fish": true` no `vivo_<conta>.json`.
> 2. **Fish online** (Shorts do PC1), com a voz por nicho (`voz_por_nicho.json`: esportes = Neymar,
>    curiosidades = Iberê, resto = narrador do Chris). Fala de **personagem** usa a voz DELE no site
>    (`vozes_site.json`, 48 vozes); personagem sem voz no site segue no RVC dele.
> 3. Senão: Kitten 2 (GPU) / **p3 com mistura** (PCs).
>
> **Referências no Drive** (`referencia_fish.origem` diz de onde veio):
> - `original:...` = fala real (melhor). 15 narradores parceiros (momo, mike, guugou, mangaticos, mattz, porao, iki,
>   doinsuka...) + ~30 vozes dos `videos-backup/amostras_voz/referencias/` (feitas no STI, `D:\tmp\sti_referencias.py`).
> - `site:<id>` = PONTE gerada com a voz pública do site, até achar o original (`fazer_referencia.py --site`).
> Fazer nova: `python fazer_referencia.py <audio_original> <pasta> <voz> --sobe` ou `--site <id> <voz> --sobe`.
>
> **Técnicas no Fish:** ENTRAM nivelar volume (-20 LUFS) + efeito da voz (`_acabamento_fish`), margem final, abertura
> com trecho original. FICAM FORA humanizar, curva do locutor, climas, RVC (o Fish já tem o jeito do narrador).
>
> **Longos no Kaggle:** as contas de papel "longo" estão banidas; a central empresta até `curto_pro_longo_max` (2)
> contas de curto para longo (`vps_central.py`, 19/11).
>
> **⚠️ LICENÇA:** plano grátis do site = sem uso comercial; Fish Speech 1.5 (pesos) = CC-BY-NC-SA 4.0 (não comercial).
> Decisão da dona (assinar o Plus libera o comercial no site).
>
> **Logins do pool:** `logar_pool_noite.py` tenta 1 conta a cada 10 min pelo IP dela e para em verificação.
> **Relatório:** `python relatorio_fish.py` -> `RELATORIO_MANHA.md`.

> **18/11 noite — caminho RÁPIDO por HTTP: `fish_http.py` + `fabrica_fish.py` + `sessoes_fish.py`.** A geração
> chama a API do Fish direto, sem clicar na página. O Chrome só fabrica o token do reCAPTCHA e fica aberto
> ("quente") entre um vídeo e outro. **Saldo e escolha de conta saem SEM Chrome.** Medido: com a fábrica quente,
> ~2 s por fala e 3 falas em paralelo; um roteiro de 6 falas fica pronto em ~10 s. Com `preaquecer()` chamado no
> início do vídeo, a narração não espera nem o 1º Chrome. Tudo na seção **9**. O `fish_audio.py` (clicar na tela)
> continua existindo como reserva.

> **18/11 noite — NA PRODUÇÃO (Shorts do PC1).** Todo Short narrado pelo `anime_auto` tenta primeiro a voz online
> do Fish. Sem crédito ou com erro, cai sozinho no **p3 com as técnicas**, sem travar o vídeo.
> - Como funciona: `anime_auto.py` põe `VOZ_ONLINE=fish` no ambiente do Short e chama `fish_lote.preaquecer()`,
>   que já abre o Chrome quente. Depois `anime_tts._narrar_online()`, no começo do `preparar_clone`, chama
>   `fish_lote.gerar()`. Cada `audio_N.wav` que sai do Fish fica pronto e o laço do p3 pula essa frase.
> - Nas frases do Fish:
>   - Não tem RVC por cima, porque ele já é a voz.
>   - O tempo de cada palavra vai para o `audio_N.wav.words.json`, para a legenda cinética.
>   - A marca `_voz_online.json` fica na pasta do áudio.
> - **Só no PC1:** precisa do cofre e do `creditos.json`. Em outra máquina o `fish_lote.disponivel()` dá falso e
>   tudo segue no p3. **No Kaggle não roda:** a variável não vai no pedido, e a conta sairia de outro IP.
> - **Desligar:** `SHORTS_VOZ_ONLINE=0` desliga nos Shorts; `FISH_ONLINE=0` desliga tudo.
> - **Escolha de conta:** pelo `creditos.json`, sem abrir nenhuma conta. Fica a de mais crédito, e troca quando
>   acaba. Para ver o saldo: `python creditos.py`.
> - **Teste em 18/11:** um Short real de 6 frases saiu 6/6 online, com 5/6 frases com o tempo das palavras.
>   Prévia em `amostras_voz\fish_audio_site_1811\previa_short_animais_estranhos_FISH.mp4`.
> - **Próximo passo (não feito):** no Short que vai para o Kaggle, narrar aqui antes de enviar e mandar os
>   `audio_N.wav` prontos. Para isso o PC1 precisa saber o texto final exato de cada frase (com mascote, falas de
>   personagem e abertura).

## 1. O que é e por que é melhor que o nosso RVC

- **O que é:** o Fish Audio (fish.audio) gera a fala direto do texto e imita a voz de referência inteira: timbre,
  ritmo, pausas e ênfase.
- **Por que o RVC fica pior:** o nosso RVC troca só o timbre de uma voz base (Francisca ou Kokoro). Por isso o
  clone RVC tem a voz certa, mas o jeito de falar errado.
- **Voz pública usada:** **NARRADOR DO TODO MUNDO ODEIA O CHRIS** (criada por "Estudante 004"), com 3,78 milhões de
  usos. É a voz dos Shorts virais de "tipos de...".
  - Link: https://fish.audio/pt/m/4b215a58407c4def88e0892def6421b2
  - ID da voz: `4b215a58407c4def88e0892def6421b2`
- **Modelo do site:** Fish Audio **Drama 3**, o mais recente.

## 2. Pool de contas (cada conta com IP próprio, igual ao Kaggle)

Montado em 18/11 com `pool_fish.py`.
- **22 contas não-Kaggle** do cofre, cada uma com um IP Webshare **exclusivo**, gravado no cofre no campo
  `fish_proxy = rnprmtfo-N`.
- Os IPs `rnprmtfo-N` (1 a 100) são da mesma conta Webshare. Os que o Kaggle usa **nunca** são reusados aqui; o
  script calcula os livres.
- Comandos:
  - `pool_fish.py status`: mostra o pool e os IPs livres.
  - `pool_fish.py montar N`: põe mais N contas no pool.
- `fish_audio.py` e `login_fish.py` abrem cada conta pela **ponte** do IP dela
  (`ponte_proxy_fixo.py N 18500+N`). Conferido: a casa sai por 191.36.x e a conta do pool por outro IP
  (ex.: 85.198.45.21).

### Login de cada conta no Fish Audio (uma vez por conta)

| Conta | Situação |
|---|---|
| vendeafiliados3 | **logada** (manual com o script, 18/11) |
| jogoscomia | **logada** (pelo `login_fish.py`, 18/11) |
| as outras 20 | **sem login** |

**O que funcionou nas 2:** Login com Google, com **clique de MOUSE no centro do ícone do Google**
(`page.mouse.click(x, y)`). Clicar no elemento não funciona, porque o site ignora. O Google abre na **mesma aba**:
escolher a conta, Continue, volta logado.

**O que trava (18/11):** nas tentativas seguintes, pelo navegador controlado por script e pelo IP Webshare:
- O clique no Google não abre a tela do Google.
- O "Continuar com e-mail" fica girando e não avança.

O site carrega o reCAPTCHA invisível, então o mais provável é uma **verificação de robô por trás**. Pela regra da
casa, verificação de robô em conta nova = **parar e avisar a dona**, sem tentar contornar.

**Como logar as que faltam (com a dona):**
1. `python login_fish.py <email>` abre a conta pelo IP dela.
2. Se parar, a dona faz o login à mão nessa janela, com o mesmo IP. A janela do cofre fica fora da tela: trazer para
   a frente.
3. Depois, `python login_fish.py <email>` de novo mostra `JÁ LOGADO`, e o script marca `fish_logado` no cofre.

**Conferir login (o jeito confiável):** abrir `https://fish.audio/pt/app/billing/` e ver se aparecem "My Team" e os
créditos restantes.

**Alarme falso que já aconteceu:** procurar "recaptcha" no **HTML** sempre dá positivo, porque o script do reCAPTCHA
vem na página. Procurar só no **texto visível**.

## 3. Conta (regras de segurança)

| Item | Valor |
|---|---|
| Conta do cofre | **vendeafiliados3@gmail.com** (porta 9763), entra com "Login com Google" |
| Plano | Grátis |
| Registro | No cofre: `usos.fish_audio` |

- **Nunca use conta do Kaggle aqui.** O script confere com `cofre.saida_kaggle()` e recusa se for.
  - Por quê: conta Google do Kaggle aparecendo em outro serviço já causou banimento (09/11 e 14/11). Veja
    `kaggle_gerente\INCIDENTE_BANIMENTO_02NOV.md`.
- **Não faça rodízio de várias contas grátis** para somar cota. É contra os termos do site e repete o risco de
  banimento. *(18/11 noite: a dona pediu o rodízio com controle de crédito por conta; ele existe no
  `fish_http.gerar_frases`, cada conta no próprio IP. O risco de banimento continua valendo — ver seção 9.)*
- **Captcha, cobrança ou tela de login:** o script **para** e deixa um print na pasta de saída
  (`_CAPTCHA.png`, `_SEM_CREDITO.png`, `_PRECISA_LOGIN.png`). Resolva à mão.
- **Consentimento:** a voz é do dublador. Para publicar, vale a mesma regra das outras vozes clonadas, que é pedir
  consentimento.

## 4. Cota e preço (medidos em 18/11/2026)

**Gasto: 1 crédito por caractere.** O site gera 2 versões por fala, mas cobra só uma. Medido: 2 falas de 90 + 52
caracteres gastaram 142 créditos.

| Plano | Preço | Créditos por mês | Rende |
|---|---|---|---|
| **Grátis** (atual) | R$ 0, sem cartão | 8.000 (renova dia 18) | uns **17 Shorts** de 30 s (~450 caracteres cada) |
| **Plus** | R$ 29,16 por mês no anual com 50% no 1º ano (R$ 349,95 por ano); R$ 39,95 no mensal | 250.000 | uns **550 Shorts** |
| **Pro** | R$ 199,58 por mês no anual (R$ 2.395 por ano) | 2.000.000 | uns 4.400 Shorts |

- **Grátis:** até 500 caracteres por geração. O script corta o texto em frases de até 480.
- **Créditos restantes:** https://fish.audio/pt/app/billing/

## 5. Tempo

| Onde | Tempo |
|---|---|
| Site, por fala | **~7,5 s** para gerar uns 3 s de áudio (medido pelo script) |
| Short de 10 falas | uns **75 s**, mais 15 s para abrir o Chrome |

- Não usa GPU nossa nem CPU do PC1: a geração roda no servidor deles. O PC só abre o Chrome por uns minutos.
- Comparado com os motores locais na GPU do Kaggle (Short de 10 falas):

| Motor | Tempo |
|---|---|
| Supertonic, Edge, Kokoro, Piper | 10 a 20 s |
| Kitten 2 | ~90 s |
| Fish Audio (site) | ~90 s |

## 6. Como usar

O script fica em `D:\hipercool-materiais\comum\fish_audio\fish_audio.py` e roda com o python da produção.

```
set PY=D:\recapd-ambientes\producao\venv\Scripts\python.exe
cd /d D:\hipercool-materiais\comum\fish_audio

:: falas na linha de comando
%PY% -X utf8 fish_audio.py "Toda vez que a família se reúne, alguns tipos aparecem." "Primeiro, temos o tio do pavê." -o D:\tmp\minha_narracao

:: roteiro inteiro (uma fala por linha)
%PY% -X utf8 fish_audio.py -f roteiro.txt -o D:\tmp\minha_narracao

:: outra voz da biblioteca ou outra conta do cofre (nunca do Kaggle)
%PY% -X utf8 fish_audio.py -f roteiro.txt -o PASTA --voz <id> --conta <email>
```

**Arquivos na pasta de saída:**
- `fala_NN.mp3`: uma por fala.
- `fish_tudo.mp3`: todas juntas, com 0,25 s entre elas.
- `relatorio.json`: tempo e caracteres de cada fala, e se deu certo.

**O que o script faz:**
1. Confere que a conta não é do Kaggle.
2. Abre a conta pelo cofre, com o Chrome fora da tela (que é o padrão do cofre).
3. Abre a página da voz e fecha os avisos de propaganda do site.
4. Para cada fala: escreve o texto, clica em "Gerar fala", espera o botão de download e baixa o take 1.
5. Fecha o Chrome no fim. Para deixar aberto, use `--manter-aberto`.

## 7. Para usar nos Shorts (a fazer)

- **Uso:** narração do Short no estilo "tipos de...", com a voz do narrador do Chris.
- **Volume:** com o plano grátis dá uns 17 Shorts por mês. Para a produção diária é preciso o plano Plus
  (decisão da dona).
- **Encaixe na produção:** ainda não foi feito. O caminho seria uma base nova no `anime_tts.py`
  (`VOZ_CLONADA_BASE=fish`) que chama este script com as falas do roteiro e devolve os mp3 por frase.
- **Alternativa grátis:** o Fish Speech aberto rodando na GPU do Kaggle (pedido `fila_teste_voz/fish_speech_1811`,
  script `D:\tmp\teste_voz_kaggle\fish\job_fish.py`). Ainda está esperando conta. É um modelo mais antigo que o
  Drama 3, então falta comparar a qualidade.

## 8. Amostras

`D:\hipercool-materiais\amostras_voz\fish_audio_site_1811\`
- `narrador_chris_fish_site_fala1.mp3`: Fish Audio site.
- `comparar_nosso_clone_RVC.wav`: o nosso clone RVC da mesma voz, para comparar.

## 9. Caminho HTTP (sem navegador) — `fish_http.py` + `fabrica_fish.py` + `sessoes_fish.py`

Provado e medido em 18/11/2026. Mesma ideia do `gemini-argo`/`projeto-navegador-sem-navegador`: falar direto com a
API interna do site. O Chrome só aparece onde é inevitável, para fabricar o token do reCAPTCHA (igual ao Flow), e fica
aberto entre um vídeo e outro.

### As 3 peças

| Arquivo | Faz | Precisa de Chrome? |
|---|---|---|
| `fish_http.py` | gera as falas (POST /task), rodízio de contas, cache, saldo | não |
| `fabrica_fish.py` | Chrome QUENTE por conta (fora da tela, pela ponte do IP dela) com reserva de tokens do reCAPTCHA | sim (só ela) |
| `sessoes_fish.py` | guarda o token Bearer de cada conta (`sessoes.json`): saldo e login conferidos sem Chrome | não |

A fábrica sobe sozinha (oculta, `pythonw`) quando alguém pede e se encerra sozinha. Ela escuta na porta 9397.
- Conta parada há 15 min: o Chrome dela fecha.
- Nenhuma conta aberta por 15 min: a fábrica encerra.
- Se a fábrica morrer de repente, a próxima a subir fecha os Chromes que ela anotou como seus (`fabrica_abertos.json`).
  Nunca fecha um Chrome que a dona ou outro projeto abriu: compara a porta e o pid.

Roda no **python da produção** (`D:\recapd-ambientes\producao\venv`); `requests` comum passa no Fish, não precisa de
`curl_cffi`. O `D:\veo\venv` também serve (é o que o `fish_lote` usa).

### Tempos medidos (18/11)

| Situação | Tempo |
|---|---|
| 1ª fala com tudo frio (abre Chrome + carrega reCAPTCHA) | 35–50 s |
| Fala com a fábrica quente | 1,8–4 s |
| Roteiro de 6 falas, fábrica quente, 3 em paralelo | ~10 s no total |
| Fala repetida (cache) | 0 s, sem gastar crédito |
| Saldo de uma conta (sem Chrome) | ~5 s |
| `preaquecer()` no início do vídeo + 2 falas depois | narração em 3,9 s |
| Caminho antigo (`fish_audio.py`, clicando) | ~7,5 s por fala + 15 s de Chrome |

### Como usar

Linha de comando:
```
set PY=D:\recapd-ambientes\producao\venv\Scripts\python.exe
cd /d D:\hipercool-materiais\comum\fish_audio

%PY% -X utf8 fish_http.py -f roteiro.txt -o D:\tmp\narracao [--velocidade 1.15] [--conta E] [--voz ID]
%PY% -X utf8 fish_http.py --saldo [--conta E]       :: saldo (abre a conta na fábrica)
%PY% -X utf8 sessoes_fish.py saldo <email>          :: saldo SEM Chrome (sessão guardada)
%PY% -X utf8 fish_http.py --estado                  :: contas quentes na fábrica e tokens de reserva
```

Como módulo, que é o jeito recomendado para a produção:
```python
import fish_http as fh

fh.preaquecer()          # NO INÍCIO do vídeo: aquece a conta em 2º plano e volta na hora

# ... roteiro, imagens, montagem ...

feitos = fh.gerar_frases([(0, "fala 1", "a0.mp3"), (1, "fala 2", "a1.mp3")], velocidade=1.1)
# -> {i: arquivo} das falas que saíram; o que faltar fica para o p3. Nunca levanta.
```
`gerar_roteiro(falas, pasta)` continua existindo. Ele gera `fala_NN.mp3`, `fish_tudo.mp3` e `relatorio.json`.
`FishHTTP(email)` com `.saldo()`, `.gerar()` e `.fechar()` também continua: é o que o `fish_lote` usa.

### Controle de crédito e rodízio de contas (dona 18/11)

- **Escolher a conta não abre navegador.** A escolha usa o `creditos.json` (estimativa: 1 crédito por caractere
  gerado). Só a conta escolhida tem o saldo real lido, por HTTP e pelo IP dela, e só quando a estimativa venceu (o
  crédito renovou ou nunca foi lido).
- **Saldo real em segundo plano.** Depois de gerar, o saldo da conta é relido sem segurar quem chamou: a montagem do
  vídeo segue enquanto isso.
- **Rodízio dentro do mesmo roteiro.** A conta de mais crédito gera as falas que cabem no saldo dela. Se não couber
  tudo, a próxima conta **já vai sendo aquecida em paralelo** e assume o resto sem esperar o Chrome abrir. Testado
  com 2 contas: 4 falas na jogoscomia e a 5ª na vendeafiliados3, sem pausa.
- Sem crédito no meio da fala (402), sessão vencida (401) ou conta recusada: troca para a próxima. Nenhuma conta com
  crédito: o resto fica para o p3.
- ⚠️ **Termos de uso:** o Fish proíbe juntar várias contas grátis para somar cota (ver seção 3). O rodízio foi
  pedido pela dona em 18/11 sabendo disso. O risco é a conta ser banida no Fish. Cada conta continua no próprio IP,
  então uma conta banida não arrasta as outras pelo IP.

### O que foi mapeado (capturado de sessão real, nada inventado — `capturas\captura_fish.jsonl`)

- **Autenticação:** `Authorization: Bearer <token>`. O token é o `localStorage.token` da página logada (NÃO é
  cookie) e vale fora do Chrome. O workspace é o `localStorage.active_workspace_id`.
- **Gerar (1 chamada, devolve o MP3 direto):**
  `POST https://api.fish.audio/task` com `{"type":"tts","stream":true,"model":<voz>,"parameters":{"text":...,
  "model_id":<voz>,"format":"mp3","backend":"drama-3","normalize":false[,"prosody":{"speed":1.15,"volume":0}]},
  "recaptcha":<token>}` → o corpo da resposta é o MP3. A velocidade (`prosody.speed`) foi testada: 1,3 deixou a fala
  22% mais curta.
- **Saldo (HTTP puro, não gasta):** `GET /wallet/<workspace>/package` → `{"balance":...,"total":...}`.
- **O reCAPTCHA Enterprise é OBRIGATÓRIO no POST /task.** Sem ele a resposta é `400 Missing reCAPTCHA Enterprise`
  (medido). siteKey: `6LfR4RwqAAAAAEvptRw9zohw7HeDU6NCqtAnJk1i`; action `tts`.
  - A página só carrega o script do reCAPTCHA quando a pessoa clica em gerar, por isso a fábrica injeta ela mesma
    `enterprise.js?render=<siteKey>`.
  - O 1º token de um Chrome recém-aberto leva 10–40 s; depois cai para ~1 s, e saem 3 em paralelo em 1,9 s. Por isso
    a fábrica deixa o Chrome aberto e guarda 3 tokens prontos. O token vale ~2 min e serve uma vez só.
  - O site às vezes recarrega a página e o reCAPTCHA some. A fábrica recarrega a aba sozinha e tenta de novo.

### Regras mantidas
- Cada conta sai pelo IP fixo dela (`fish_proxy = rnprmtfo-N`, ponte `ponte_proxy_fixo.py`), nunca pela casa. Conta
  do Kaggle e conta fora do pool são recusadas (usa `fish_audio.checar_conta`).
- **Proibido laço "ler o saldo de todas".** O saldo só é lido da conta que vai ser usada ou que acabou de gerar
  (regra do CLAUDE.md: nunca varrer contas).
- Se o Chrome da conta já estiver aberto **sem** a ponte do IP dela (por exemplo, a dona logando à mão), a fábrica
  recusa essa conta e **não fecha a janela**.

### Recapturar (se o site mudar o endereço ou o siteKey)
`%PY% -X utf8 capturar_fish.py` abre a conta, gera 1 fala de teste e grava `capturas\captura_fish.jsonl`,
`localStorage.json` e `cookies_fish.json`, para reler os endereços.

### Encaixe na produção (feito pelo outro chat, 18/11 noite)
O `fish_lote` já chama `fish_http.preaquecer()` no começo do Short e `fish_http.gerar_frases(...)` para narrar, no
python da produção, sem subprocesso. Tudo o que está abaixo vale nos Shorts sem mudar o lote.

### O que mais sai sem Chrome (18/11 noite)

| Função | Como | Comando |
|---|---|---|
| Conferir se a conta está logada | `GET /user/self` com o token guardado | `sessoes_fish.py logada <email>` |
| Recuperar fala já gerada sem pagar | histórico `GET /task?state=finished` (20 últimas); o link do MP3 baixa pelo IP da conta | automático no `gerar()` (origem `"historico"`) |
| Pôr conta nova no rodízio | depois do login à mão: abre a conta na fábrica (grava o token) e lê o saldo | `sessoes_fish.py registrar <email>` |
| Medir quanto o token do Fish dura | cada token morto é anotado em `sessoes_vida.jsonl` | `sessoes_fish.py vida` |

- **Ordem para achar uma fala:** cache local → histórico da conta → gerar (paga). Só a fala **gerada** desconta no
  `creditos.json`; cache e histórico não gastam. O histórico só é usado com velocidade normal (fala com outra
  velocidade é outra fala). Testado: fala apagada do cache voltou pelo histórico em 2,4 s, com o saldo parado.
- **Cache com limite:** passou de 500 MB (`FISH_CACHE_MB`), apaga os usados há mais tempo até 80% do teto. Roda no fim
  de cada `gerar_frases`.
- **Aviso no Telegram (só no resumo das 9/14/21 h, origem `fish`):** quando falas vão para o p3 por falta de conta
  com crédito, ou quando a fábrica não sobe. Não sai na hora, porque o p3 já narrou; repetido em 12 h não repete.
- **Conta nova no rodízio:** a dona loga à mão (`login_fish.py <email>`, uma conta, a janela fica aberta para ela) e
  depois roda `sessoes_fish.py registrar <email>`. A partir daí a conta entra na escolha por crédito sozinha.
- **Validade do token:** ainda não medida (nenhum morreu até 18/11 21h). Quando morre, o sistema percebe (401),
  marca a sessão como morta, e a fábrica grava um token novo na próxima vez que abrir a conta. Para ver: `vida`.
