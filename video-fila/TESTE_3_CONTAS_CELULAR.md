# Teste: 3 contas criadas e usadas SÓ pelo celular (dona 18/11/2026)

## Objetivo
Descobrir se o que derrubou os 12 canais (17/11) foi o **login em massa** (várias contas no mesmo aparelho/IP) ou o
**jeito de postar** (navegador/PC). E ver se conta "orgânica" (criada e usada só no próprio celular) **viraliza mais**.

## As 3 contas (uma por aparelho, nada mais logado nelas)
| Conta | Aparelho | Rede | Papel no teste |
|---|---|---|---|
| emersonjosiel2042 | A2 | 3G (chip) | orgânica 3G |
| emersonjosiel2043 | S20 | 3G (chip) | orgânica 3G |
| emersonjosiel2052 | S20 Ultra | **Wi-Fi da casa** | **parâmetro** (mesmo celular/app, IP da casa) |

| emersonjosiel2054 | A3 | 4G (chip Pague Menos, Wi-Fi off) | **teste de contágio**: aparelho com ~59 contas logadas (inclusive 4 Kaggle vivas) |

**A3 = teste diferente (dona 18/11 16h):** o A3 tem várias contas antigas logadas. A ideia é usar SÓ a 2054 nele (criar
canal, postar) e deixar as outras logadas, sem mexer nelas, para ver se uma conta nova usada no aparelho influencia o
banimento das contas que já estavam lá. Cada celular tem a sua conta nova = cada um é um teste isolado (uma conta nova
por aparelho, nunca duas).
O que olhar no A3: (a) a 2054 é punida? (b) alguma das contas antigas do A3 é punida DEPOIS do uso da 2054 (comparar com
as mesmas contas antes de 18/11)? Se (b) sim e nos outros aparelhos não → usar conta nova num celular com muitas contas
põe as antigas em risco.

Regras do teste (não quebrar, senão o resultado não vale):
- Tudo da conta é feito **no próprio celular, pelo app do YouTube**: criar canal, foto, banner, descrição, postar.
  Nada pelo PC, nada pelo Chrome do cofre, nenhum robô de PC falando como essas contas.
- **Nenhuma outra conta** loga nesses 3 aparelhos durante o teste (G20/A3 com várias contas = o que derrubou os 12).
- **Conta nova: captcha / "não sou um robô" / confirmação = PARAR e avisar a dona** (regra 18/11).
- Mesmo ritmo nas 3: 1 Short por dia na 1ª semana, mesmo tipo de conteúdo (fatos/curiosidades), horário nobre.
- Vídeo único por canal (a mesma fonte nunca em 2 canais).
- O 2053 só muda a REDE (casa em vez de 3G). Todo o resto igual.

## Comparação de controle (PC/navegador)
Os 2 canais novos de 18/11 feitos pelo PC (Chrome do cofre, IP da casa):
- **Fato Chocante** (phikhanh141173) e **Por Dentro** (duongphuong6983) — mesmo nicho, 1/dia.
Assim dá pra comparar: celular 3G x celular casa x PC casa.

## O que medir (por canal, dia a dia, 14 dias)
- Banido / removido / "confirme identidade" / captcha (data e tela)
- Views em 48 h por Short, inscritos, % de Shorts que passam de 1.000 views
- Mediana de views (mesma métrica do relatório)

## Possibilidades e o que fazer em cada uma
| Resultado | O que significa | Decisão |
|---|---|---|
| 3G (2042/2043) e casa (2053) **iguais** em views e ninguém banido | a rede (3G x casa) não faz diferença | pode postar pelo celular pelo Wi-Fi da casa ou pelo PC |
| Celular (3G e casa) **melhor** que o PC, ninguém banido | o banimento de 17/11 foi o LOGIN EM MASSA, não o jeito de postar; celular viraliza mais | migrar a postagem pros celulares (1 conta por aparelho) |
| Celular **igual** ao PC, ninguém banido | não importa por onde posta | escolher pelo que é mais barato/estável (PC) |
| **Só o 2053 (casa) banido**, os 3G não | IP da casa compartilhado é risco | celular SÓ no 3G; nunca Wi-Fi da casa pra conta nova |
| **Os 3G banidos**, o 2053 não | o chip/3G é que está marcado (operadora/IP de CGNAT ruim) | usar celular no Wi-Fi da casa; trocar chip |
| **Todos os celulares banidos**, PC não | o problema é o app/aparelho (ex.: aparelho já marcado pelos 12) | voltar pro PC; não usar esses aparelhos |
| **PC banido**, celulares não | navegador/automação é o que pega | postar só pelos celulares |
| Ninguém banido e **ninguém faz sucesso** | o nicho/conteúdo é o problema, não a forma | trocar conteúdo antes de concluir algo |
| Celular 3G **muito melhor** que o 2053 (casa) | o 3G ajuda a distribuição (IP "móvel" orgânico) | postar pelo celular no 3G pra viralizar |

## ⚠️ Ponto a conferir antes de começar
Pela contagem de 17/11 (`projeto celular sub controle\CONTAS_POR_APARELHO_1711.md`), o **A2 tinha 17 contas** e o
**S20 35 contas** logadas. Se continuarem lá, as contas novas NÃO estão sozinhas no aparelho — o teste mediria
"celular com várias contas" (o mesmo cenário que derrubou os 12), não "conta orgânica". A dona precisa confirmar se
os aparelhos foram limpos (só a conta nova) ou se o teste segue assim mesmo (aí o resultado vale pra esse cenário).

**Decisão da dona 18/11 ~13h40:** NÃO tirar as contas antigas — o teste segue com elas nos aparelhos. Então o teste
mede "conta nova criada e usada só no celular, num aparelho que tem outras contas" (A2: +15, inclusive Kaggle vivas;
S20 Ultra: +8). Interpretar o resultado com isso em mente: se a conta nova for punida, olhar se as outras do mesmo
aparelho também foram (sinal de família ligada pelo aparelho).
Motivo da dona: se o teste mostrar que o celular é o melhor caminho, as contas teriam que ser logadas de novo — e o que
vimos é que **logins em massa / simultâneos** é o que causa banimento. Deslogar agora = relogar depois = risco à toa.

## Status
- 18/11 ~10:35: documentado. Contas criadas pela dona nos aparelhos. Falta: confirmar que cada aparelho só tem a conta
  dele, criar o canal pelo app, 1º post. Fato Chocante e Por Dentro (controle PC) com 1º Short agendado 11:05/11:10.
- 18/11 10:45: 1º Short dos canais de controle (PC): Fato Chocante https://youtu.be/Em6oLFNG6yo (11:15), Por Dentro https://youtu.be/1Em7b7KE6WE (11:30, sem capa: telefone não verificado).
- 18/11 15:19: canal da 2042 criado pelo app no A2 = **Curioso Demais** (@CuriosoDemais-l6p), sem captcha.
  1º Short pronto (pássaro, parceiro sem-obra-105c05) com a @ antiga (@codigointeligente-n7j) trocada pela
  @CuriosoDemais-l6p: `D:\tmp\teste_remoto\desktop\curioso_passaro.mp4` (script `D:\tmp\canal_phikhanh\trocar_marca.py`,
  render no desktop). Não postado: A2 caiu do 3G/Tailscale às 16:00. postar_celular.py não serve no A2 (uiautomator
  "null root node" com o YouTube aberto) → postar à mão por print+toque.
- 18/11 16:05: S20 Ultra NÃO tem a 2052 no Android (só foi criada no Chrome) — falta "Adicionar conta". App do YouTube
  abre com aviso "contestação negada (spam)" de canal antigo. Tela mudando sozinha (busca, notícias) = alguém/outro
  processo usando → parei de mexer.
- ⚠️ Shorts de parceiro levam queimada a @ de canal NOSSO antigo: os 1ºs posts do Fato Chocante e Por Dentro saíram com
  @...noturno e @curiosidadesnoturnasbr — liga os canais novos à família antiga. Antes de postar parceiro em canal de
  teste: trocar a @ (trocar_marca.py).
- 18/11 15:05: A2 com toque fantasma — automação parada; a dona decide (criar o canal da 2042 na mão ou tentar depois).
- 18/11 16:20 — **S20 (2043): conta RESTRITA pelo Google.** O app abre direto em "Não foi possível acessar um produto do
  Google — conteste a restrição de acesso à conta emersonjosiel2043" (formulário de contestação). Nada preenchido; tela
  deixada aberta. (Já nasceu punida? criada no 3G hoje — 1º dado do teste.)
- 18/11 16:23 — **A3 (2054):** a conta existia só no Chrome; ao adicionar no Android (Configurações > Adicionar conta)
  o Google pediu "Confirme que é você — Não sou um robô (reCAPTCHA)". PAREI (regra): tela deixada aberta no A3.
- G20: não tem conta nova de teste (só as antigas 2026-2038). A2 (2042): fora do ar (3G caiu 16:00).
- S20 Ultra (2052): só no Chrome, falta Adicionar conta no Android (dona confere).
- 18/11 16:40 — S20 Ultra: a dona confirmou que a 2052 já está no aparelho → falta criar o canal e fazer o 1º post (depois).
- 18/11 16:38 — S20 (2043): formulário de contestação refeito pela dona, parado no campo "URL do canal suspenso". Não há
  registro de canal criado na 2043 (nem @ nem ID UC…): a restrição apareceu logo após a conta ser criada.
- 18/11 ~17:00 — dona: a restrição do S20 (2043) era BUG; S20, A2 e A3 normais. (Correção: o formulário de contestação NÃO foi enviado.)
- 18/11 17:50 — **A2 (2042) 1º Short postado pelo app**: Curioso Demais, "NINGUÉM ESPERAVA que esse PÁSSARO esconde esse SEGREDO! 😱", agendado 18/11 21:00, não é para crianças (aparece "Programado"). Canal UCGUq0XSFjae30caBuP8a5kQ.
- 18/11 18:23 — **A3 (2054) canal criado pelo app: Fatos Ocultos** @FatosOcultos-x8j (UCe9gcknfH3e0caH4nR9nSGQ), sem captcha.
- 18/11 18:32 — **S20 Ultra (2052) canal criado pelo app: Segredos Revelados** @SegredosRevelados-q8h (UCRLyr94K9_kBIrSLzjh-eOQ), sem captcha.
- 18/11 18:26 — **S20 (2043): "Esse nome não pode ser usado no seu canal"** para 2 nomes diferentes ("Mundo Curioso" e "Curiosidades do Mundo"); o @mundocuriosobr-h8e foi aceito. 2 nomes comuns recusados = provável trava da conta (a mesma que mostrou a restrição antes), não o nome. PAREI; tela "How you'll appear" deixada aberta. 2º dado do teste: a 2043 (3G) é a única com problema.
- Falta: 1º Short em Fatos Ocultos e Segredos Revelados (vídeo único com a @ trocada, horário nobre).
- 18/11 ~19:00 — a dona criou à mão o canal do S20 (2043): **Curiosidades do Mundo 3d** @mundocuriosobr-h8e.
- 18/11 noite — **os 4 primeiros Shorts agendados, cada um pelo app do próprio celular**: Curioso Demais (A2) 21:00,
  Fatos Ocultos (A3) 21:30, Curiosidades do Mundo 3d (S20) 21:45, Segredos Revelados (S20U) 22:00. Todos "não é para
  crianças". 21:40: o do Curioso Demais já estava no ar com **257 views**.
- ⚠️ vigia_celulares/celular_midia pegam os celulares do teste no meio do trabalho (o 16664 tomou o S20). Ao mexer no
  celular: `pausado_<serial>.txt` (o `celular_canal\canal.py` já faz isso sozinho).
- 18/11 21:30-21:55 — **artes do outro chat aplicadas pelo app** (`D:\manhwa-react\canais\<slug>`): Segredos Revelados
  (S20U) foto + banner + descrição ✔; Curioso Demais (A2) foto + banner + descrição ✔. Fatos Ocultos (A3) **NÃO**:
  o A3 está com o aviso do Google "Quer permitir que um app acesse seus dados? murilodoctor192 (conta antiga do A3),
  dispositivo Linux, Italva-RJ — Sim, combinar número". É confirmação de identidade → PAREI, tela deixada aberta, a dona
  decide. S20 (Mundo 3d) sem arte (o outro chat não fez).
- Scripts de cada ação (foto, banner, descrição, digitar, print, pausar, postar Short): `D:\projeto celular sub
  controle\celular_canal\LEIA_ME.md`. Banner pelo app precisa ir "preparado" (o editor dá zoom no 16:9): o canal.py faz.
