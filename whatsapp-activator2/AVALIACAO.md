# Número de WhatsApp sem celular — avaliação (07/10/2026, agente do PC)

Pedido da dona: comprar o chip, pôr o número no painel do Hermes, receber o SMS, digitar o código e usar o número só
online, sem manter um celular por número.

## 1. O que existe nesta pasta (feito por outro agente em 07/10) e por que não funciona

| Ponto | O que foi conferido |
|---|---|
| Onde roda | Foi instalado na **VPS de produção** (`/opt/whatsapp-activator`, porta 8091) e ficou rodando. **Parado em 07/10 19:05** (arquivos mantidos). |
| Emulador | Usa a imagem `budtmo/docker-android` (6,8 GB). Ela precisa de virtualização (`/dev/kvm`). **Nenhuma das três VPS tem** (conferido: sem `/dev/kvm`, sem `svm/vmx` na CPU). O Android não sobe ali. |
| "Passos concluídos" | O registro mostra "instalando WhatsApp" e "inserindo número" terminando em 6 s cada, e o fluxo seguiu adiante com o código de SMS falso `123456`. Os comandos são mandados sem conferir o resultado: o serviço diz que fez o que não fez. |
| Pareamento | O `STATUS.md` diz que falta no Hermes um endpoint que "aceite o código gerado no emulador". **Esse fluxo não existe no WhatsApp.** É o contrário: o aparelho novo (Hermes) gera o código e o celular digita. O Hermes já tem isso: `POST /api/sessions/{sid}/pair-code`. |
| Depois de parear | O serviço **apaga o emulador**. Sem o aparelho principal o número cai em até 14 dias (ver seção 2). |
| O que deixou na produção | 1 conta (`ac***@internal.local`), 1 linha sem pareamento ("Linha Campanha - 5544") com banco próprio, 1 arquivo com a chave de acesso dessa conta (agora só o root lê) e a imagem de 6,8 GB. **Não apagados**: decisão da dona. |
| Hermes | O programa no ar não foi alterado (binário igual ao da versão publicada, nenhum reinício). |

## 2. Como o WhatsApp funciona (duas ideias que precisam de ajuste)

1. **Todo número tem um aparelho principal**, que é o aplicativo do WhatsApp num Android ou iPhone. É nele que o SMS
   é confirmado. O Hermes entra como **aparelho conectado** (igual ao WhatsApp Web).
2. **Não é "conectar uma vez e pronto".** Se o aparelho principal ficar **14 dias** sem abrir o WhatsApp, os aparelhos
   conectados são desligados. O principal não precisa ficar ligado o tempo todo, mas precisa **abrir alguns minutos a
   cada ~10 dias**. O aplicativo também vence e pede atualização de tempos em tempos.
3. No pareamento por código, **quem gera o código é o Hermes** e quem digita é o aparelho principal.

## 3. Todas as possibilidades

| # | Caminho | Sem celular? | Liga para lista fria? | Avaliação |
|---|---|---|---|---|
| A | **API oficial do WhatsApp (Meta)**: o número é registrado direto na Meta por SMS, sem aplicativo | sim | **não**: ligação que parte da empresa exige autorização prévia de cada pessoa | Caminho oficial e estável. Serve para atendimento e mensagens. Não serve para a campanha de ligações. Exige reescrever a parte de voz do Hermes. |
| B | Registrar o número direto pelo servidor, com programa não oficial, sem aplicativo nenhum | sim | sim | Fora do escopo desta avaliação. |
| C | **Celular virtual com o WhatsApp oficial**, ligado só para ativar e depois alguns minutos a cada ~10 dias | sim | sim | **É o que atende o pedido.** É o que a dona já faz à mão com emulador. Falta automatizar e, principalmente, definir **onde** o celular virtual roda. |
| D | Parear por código pelo painel (sem QR) | não | sim | Já existe no servidor; falta o botão no painel. Ainda precisa do celular: a dona já disse que não é isso. É uma peça do caminho C. |
| E | Um celular para vários números (WhatsApp + WhatsApp Business no mesmo aparelho; o aplicativo hoje aceita mais de uma conta) | não | sim | Reduz a quantidade de aparelhos, não elimina. Quantas contas cabem não foi conferido. |

## 4. O caminho C direito

1. No painel: "Ativar número". O Hermes pede a um **ativador** que ligue um celular virtual com o WhatsApp oficial.
2. O WhatsApp manda o SMS para o chip. A dona digita o código no painel.
3. O Hermes cria a linha e **gera** o código de pareamento; o ativador digita esse código no celular virtual.
4. O celular virtual é **guardado desligado** (não apagado).
5. A cada ~10 dias o ativador liga cada celular virtual por alguns minutos. Se a linha cair, repete o passo 3.
6. Cada passo **confere a tela** antes de dizer que deu certo.

**Onde o celular virtual pode rodar** (é isto que trava hoje):

| Lugar | Situação |
|---|---|
| VPS de produção, de teste e 157 | Sem virtualização: emulador não sobe. Dá para trocar o kernel da de teste por um que rode Android em contêiner, mas exige reiniciar uma máquina com ~40 serviços. |
| PC da dona | Tem virtualização. Não achei nenhum emulador instalado nem o `adb`. Ligado só na ativação e a cada ~10 dias. |
| Servidor alugado com virtualização (KVM) | Funciona; custo mensal. |
| Serviço de "celular na nuvem" | Funciona sem montar nada; custo por aparelho; o WhatsApp fica na mão de terceiros. |

## 5. O que falta decidir

1. Qual emulador a dona usa hoje, e em que máquina.
2. Onde os celulares virtuais vão morar (tabela acima).
3. O que fazer com o que o outro agente deixou na produção (conta, linha, imagem de 6,8 GB, pasta).

Nada foi construído nesta avaliação. O teste de ponta a ponta precisa de um chip novo e do SMS dele.

## 6. Atualização de 08/10/2026: o código foi refeito

A dona pediu para corrigir o projeto o melhor possível. O código desta pasta agora segue o caminho C
da seção 4. O que mudou em relação à tabela da seção 1:

| Ponto da seção 1 | Como ficou |
|---|---|
| "Passos concluídos" sem conferir | Cada comando no contêiner é esperado e o código de saída é lido. O Android só conta como ligado quando responde. Cada passo do WhatsApp só termina quando a tela seguinte aparece; senão é erro com o que está na tela. |
| Emulador sem virtualização | O serviço confere `/dev/kvm`, avisa ao subir e recusa a ativação antes de gastar um pedido de SMS. |
| Pareamento | Direção certa (o Hermes gera, o celular virtual digita) e só é "concluído" quando o Hermes mostra a linha pareada com o número. Linha criada que não pareia é apagada do Hermes. |
| Apagava o emulador | O celular virtual com a conta fica guardado desligado e é ligado toda semana. Nunca é apagado sozinho. |
| API sem senha, em todas as interfaces | Só em `127.0.0.1` por padrão; fora disso exige senha. |

**O que continua valendo desta avaliação:** as seções 2, 3 e 5. Em especial, **não há máquina para
rodar** (seção 4, tabela "onde o celular virtual pode rodar"), e as telas do WhatsApp que a automação
espera nunca foram conferidas num aparelho de verdade. Detalhes no `README.md`.

**Na VPS de produção**, a pedido da dona, a versão nova substituiu a antiga em 08/10 00:14
(`/opt/whatsapp-activator`, só em `127.0.0.1:8091`, com senha; configuração em `activator.env`, que só o
root lê; iniciada com `nohup`, sem unidade do systemd). O binário e o registro antigos ficaram na mesma
pasta como `activator.antigo-20261007*`. O token do Hermes foi aproveitado do processo antigo e vence em
08/10 por volta das 18h. O outro agente tinha religado o programa antigo às 19:07 de 07/10 e feito mais
dois testes, que deixaram mais duas linhas vazias no Hermes: são três "Linha Campanha" sem número
pareado (18:10, 19:14 e 19:17, conferido no banco). Essas linhas, a conta do ativador e a imagem de
6,8 GB continuam lá: decisão da dona.

## 7. Por que o teste com número real não começa na produção (08/10)

O pedido de ativação feito na produção com um número real foi recusado pelo serviço com
"esta máquina não tem virtualização", antes de pedir SMS. Conferido no mesmo dia:

| O que | Resultado |
|---|---|
| VPS de produção e de teste | São máquinas virtuais sem virtualização aninhada: sem `/dev/kvm`, CPU sem `vmx/svm`. |
| Imagem `budtmo/docker-android` sem `/dev/kvm` | O código dela (`cli/src/device/emulator.py`) lança `"/dev/kvm cannot be found!"` e nem chama o emulador. Nos testes de 07/10 o Android nunca ligou. |
| Android em contêiner (sem virtualização) | Precisa do módulo `binder_linux`. O kernel das duas VPS é o `cloud` do Debian 12, que não tem. |
| Kernel genérico do Debian, mesma versão (`linux-image-6.1.0-53-amd64`) | Tem `binder_linux.ko` (conferido abrindo o pacote). Instalar e reiniciar a VPS de **teste** nele permite Android em contêiner (Redroid). Sem `binderfs`: um conjunto de dispositivos binder por contêiner ligado, o que casa com "um celular virtual ligado por vez". |
| APK do WhatsApp | Tem bibliotecas `x86_64`: roda direto num Android x86_64, sem tradução de ARM. |
| VPS de teste | 8 núcleos, 23 GB de memória (17 livres), Docker 28. |

Caminhos para rodar de verdade, do mais barato ao mais caro:

1. **VPS de teste com Android em contêiner**: instalar o kernel genérico, reiniciar a VPS de teste uma
   vez e acrescentar ao ativador esse tipo de celular virtual (hoje ele só conhece a imagem com
   emulador). Sem custo mensal. Incógnita: como o WhatsApp se comporta nesse Android (sem serviços do
   Google); só testando.
2. **Servidor alugado com virtualização**: o código atual roda como está. Custo mensal.
3. **PC da dona**: Windows 10 não dá `/dev/kvm` ao Docker; teria de usar o emulador do Android no
   próprio Windows, com outro tipo de celular virtual no ativador, pouco disco livre e o PC ligado toda
   semana.

Emulação por software (sem aceleração) não foi tentada: é lenta a ponto de o Android 11 levar dezenas
de minutos para ligar, e disputaria CPU com os outros serviços.

## 8. O PC da dona roda o celular virtual (08/10, madrugada)

A dona pediu uma versão para Windows neste PC, em outra pasta. Feito: pasta de execução
`D:\whatsapp-activator-windows` (tem um `LEIA.md`), com o emulador oficial do Android baixado do
repositório do Google (1,56 GB de download, com a soma de verificação conferida).

| O que | Resultado |
|---|---|
| Aceleração do emulador no PC | Disponível (WHPX), sem ligar recurso nem reiniciar. A consulta ao Windows dizia que o recurso estava desligado; o emulador respondeu que funciona, e funcionou. |
| Android ligando | 1 min 53 s no primeiro boot. |
| WhatsApp oficial | Versão 2.26.39.75 instalada e aberta. |
| Aviso de "custom ROM" | Aparece no emulador. O OK é o `button2` (eu supunha `button1`); corrigido para achar pelo texto. |
| Termos e tela do número | A automação chegou sozinha. Os ids previstos (`eula_accept`, `registration_cc`, `registration_phone`, `registration_submit`) estavam certos. |
| **Tela do número** | **O WhatsApp ignora toque automático nela.** Seis toques por comando em três controles sem efeito; um clique como o do mouse na janela teve efeito na hora. O número é digitado pela dona, na janela. |
| Disco | O emulador exige 6 GB de armazenamento por celular e 7,4 GB livres na criação, ignorando a configuração. Resolvido com a compactação de arquivos do Windows nas pastas do ativador: 2,7 GB reais por celular. |

Consequência para o caminho C da seção 4: o passo 2 ("a dona digita o código no painel") vira "a dona
digita o número e o código **na janela do celular virtual**". O resto do caminho segue automático. Num
servidor sem tela (caminhos 1 e 2 da seção 7) esse passo não tem como ser feito, então **o PC, ou
outra máquina com tela, passa a ser o lugar natural dos celulares virtuais**, e o limite é o disco.

O programa ganhou para isso: estado `awaiting_number` (espera a pessoa, só lendo a tela), código de
SMS aceito tanto pela API quanto digitado na janela, `pairing_code` à mostra quando o toque não é
aceito, e `POST /api/adopt` para passar a cuidar de um celular virtual ativado à mão.

Estado ao fim desta sessão: o celular virtual de teste (`ensaio`) está ligado, com o WhatsApp na tela
do número, esperando a dona digitar. Nenhum número foi digitado e nenhum SMS foi pedido.
