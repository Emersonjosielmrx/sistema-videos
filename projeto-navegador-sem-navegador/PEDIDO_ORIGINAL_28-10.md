# Pedido original do dono (28/10, colado no chat) — ler inteiro antes de começar às 00:40

Com base no sistema que o projeto gemini-argo usa para fazer suas chamadas ao Gemini, analise todos os sistemas que temos
que usam navegador: geração de imagens e vídeos com o Veo 3 e outras ferramentas de lá que não usamos ainda, postagens de
vídeos YouTube, TikTok, Instagram e Facebook etc.

Analise cuidadosamente o máximo possível de funções de cada um que poderíamos adicionar e que ainda não usamos. Ex.: coisas
que não postamos no Instagram, como Stories; saber se foi postado ou não; se a postagem vai só como post ou se fazemos
Reels; coisas que não fazemos ainda no Veo, como vídeos estendidos e correções de vídeos já feitos, vídeos laterais,
vídeos a partir de objetos; recolhimento de análise (acho que já foi feito de um, mas podemos pegar mais dados, e de
todos); busca no Google Fotos, que podemos organizar ou transferir de um para outro mantendo tudo em um só.

Objetivo: criar primeiro as funções que já temos e as subjacentes, da mesma forma que o gemini-argo hoje — sem abrir o
navegador, só usando cookies e chamando as URLs dos endpoints — deixando testado e funcionando, para fazermos o que já
fazemos melhor e em menos tempo. Depois trabalhar nas novas para criá-las também.

Algumas que eu já desejo:

## Instagram
- **Stories** (Instagram Web com User-Agent mobile): bastidores diários, aviso de vídeo novo ("arrasta pra cima / link na
  bio"), enquetes; repostar automaticamente o Reel do dia nos Stories para dobrar o alcance nas primeiras 2 h.
- **Carrossel nativo de imagens** (post no feed, 5 a 10 imagens com design limpo, como MS Energy e Inovare) em vez de
  transformar tudo em MP4.
- **Destaques** do perfil: "Quem Somos", "Instalações", "Serviços", "Depoimentos".
- **Bio e link dinâmicos** (accounts/edit): trocar conforme o produto/campanha da semana (landing ativa).
- **DMs e comentários**: quem comentar "QUERO" ou mandar DM recebe o link do WhatsApp/landing.
- **Meta Business Suite** (business.facebook.com com a sessão do cofre): agendar posts e Reels com semanas de antecedência
  sem token da Graph API de 60 dias.

## Veo / Flow
- **Estender vídeo** (+4 s / +8 s) até 16–24 s contínuos, mesma câmera e física.
- **Correção/reprompt na mesma conversa** ("troque o fundo por dia ensolarado", "aproxime a câmera mais rápido").
- **16:9 (LANDSCAPE 1920x1080)** para YouTube longo (hipercool, curiosidades, recap longo).
- **Imagem→vídeo com foto real** (veo_3_i2v_fast): foto de instalação da MS Energy, capa de manhwa etc.
- **Quadro inicial + final** (veo_2_1): antes/depois (telhado vazio → instalação pronta).
- **Loop perfeito** (veo_2_0_i2v_loop): fundos de narração e retenção infinita no TikTok/Reels.
- **Personagem fixo** pela biblioteca "Characters" (@nome): narrador/mascote.

## Analytics (sem cota de API)
- **YouTube Studio**: retenção de Shorts (viram x pularam; >75% viraliza), retenção segundo a segundo (onde o público sai →
  feedback para a IA de roteiro), CTR das miniaturas, termos de busca reais (para tags e títulos).
- **TikTok**: tempo médio, taxa de conclusão, origem do tráfego (Para Você x pesquisa).
- **Instagram Insights** (Meta Business Suite): alcance, contas atingidas, salvamentos e compartilhamentos por post.
- **Central unificada** (já existe meio que o mapa de conteúdo; com mais dados, mais perguntas): script diário que cruza os
  três — qual nicho deu mais inscritos hoje, qual estrutura de título teve maior CTR, quais vídeos zeraram e devem ser
  reeditados ou apagados.

## Google Fotos
- **Compartilhamento com parceiro**: conta secundária compartilha tudo com a principal (mundosolar1995 ou emersonjosiel),
  principal ativa "salvar automaticamente" → tudo centralizado sem baixar nada no PC.
- **Álbuns temáticos** por empresa/projeto ("MS Energy - Placas e Inversores", "MS Energy - Instalações Reais", "Rostos e
  Modelos", "Vídeos de Clientes") para os geradores pegarem pela URL do álbum.
- **Limpeza de lixo e cota (15 GB)** — `limpar_fotos_lixo.py`: quotamanagement, apagar vídeos gigantes duplicados, prints
  antigos, fotos borradas; esvaziar a lixeira. (As contas precisam de espaço para o Gmail receber códigos e o Drive
  funcionar.)
- **Catálogo com visão** (Gemini Flash): tags automáticas ("painel solar no chão", "telhado colonial", "inversor string")
  num JSON/SQLite local para o gerador de vídeos puxar na hora.

Lembrete: isso é para fazer quando chegar o cron das 00:40. Já existe o projeto "navegador sem navegador"
(D:\projeto-navegador-sem-navegador), cheio de erros, mas que pode ser aproveitado.
