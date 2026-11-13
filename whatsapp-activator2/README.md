# WhatsApp Activator

Ativa um número no WhatsApp sem um celular físico por número: sobe um **celular virtual** (emulador
Android) com o aplicativo oficial do WhatsApp, acompanha o cadastro do número e conecta o Hermes
Call como aparelho dele. O celular virtual fica **guardado desligado** e é ligado alguns minutos
por semana, porque ele é o aparelho principal do número.

## Estado (08/10/2026)

Projeto de teste. Rodou com um Android de verdade **até a tela do número**; daí em diante ainda não.

| Parte | Situação |
|---|---|
| Código compila, `go vet` limpo (Windows e Linux) | conferido |
| Testes automáticos (67 casos; também com o detector de corrida, na VPS de teste) | passam |
| Android ligando no PC da dona (Windows 10, emulador oficial, aceleração WHPX) | **funcionou** (1 min 53 s) |
| WhatsApp oficial 2.26.39.75 instalando e abrindo no celular virtual | **funcionou** |
| Aviso de "custom ROM", termos e chegada à tela do número, pela automação | **funcionou** |
| Tela do número aceitar digitação automática | **não aceita**: o WhatsApp ignora toque automático nela (ver abaixo) |
| Confirmação do número, código de SMS, perfil, aparelhos conectados | **não conferido num aparelho de verdade** |
| Desligar, guardar e religar o celular virtual com a conta dentro | **não conferido** |
| Celular virtual em Docker (`budtmo/docker-android`) | **nunca rodou**: nenhuma VPS tem `/dev/kvm` |

### O WhatsApp barra toque automático na tela do número

Conferido em 08/10: na tela de digitar o número, toques enviados por comando (`adb shell input`) não
têm efeito em nenhum controle, enquanto um clique de mouse na janela do emulador funciona. Nas telas
anteriores (aviso, termos) o toque automático funciona. É uma barreira do WhatsApp contra cadastro
automático e **este programa não a contorna**. Onde uma tela não aceita o toque, o programa para de
tentar, avisa no campo `notice` da sessão e espera a pessoa fazer aquela tela na janela do celular.

Isso só é possível onde há janela: no Windows (emulador com janela). Num servidor sem tela, a
ativação para em erro nesse ponto.

## Dois tipos de celular virtual

| `BACKEND` | Onde | Como |
|---|---|---|
| `avd` (padrão no Windows) | PC com Windows | emulador oficial do Android instalado numa pasta, com janela. Pasta de execução: `D:\whatsapp-activator-windows` (tem um `LEIA.md` próprio) |
| `docker` (padrão no Linux) | servidor Linux com `/dev/kvm` | emulador dentro de um contêiner (`budtmo/docker-android`), sem janela |

## Como funciona

1. `POST /api/activate` com o número. Antes de qualquer coisa o serviço confere: APK presente,
   máquina capaz de rodar o celular virtual, Hermes respondendo e aceitando o token.
2. Cria o celular virtual e espera o Android responder que terminou de ligar.
3. Instala o WhatsApp e confere no Android que o pacote existe.
4. Abre o WhatsApp, fecha o aviso de "custom ROM", aceita os termos e tenta digitar o número. Se a
   tela não aceitar (é o caso hoje), a sessão vai para `awaiting_number` e o serviço **só observa**
   até a pessoa digitar o número na janela e o WhatsApp chegar à tela do código.
5. `awaiting_sms`: o código pode vir por `POST /api/activate/{id}/sms` ou ser digitado na janela;
   o que vier primeiro. Código recusado: até 3 tentativas.
6. Pareamento: o serviço cria a linha no Hermes, **pede o código ao Hermes** e o digita no WhatsApp
   (Aparelhos conectados > Conectar com número de telefone). Se o toque não for aceito, o código fica
   no campo `pairing_code` para a pessoa digitar. Só é `completed` quando o Hermes mostra a linha
   pareada com esse número.
7. O celular virtual é desligado pelo próprio Android e guardado. A cada `WAKE_EVERY` (7 dias) o
   serviço o liga por `WAKE_FOR` (3 min) e confere que o WhatsApp continua com a conta.

Só um celular virtual fica ligado por vez.

## O que a máquina precisa

**Windows (`avd`):** rodar uma vez `python -I preparar.py` na pasta de execução (baixa adb, emulador
e Android 9 do repositório oficial, 1,56 GB de download, 3,7 GB em disco). `emulator -accel-check`
tem de responder que a aceleração está disponível; o serviço confere isso ao subir. Cerca de 3 GB de
memória por celular ligado e ~2,7 GB reais de disco por celular guardado (com a compactação de
arquivos do Windows; ver `LEIA.md` da pasta de execução).

**Linux (`docker`):** Docker e `/dev/kvm`. Sem `/dev/kvm` o serviço avisa ao subir, mostra em
`/health` e recusa ativações. Cerca de 4 GB de memória e ~7 GB de disco para a imagem.

Nos dois: APK oficial do WhatsApp (whatsapp.com/android) e acesso à API do Hermes com o token de
uma conta, que será a dona das linhas criadas.

## Configuração

O serviço lê `activator.env` da pasta onde roda (variável de ambiente já definida vale mais). Todas
as variáveis estão em `.env.example`. As que importam:

| Variável | Padrão | Para quê |
|---|---|---|
| `BACKEND` | `avd` no Windows, `docker` no Linux | tipo de celular virtual |
| `LISTEN_ADDR` / `PORT` | `127.0.0.1` / `8090` | onde a API escuta |
| `ACTIVATOR_TOKEN` | vazio | senha da API; obrigatória fora de `127.0.0.1` |
| `HERMES_URL` / `HERMES_TOKEN` | `http://localhost:8080` / vazio | Hermes Call |
| `PROFILE_NAME` | `Atendimento` | nome que o número mostra no WhatsApp |
| `DATA_DIR` | `./data` | sessões (`sessoes.json`) e telas de erro (`diagnostico/`) |
| `MANUAL_TIMEOUT` | `15m` | prazo de um passo feito à mão na janela do celular |
| `EMULATOR_WINDOW` | `1` | (`avd`) mostrar a janela do celular |

## Rodar

```bash
go build -o activator . && ./activator
```

No Windows: `iniciar.bat` na pasta de execução. No Linux também há `docker compose up -d --build`
(precisa de `.env` com `ACTIVATOR_TOKEN` e `HERMES_TOKEN`).

## API

Tudo em `/api` pede `Authorization: Bearer $ACTIVATOR_TOKEN` quando a senha está configurada.
Erros voltam como `{"error": "..."}`.

| Rota | O que faz |
|---|---|
| `GET /health` | serviço no ar e se a máquina roda o celular virtual (sem senha) |
| `POST /api/activate` | começa a ativação. Corpo: `phone` (obrigatório), `name` (nome da linha no Hermes), `profile_name` |
| `POST /api/adopt` | põe sob os cuidados do serviço um celular virtual que já existe e já tem o número ativado. Corpo: `phone`, `emulator_id`, e opcionais `name`, `hermes_session_id` |
| `GET /api/activate` | lista as sessões |
| `GET /api/activate/{id}` | estado de uma sessão |
| `POST /api/activate/{id}/sms` | envia o código de SMS (`{"code": "123456"}`); só em `awaiting_sms` |
| `POST /api/activate/{id}/pair` | pareia de novo um número já ativado (pareamento que falhou ou linha que caiu) |
| `POST /api/activate/{id}/wake` | liga agora o celular virtual guardado |
| `GET /api/activate/{id}/tela` | o que está escrito na tela do celular ligado; `?png=1` devolve a imagem |
| `POST /api/activate/{id}/toque` | toca num botão pelo texto (`{"texto": "Agora não"}`) |
| `DELETE /api/activate/{id}` | cancela e apaga o celular virtual. Com o número já ativado, só com `?force=1` |

```bash
curl -s -X POST http://127.0.0.1:8090/api/activate \
  -H "Authorization: Bearer $ACTIVATOR_TOKEN" \
  -d '{"phone": "+55 11 90000-0000", "profile_name": "Atendimento"}'
```

### Campos da sessão

| Campo | Significado |
|---|---|
| `state` | `creating_emulator`, `installing_whatsapp`, `entering_phone`, `awaiting_number`, `awaiting_sms`, `pairing`, `checking`, `completed`, `error` |
| `job` | trabalho em andamento: `ativar`, `parear`, `ligar`, `adotar` |
| `registered` | o WhatsApp do celular virtual tem a conta do número |
| `error` / `notice` | por que falhou / recado: o que a pessoa tem de fazer na janela, código recusado etc. |
| `pairing_code` | código de pareamento à espera de ser digitado no celular |
| `diagnostic` | caminho (sem extensão) do `.xml` e do `.png` com a tela do último erro |
| `hermes_session_id` | linha criada no Hermes |
| `last_wake_at` / `last_wake_error` | última vez que o celular guardado foi ligado, e o problema se houve |

Estado `error` com `registered: true` significa: o número foi ativado, só o pareamento falhou. O
celular virtual está guardado; use `/pair`, não é preciso outro SMS.

## Ensaio sem gastar SMS

`ensaio.exe` (código em `cmd/ensaio`) liga um celular virtual de teste, instala o WhatsApp e avança
até a tela do número **sem digitar número nenhum**, guardando cada tela que aparece (XML e imagem) e
imprimindo textos e ids. É o jeito de conferir uma versão nova do WhatsApp antes de usar um chip.

## Quando um passo falha

O erro diz o passo e o que estava escrito na tela, por exemplo:

```
inserir o número: a tela esperada não apareceu em 3m0s. Na tela: Verificar de outra forma | ...
```

1. Olhe `data/diagnostico/<id>-<hora>.png` e `.xml` (a tela no momento do erro).
2. Se for uma tela que a automação não conhece, acrescente o id ou o texto do botão em
   `internal/whatsapp/screens.go`. O `.xml` tem os `resource-id` e os textos exatos. Atenção: a
   posição dos botões de um diálogo muda (no aviso de "custom ROM" o OK é o `button2`); ache o
   botão pelo texto, com `dialogButton`.
3. Com a sessão em andamento dá para ver a tela por `GET .../tela` e, no Windows, agir direto na
   janela do celular: o fluxo continua sozinho quando a tela esperada aparece.

Recados conhecidos do WhatsApp (número banido, espere para tentar de novo, código errado,
confirmação em duas etapas, versão vencida) viram erro com explicação.

## Segurança

- A API cria e apaga celulares virtuais (e, no Linux, contêineres): por isso escuta em `127.0.0.1`
  por padrão e o serviço se recusa a subir em outro endereço sem `ACTIVATOR_TOKEN`.
- Número, nome de perfil e códigos são validados antes de chegar ao `adb shell` (só dígitos, ou
  letras, números e espaço).
- O registro mostra o número mascarado e nunca os códigos de SMS.
- No Linux o contêiner do emulador recebe só o dispositivo `/dev/kvm`, não roda como `privileged`.
- Um celular virtual com conta **nunca é apagado sozinho**: nem por erro, nem por reinício, nem por
  limpeza. Celular virtual que nenhuma sessão conhece é só avisado no registro.
- O programa não falsifica nada para o WhatsApp e não contorna as barreiras dele: usa o aplicativo
  oficial, e o que o aplicativo exige que seja feito à mão é feito à mão.
- Não escreva token nem número de chip em arquivo desta pasta.

## Desenvolvimento

```bash
go vet ./... && go test ./...
CGO_ENABLED=1 go test -race ./...   # precisa de gcc; o PC não tem, rodar numa VPS
```

```
main.go                       configuração e servidor HTTP
cmd/ensaio/                   ensaio até a tela do número, sem digitar nada
internal/activator/           fluxos (ativar, parear, ligar, adotar), API, sessões em disco
internal/avd/                 celular virtual no Windows: emulador oficial do Android, sem Docker
internal/emulator/            celular virtual em Docker (precisa de /dev/kvm)
internal/whatsapp/            automação por leitura de tela (uiautomator)
  screens.go                  tabela das telas (o que já foi conferido está dito no topo)
  flows.go                    os passos: número, código, pareamento, conferência
internal/whatsapp/watest/     celular de mentira usado nos testes
internal/hermes/              cliente da API do Hermes
internal/phone/               validação do número (mesma regra do Hermes)
docs/historico/               documentos da primeira versão (não seguir)
```

O celular de mentira dos testes copia o WhatsApp de verdade até a tela do número; daí em diante
segue o que a automação **espera**. Os testes provam a lógica (só avança quando a tela muda, para
quando não muda), não que o WhatsApp tem essas telas.

## O que falta

- Primeira ativação completa com um chip: conferir as telas depois do número (confirmação, código,
  perfil, aparelhos conectados) e acertar `screens.go`.
- Conferir que o celular virtual mantém a conta entre desligar e ligar.
- Rodar o serviço no PC de forma permanente (hoje é `iniciar.bat`, à mão) e garantir o PC ligado
  alguns minutos por semana.
- Disco do PC: cabe pouco mais de um celular virtual por vez no D como está hoje.
- Botão "Ativar número" no painel do Hermes chamando esta API (hoje é só `curl`).
- Atualizar o WhatsApp dentro dos celulares guardados quando a versão vencer (hoje o `ligar` só
  acusa "versão vencida").
