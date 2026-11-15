# Ideias de fluxo ainda NÃO feitas no n8n6 (levantado em 02/11/2026)

## ▶ PRÓXIMO PROJETO (dona, 03/11) — começar assim que o Editor V6 fechar
2 fluxos novos:
1. **Criação de mascote**: como a mascote dos canais de hoje (ver memória project_mascote_viva: castanho dourado,
   biquíni, entra ANDANDO no 16:9; tarefa MascoteProducao no PC).
2. **Inserção da mascote no vídeo**: versão melhorada do Editor de Reels (V6) que põe a mascote dentro do vídeo.
Não mexer no V6 para isso: fluxos separados.

As listas originais (`ideias_site.md`, `ideias_fluxos_grandes.md`, `CONSTRUCAO_FLUXOS.md` em
C:\Users\Haylla\.gemini\antigravity\scratch\fluxos\) sumiram do disco; reconstruído das conversas de 13/10, 19/10 e
21/10 e conferido contra os 50 fluxos ativos do n8n6.

## Lista de 13/10 (a mais antiga)
- 6 · Raio-X de empresa pelo CNPJ (BrasilAPI → perfil, dores, automações para oferecer, mensagem de abordagem)
- 7 · Auditoria de site com IA (Jina Reader + velocidade → relatório com nota e plano de ação)
- 9 · Chatbot do site treinado com o próprio site (widget para colar em qualquer página)
- 10 · Link na bio com IA (estilo Linktree)
- 12 · Pesquisa de satisfação (NPS) com análise de IA e alerta de nota ruim
- 14 · Fluxos como ferramentas do Claude/ChatGPT (MCP Server Trigger)
- 15 · Resumo diário de notícias do nicho no WhatsApp (Google News RSS)
- 16 · Monitor de concorrente (site muda preço/promoção → aviso)
- 17 · Currículo + portfólio online
- 18 · Contrato simples de prestação de serviço (precisa revisão humana)
- Hub de eventos do Instagram (comentário→DM, DM catálogo, moderação, menções) — esperando decidir o callback da Meta

## Lista de 19/10
- Painel a partir de planilha (Excel/CSV → dashboard com gráficos e análise)
- Quiz ao vivo tipo Kahoot (código, celular dos alunos, placar ao vivo)
- Livro infantil personalizado (nome + tema → história ilustrada)
- Plano de aula + atividades + prova com gabarito (versão online que corrige sozinha)

## Ranking de 21/10 (23 ideias; 14 prontas)
- "NotebookLM caseiro": PDF → resumo, flashcards e podcast de 2 vozes
- Dublagem de vídeo
- Encarte de ofertas (folheto de supermercado/loja)
- Raio-X de concorrentes
- Kit visual da marca
- (deixadas de fora na época: dieta, foto de produto por IA, jingle, avatar falante)

## Análise de 14/11 (depois do Cardápio apresentado em 13/11) — conferido contra os fluxos ativos do n8n6
Família "comércio local", continuação do Cardápio (reaproveita página + WhatsApp + painel + push do PWA + tela da Fila):
- A1 · Pedido com rastreio + tela da cozinha (recebido → preparo → saiu → entregue; aviso no celular; tempo médio)
- A2 · Comanda de mesa por QR (pede da mesa, cozinha/garçom recebem, fecha conta no Pix, divide a conta)
- A3 · Avaliação pós-pedido (NPS): nota ruim avisa o dono, nota boa recebe o link de avaliação do Google
- A4 · Reativação de cliente sumido (sem pedir há 30 dias → cupom escrito pela IA no WhatsApp; mede retorno)
- A5 · Caixa do dia por áudio/foto no WhatsApp (vendas e despesas → planilha + relatório semanal com IA)
- A6 · Estoque + ficha técnica por foto da nota (alerta de acabando, custo do prato, preço sugerido)
- A7 · Encarte de ofertas do dia gerado do próprio cardápio (arte + Status + TV)
- A8 · Orçamento por foto (oficina, marcenaria, conserto: foto → estimativa → Proposta com Pix)
### ▶ ESCOLHIDO pela dona (14/11): A2 Comanda — foco num PAINEL ADMINISTRADOR excelente
Problema do Cardápio (8ldocDEQL74f9C50): o "Painel do dono" é só GET que lê pedidos; não cria/edita produto, não sobe foto.
Base = app do Açaí (VPS 157, backup diário em /root/backups-acai-remoto; SQLite com usuarios+papel, categorias com
ícone/ordem, itens com preco_antigo/destaque/disponivel, clientes com etiquetas, cupons, resgates, entregadores,
followups/envios, conversas, atividades, push_inscricoes). O Açaí NÃO tem caixa nem estoque → novidades.
Módulos do painel: Produtos (CRUD + foto do celular + adicionais + esgotado em 1 toque + descrição pela IA),
Mesas (QR para imprimir, mapa livre/ocupada/pediu conta), Comanda (garçom lança, transfere/junta, divide, 10%),
Cozinha/Bar (tela com tempo, "pronto" avisa o garçom), Caixa (abertura com troco, sangria/suprimento, fechamento
por forma de pagamento com diferença), Estoque (insumos, ficha técnica com baixa automática, alerta de mínimo,
entrada pela foto da nota, custo e margem), Clientes/cupons/fidelidade, Relatórios (dia/hora/produto/garçom, curva
ABC, análise semanal da IA), Equipe com papéis + registro de atividades (quem cancelou item), Configurações.
Dados: muitas tabelas relacionadas → avaliar Postgres (postgres2) em vez de só Redis.

Prospecção (vender o fluxo):
- B1 · Caçador de clientes: negócios da cidade por nicho → sem site/cardápio → Raio-X + mensagem pronta (junta 6, 7, 16)

## Fora de alimentação (14/11) — dona pediu sair desse nicho
- C1 Ordem de serviço (oficina/assistência: fotos antes/depois, aprovação do orçamento, status por link, garantia)
- C2 Clínica/consultório (anamnese online, prontuário simples, retorno automático, receita/atestado em PDF)
- C3 Imobiliária (cadastro de imóvel por fotos → anúncio + página, visita agendada, lead com nota)
- C4 Academia/personal (treino com vídeo, check-in por QR, mensalidade com aviso de atraso, evolução)
- C5 Escola/curso livre (chamada por QR, boletim, aviso aos pais, mensalidade)
- C6 Salão/barbearia com comanda e comissão por profissional (Agenda já existe; falta caixa+comissão)
- C7 Condomínio (reserva de espaço, avisos, ocorrências com foto, encomendas na portaria)
- C8 Pet shop (ficha do pet, vacinas com lembrete, banho e tosa com foto "pronto")
- C9 Controle financeiro pessoal/MEI pelo WhatsApp (áudio/foto → planilha, DAS, relatório)
- C10 Locação de equipamentos/aluguel de roupa (calendário de disponibilidade, contrato, caução)
- C11 Igreja/ONG (membros, dízimo/doação Pix, escalas de voluntários, avisos)
- C12 Vistoria/checklist com fotos → laudo em PDF (técnico, imóvel, carro)

## Análise de 14/11 (noite) — depois da Comanda e da Vitrine de Imóveis
Base nova reaproveitável: banco Postgres apps_aulas + função *_api(jsonb) + painel com papéis (padrão comum/),
fotos no banco, IA com visão, vídeo pelo fluxo de anúncio, oficina (fotos_b64, guardar_video, pasta vitrines).
TOP para as próximas aulas (fora de alimentação):
1. D1 Ordem de Serviço (oficina mecânica, celular, refrigeração): fotos antes/depois, orçamento que o cliente aprova
   pelo link, status ao vivo, peças do estoque, garantia em PDF, IA olha a foto do defeito e sugere o diagnóstico.
2. D2 Vitrine de Carros (revenda): mesma base da Vitrine de Imóveis; IA lê a foto do documento/painel (km, ano),
   tabela FIPE pela API pública, simulação de financiamento, vídeo por carro. Rápido de fazer (~70% reaproveitado).
3. D3 Salão/Barbearia completo: agenda (já existe) + comanda + caixa + comissão por profissional + pacotes;
   reaproveita o caixa da Comanda.
4. D4 Vistoria com fotos → laudo PDF (imóvel de aluguel entrada/saída, carro): IA descreve cada cômodo/foto,
   compara entrada x saída e aponta danos; assinatura no celular.
5. D5 Loja/Catálogo com estoque e variações (roupa, cosmético): vitrine de produtos + carrinho no WhatsApp + estoque
   por tamanho/cor + IA tira o fundo e escreve a descrição pela foto.
6. D6 Clínica/Consultório (estética, fisio, nutri): anamnese online, prontuário com fotos de evolução, retorno
   automático, pacote de sessões; IA resume a anamnese.
7. D7 Academia/Personal: check-in por QR, treino com vídeo, mensalidade com aviso, avaliação física com evolução.
8. D8 Caçador de clientes (B1): acha negócios da cidade sem site → raio-x + mensagem; vende os fluxos acima.
Menores / rápidos: NPS pós-atendimento (serve para todos), Link na bio com IA, Quiz ao vivo tipo Kahoot (aula).
Melhorias dos 2 novos: impressão térmica da cozinha, alerta de estoque no celular, simulador de financiamento,
botão "postar no Instagram", link de demonstração preenchido.

## Instagram fora da caixa (14/11 noite)
Já existem: Carrossel com aprovação, Relatório do perfil, Post conversado (off), 30 dias de posts, Sorteio parte 1,
Editor de Reels V1-V6, Vídeo de anúncio, Cortes; antigos (set/2025-jan/2026, desligados): agente que responde DM,
agente que responde comentário, comentário→direct, multi atendimento, Fábrica Viral posta, repostagem de short.
Trava: eventos (comentário/DM/menção) dependem do callback único do app Meta (hoje no sorteio) → decidir antes.
Ideias novas:
- I1 Instagram vira site/loja em 1 min (listMedia+getMyProfile → IA monta site com produtos e preços das legendas)
- I2 Leilão/drop relâmpago nos comentários (lance no comentário, placar, fecha com Pix no DM)
- I3 Jogo/quiz de personalidade por DM (quick replies → resultado em imagem para repostar no story)
- I4 Gincana nos Stories (pistas diárias, resposta por DM, ranking, prêmio)
- I5 Escudo da marca (oculta golpe/spam/ofensa, responde dúvida, avisa o dono) — o "hub" pendente, com nome vendável
- I6 Menção vira cliente fiel (cliente marca a loja no story → DM de agradecimento + cupom + pedido de repost)
- I7 Autopiloto dos sistemas: Vitrine/Comanda/Cardápio publicam sozinhos (imóvel novo → Reel+carrossel; prato do dia → story)
- I8 1 vídeo vira 1 semana (YouTube/live/podcast → cortes + carrosséis + legendas + agenda)
- I9 Prova social automática (depoimento por DM → arte + carrossel de depoimentos)
- I10 Sorteio com vídeo-prova (roleta animada vira Reel + página de transparência) — completa o sorteio parte 1
- I11 Raio-X de concorrente (Business Discovery da Graph API: só contas comerciais; testar se o token permite)

FEITOS em 14/11: I1 (Instagram vira site), I4 (Gincana nos stories), I6 (Menção vira cliente fiel), I10 (Sorteio com vídeo)
→ tudo na "📸 INSTAGRAM · Central" (aU1mIOMFwyEkAjnf).

## Já prontos (não repetir)
Proposta comercial, Cardápio, Leads, Métricas, 30 dias de posts, Quiz funil, Agente com ferramentas, App PWA,
Apresentação, E-book, Curso online, Campanha de anúncios, Site de evento, Agenda online, Cartão fidelidade, Fila e
senha, TV do estabelecimento, Spot de áudio, Cortes automáticos, Vídeo de anúncio (fotos), Editor de vídeo (recap),
Editor de Reels (V1–V4), Carrossel/Relatório/Post conversado do Instagram, Revisão de livro, Narrador, Imagens,
Clipes LTX, Fábrica de vídeos, Radar dos canais, Ponte PC.
