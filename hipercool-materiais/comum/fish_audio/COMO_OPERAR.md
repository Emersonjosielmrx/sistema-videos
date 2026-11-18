# Fish Audio — como operar (voz do narrador do "Todo Mundo Odeia o Chris")

Atualizado em 18/11/2026. A dona ouviu e disse: "realmente é outro nível de clone de voz".

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
  banimento.
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
