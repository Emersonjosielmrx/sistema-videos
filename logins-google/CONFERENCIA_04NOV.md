# Conferência de logins em todos os PCs — madrugada 04/11/2026

## ☀️ RESUMO PRA DONA (o que precisa de você)
1. **Google emersonjosiel2027** — deslogado no pc2, acer e x200ma (único Google realmente caído nos outros PCs).
2. **Quarentena (PC1, cofre)** — filmescomia00, andreluizdias384, emersonjosiel2028, inovaremanhwaverse3,
   inovaremanhwaverse4, revolutionemerson7: logar quando puder (`python D:\logins-google\logar_deslogadas_pc1.py`).
3. **Kaggle** — token da emersongencshin (Chrome no rnprmtfo-5, IP 185.72.242.159) e dizer por qual IP criou a alxservicesia.
4. **Instagram nos notebooks** — muitas Inovare deslogadas no x200ma/acer (lista abaixo). Só importa se o Insta ainda
   posta pelos notebooks; não relogar sem você (suspende em "aparelho novo").
Não precisa de você: TikTok deslogado (reloga sozinho no post pelo Google).
Falta conferir: resto do pc2/x200ma/acer e o desktop inteiro (parado às 06:20 pro Veo das solares; volta após 10h,
uma máquina por vez). Desktop: todas as contas deram o mesmo canal/@ — causa em aberto, TikTok pelas máquinas desligado.


Pedido da dona (03/11 ~02h): conferir todas as contas dos outros PCs sem ela precisar fechar janela; de manhã, listar
SÓ as realmente deslogadas. Se o Google estiver logado, logar o resto pelo Google; Google deslogado = ela vê de manhã.

## Como está rodando
- `postador-de-videos\bin\netbooks\conferir_logins.py` (padrão: abre, prova pela rede, fecha, respeita a vez da máquina).
- Rodada 1: `logs\conferir_todas_04nov.txt` (desktop pc2 x200ma acer). Rodada 2 (relançada 02:05): `logs\conferir_todas_04nov_b.txt`
  (desktop x200ma acer — pararam por "ocupado há 30 min").
- Resultado por máquina: `logs\conferencia_<maquina>.json`.

## NÃO logar TikTok/Instagram nos outros PCs
Regra de 03/11 (memória project_tiktok_insta_saida_casa): TikTok remoto DESLIGADO — todos os PCs saem pela internet de
casa; posts saem pelo PC1 com o IP Webshare da conta. TikTok deslogado no post reloga sozinho (`bin\tiktok_relogar.py`).
Logar TikTok/Insta nos PCs = várias contas no mesmo IP. Por isso a madrugada é só conferência.

## Achados até 02:05
- PC1 (cofre.checar, 03/11 22h): Google vivo em todas, menos a quarentena (filmescomia00, andreluizdias384,
  emersonjosiel2028, inovaremanhwaverse3, inovaremanhwaverse4, revolutionemerson7 — dona loga 05/11).
- desktop: 34 contas, Google e YouTube todos logados.
  **TikTok do desktop devolve o MESMO @ (@user6824946137963 = TikTok da maiteanajessicajesus) para TODAS as contas** —
  ou a conferência está quebrada no desktop, ou os perfis estão logados no TikTok errado. Investigar sem mexer em conta.
- pc2 (23 até 02:04): Google DESLOGADO emersonjosiel2027; TikTok deslogado en1653964; sem resposta (Chrome não abriu a
  porta a tempo, não é login): aulacomia, emersonjosiel2032, emersonjosielmrx1995, en1653964 (google), entrevistacomia.
- x200ma, acer: não começaram na rodada 1 (ocupados).

## 03:10 — resultado do DESKTOP NÃO VALE (abre sempre a mesma sessão)
Rodada b terminou o desktop (54 contas), mas TODAS deram o mesmo canal do YouTube (UCCF2-yciERdJbuTnruw4jVg, 13 contas)
e o mesmo @ do TikTok (@user6824946137963, 88 conferências). pc2/x200ma/acer devolvem 1 @ por conta (normal).
Causa provável: `maquina_remota.Remoto.abrir` abre o Chrome numa PORTA FIXA no desktop (self.porta); se um Chrome
esquecido já está vivo nessa porta, o script de lá responde PRONTO e toda conta cai nessa sessão. Logo o "Google
logado" do desktop também não prova nada. NÃO matei Chrome no desktop de madrugada (podia ser Veo). Fazer: de manhã,
ver qual Chrome está na porta do desktop, fechar quando livre e rodar `conferir_logins.py desktop` de novo. Conferir
também se postagem/Veo pelo desktop estão caindo na conta errada (risco real se usam a mesma porta).

## Até 03:10 (pc2 41 contas, x200ma 9, acer 9)
- DESLOGADO de verdade: Google emersonjosiel2027 no pc2; TikTok en1653964 no pc2 (TikTok reloga sozinho no post).
- Sem resposta (Chrome não abriu a porta a tempo — não é login, reconferir): pc2: aulacomia, emersonjosiel2032,
  emersonjosielmrx1995, en1653964, entrevistacomia, fabricadeautomacoes0, gabriellyvitoriaisabelaaraujo,
  inovaremanhwaverseviet; x200ma: aulacomia (google/yt/tiktok/insta), canalhistoriacomia (yt/tiktok/insta),
  comoseriasecomia (google/tiktok).

## 04:05
- pc2 rodada 1 TERMINOU: google 44/56 logadas | DESLOGADA emersonjosiel2027 | sem resposta (Chrome lento): aulacomia,
  emersonjosiel2032, emersonjosielmrx1995, en1653964, entrevistacomia, fabricadeautomacoes0,
  gabriellyvitoriaisabelaaraujo, inovaremanhwaverseviet, jogoscomia, mentoriaiapro, seebotsia. TikTok: en1653964 deslogado.
- acer (19 até agora): Google DESLOGADO emersonjosiel2027; Instagram deslogado emersonjosiel2032.
- x200ma parou de novo em 12 (ocupado). Rodada c (pc2 + x200ma) lançada 04:05: `logs\conferir_todas_04nov_c.txt`.

## 05:10 (pc2 18 na rodada c, x200ma 33, acer 30 — ainda rodando)
- Google DESLOGADO: emersonjosiel2027 também no x200ma (já era pc2 e acer) = deslogada em todos.
- Instagram deslogado: x200ma aulacomia, canalhistoriacomia, entrevistacomia; acer emersonjosiel2032,
  inovaremanhwaverseesp, inovaremanhwaversefrench. NÃO relogar sozinho (Instagram suspende em "aparelho novo").
- TikTok deslogado: emersonjosiel2032 no pc2 (reloga sozinho no post).

## 06:10 (pc2 33, x200ma 43, acer 34 — rodando)
Instagram deslogado cresceu (quase todas as Inovare): x200ma aulacomia, canalhistoriacomia, entrevistacomia,
inovaremanhwabr, inovaremanhwaverse, inovaremanhwaverseesp, inovaremanhwaversefrench, inovaremanhwaversehindi;
acer emersonjosiel2032, inovaremanhwaverseesp, inovaremanhwaversefrench, inovaremanhwaversehindi, inovaremanhwaverseind,
inovaremanhwaverseing, inovaremanhwaverseita. Provável: Instagram nos notebooks está marcado como logado (netbooks_logins
de 24/10) mas a sessão caiu há dias — ver se a postagem do Insta ainda usa os notebooks (memória diz Insta posta pelo HTTP
do PC1; se for assim, o Insta dos notebooks não importa e é só desmarcar).

## 06:20 — PARADO a pedido do chat dos curtos (claude-dc)
A conferência segurava x200ma/acer 15 min por perfil e o Veo das SOLARES (prioridade 1) ficou sem máquina (reel da
Globo 09:20). Parei todos os conferir_logins. NÃO relançar antes das 10h. Faltou: x200ma/acer/pc2 terminarem e o desktop
inteiro (ver porta fixa). Ao relançar: uma máquina por vez, fora do horário do Veo das solares.

## 06:40 — desktop: hipótese do "Chrome esquecido" DESMENTIDA
chrome.log do desktop: cada perfil abriu e fechou certo na 9460; nada escutando na 9460 agora; sem portproxy.
Preferences de 5 perfis têm o e-mail certo de cada conta. Causa ainda aberta: (a) Studio abre o último canal usado e o
UCCF2 (cartuchoreact da 2030) pode ter virado canal compartilhado (Collabs 02/11?); (b) cookie de TikTok copiado entre
perfis (todos dão o @ da maite). Chat dos curtos (claude-dc) desligou o TikTok pelas máquinas até confirmar.

## Pendências da dona (não são da madrugada)
- Kaggle: token da emersongencshin (Chrome no rnprmtfo-5, IP 185.72.242.159); alxservicesia — por qual IP foi criada.
