# Contestações — recursos avançados do YouTube (acompanhar)

Dona 06/11/2026: "vamos acompanhar o retorno das contestações, deixe documentado".

## Por que os canais perderam
O aviso do YouTube é o mesmo em todos: *"Acreditamos que você já violou as políticas do YouTube antes"*. Não foi
infração nova. Causa mais provável: os canais estão **ligados** (mesmas contas Google, mesmo IP de casa, collabs
entre eles). Os robôs pioravam esbarrando no bloqueio ~70 vezes (fixar comentário, teste A/B, vídeo relacionado).

**Corrigido:**
- `bin\trava_conta.py`: na 1ª negativa o canal entra em `config\recursos_negados.json` e nenhum robô tenta de novo
  até a data.
- **Collabs DESLIGADAS** em 06/11: tarefa `CollabsYouTube` desabilitada. 23 collabs completas deram mediana de 3
  views, contra 5 sem collab, e mostravam ao YouTube que os canais são da mesma dona.

## Situação de cada canal

| Canal | Perdeu em | Contestação | Prazo para contestar | Pode pedir de novo |
|---|---|---|---|---|
| Assist-IA Investimentos | antes de 05/11 (suspensão anterior) | **sem botão de contestar** | — | 29/11/2026 |
| inovare manhwa br | 04/11 14:56 | **dona contestou 05/11** | 03/01/2027 | 04/12/2026 |
| CenaReact | 04/11 22:10 | **dona contestou 05/11** | 03/01/2027 | 04/12/2026 |
| ForjaReact | antes de 05/11 | **contestação NEGADA** (tela 05/11 12:48) | — | ? |
| InovareManhwaVerse | 05/11 | não contestado | ver no Studio | 15/11/2026 |
| Animescomia | 05/11 | não contestado | ver no Studio | 04/12/2026 |
| Curiosidades Noturnas | 05/11 | não contestado | ver no Studio | 03/01/2027 |
| InventoReact | **06/11 11:11** (teste A/B de capa) | **tela aberta pra dona em 06/11** | 03/12/2026 | 02/01/2027 |
| HistoriasEmFrames | 06/11 03:39 | não contestado | ver no Studio | 02/01/2027 |
| Dorama Noturno | 06/11 03:44 | não contestado | ver no Studio | 03/01/2027 |
| **Fio da Meada** | **06/11 14:31** — horas DEPOIS da verificação por rosto da dona | não contestado — **é o melhor canal de longos: contestar primeiro** | ver no Studio | 05/01/2027 |

Outros punidos (não são "recursos avançados"):
- **inovare_ita:** canal REMOVIDO por nudez. Contestar até 03/11/2027 ("Iniciar análise").
- **inovare_hindi:** "Muitos avisos", envio bloqueado (trava até 12/11).
- **mundoquenaoexiste:** STRIKE de direitos 01/11. Dona precisa abrir "Review details".
- **Fio da Meada:** recursos avançados "Qualificado"; dona verificou com rosto em 06/11. Conferir se ficou "Ativado".

## PENDENTE da dona — conferência do STI em 12/11/2026 (lembrar de fazer)
Telas tiradas pela conferência de logins do notebook STI: `D:\postador-de-videos\logs\tiktok_tela\sti_<perfil>_*_conferir_youtube.png`.

| Conta | O que fazer | Prazo |
|---|---|---|
| **inovarecap** (canal "Inovare inteligência artificial", removido por spam/práticas enganosas) | Antes: arrumar os **dados de login** da conta Google (no STI o Google pede SMS e recusa o número +55 19958719194, "usado muitas vezes"). Está logada no PC1 (`D:\logins-google\cofre\perfis\inovarecap`) e no Acer. Depois: Studio → **Iniciar análise** → enviar contestação | **03/09/2027** |
| **gabriellyvitoriaisabelaaraujo** | Aviso de remoção por direitos autorais (Advertência 1, 08/11/2026): "Solicitar retratação" ou "Enviar contranotificação" | ver no Studio |
| **inovaremanhwaversefrench** | 2 de 3 advertências por direitos autorais ativas: ver se alguma dá para contestar (a 3ª remove o canal) | ver no Studio |
| **rezaulkarimul355** | 1 advertência por direitos autorais ativa: ver se dá para contestar | ver no Studio |
| **inovaremanhwaverse** | 1 advertência de direitos autorais + 1 de diretrizes da comunidade (canal ativo): ver se dá para contestar | ver no Studio |

Sem contestação possível (tela "No momento, seu canal não será restabelecido": prazo vencido ou já negada), não
precisa abrir: aulasrevolution, comoseriasecomia, emersonjosiel649, emersonjosielmrx1995, en1653964,
fabricadeautomacoes0, fabricadeautomacoesia, filmescomia00, filmescomia1, gameoftroneskingsroadbrasil,
inovaremultiatendimento, mentoriaiapro, mundosolar1995, murilodoctor192, seebotsia, solarmundo195, vendeafiliados3.

## Como acompanhar
- O YouTube responde a maioria das contestações em ~24 h, por e-mail na conta Google do canal e no próprio Studio
  (Configurações → Canal → Qualificação para recursos).
- **Voltou** = "3. Recursos avançados" aparece **Ativado**. Aí apagar a linha do canal em
  `D:\postador-de-videos\config\recursos_negados.json` (o robô volta a fixar comentário, A/B e vídeo relacionado).
- **Negada** = aparece "Sua contestação relacionada aos recursos avançados foi negada". Anotar aqui; esperar a data
  de "pedir de novo".
- Ver o que está travado: `python D:\postador-de-videos\bin\trava_conta.py`.

## O que se perde sem recursos avançados
Vídeo relacionado (Short → longo), teste A/B de capa/título, fixar comentário, links externos clicáveis, contestar
Content ID, mais envios/lives por dia, pedir monetização (YPP). Continua: postar, miniatura, playlists, tela final.

## Pista pra dona decidir (07/11)
Os longos sobem **sem** a declaração "conteúdo alterado ou sintético (IA)" do YouTube, mesmo com a narração em voz
clonada (RVC) e capas de IA. O postador sabe marcar (`youtube_web_poster.py --sintetico`); o `postar_longos.py` só não
passa a opção. A declaração do YouTube é para conteúdo REALISTA (pessoa real dizendo o que não disse, evento que não
aconteceu); voz clonada de narrador parceiro em recap de anime é zona cinzenta. Não liguei sozinho — marcar errado
também tem efeito. Se a dona quiser: em `postar_longos.py`, `politica.postar_youtube(..., sintetico=True)`.

## Registro
- 05/11: dona contestou inovare br e CenaReact.
- 06/11: InventoReact perdeu às 11:11; tela de qualificação aberta pra dona contestar. Collabs desligadas.
- 12/11: conferência do STI achou as contestações pendentes acima; dona: "documente como pendente pra lembrar de fazer".
