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
- 18/11 15:05: A2 com toque fantasma — automação parada; a dona decide (criar o canal da 2042 na mão ou tentar depois).
