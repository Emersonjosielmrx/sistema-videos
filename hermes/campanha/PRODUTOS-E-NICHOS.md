# Produtos e nichos para a campanha

Escrito em 14/10/2026, a pedido da dona: abrir a campanha para além do Hermes Call de voz. A ideia é oferecer
do produto pequeno (site) ao grande (sistema completo), medir quais vendem e colocar as ligações nos que
vendem. As ligações são o recurso escasso: hoje são **48 por dia numa linha só (a 8653)**.

**Regra: o cliente nunca vê o n8n.** Ele recebe um sistema com o nome dele (painel do Hermes, página própria,
número dele). O n8n é só a nossa oficina.

---

## 1. O que existe hoje (conferido em 14/10)

| Onde | Fluxos | Diferentes | Ativos |
|---|---|---|---|
| n8n6 (servidor 157) | 1.894 | | |
| n8n do servidor de teste (209) | 909 | | |
| **Total** | **2.803** | **830** | **179** |

A maioria são cópias e backups (tags "Recuperado", "Rec - Backup"). Um só fluxo, "My workflow 106", tem 295
cópias. Os 830 diferentes se dividem assim:

- **Atendimento no WhatsApp**: a maior parte. Agentes por nicho, peças de agente (entender áudio, foto, PDF e
  vídeo, juntar mensagens picadas, responder em áudio, chamar humano, memória), follow-up, recuperação de
  carrinho, agenda, Pix. São 306 aulas com a tag `aula-fluxo`.
- **Sites e páginas**: cerca de 25 sites prontos por nicho, um gerador de landing page por IA, captação de leads
  com nota da IA e métricas de visita.
- **Cardápio e vendas**: cardápio digital com pedido no WhatsApp, vitrine de produtos com foto e confirmação de
  pedido, agente com frete e Pix.
- **Instagram**: responde direct e comentário, carrossel com aprovação e agendamento, relatório do perfil, post
  conversado, sorteio.
- **Marca e pesquisa**: Brand OS (gera o manual da marca) e Quadro Norteador de Pesquisa.
- **Conteúdo e vídeo** (uso interno): fábrica de animes, fábrica viral, postadores de YouTube, TikTok e Instagram.
- **Infra interna**: roteador de IA, backups, limpeza de servidor, testes de chaves.

O Hermes já tem, pronto e cobrado por plano (`plan_features.go`):
- **Start Voz (R$199)**: ligações com IA.
- **Start Texto (R$199)**: agente de atendimento no WhatsApp por texto.
- **Pro (R$399)**: tudo menos IA em reuniões, inclusive Agenda e Vitrine de Produtos (catálogo público com fotos,
  estoque, descrição por IA e importação de produtos de um site).
- **Scale (R$599)**: tudo.

O Hermes também lê pedidos feitos pelo catálogo do WhatsApp Business.

---

## 2. Escada de produtos (do menor para o maior)

O preço dos produtos novos é decisão da dona; aqui só a ordem. Os do Hermes já têm preço.

| Degrau | Produto | O que o cliente recebe | Já pronto | Falta para virar produto |
|---|---|---|---|---|
| 1 | **Site / página do negócio** | site de 1 a 12 páginas, com botão de WhatsApp | ~25 sites de nicho (abaixo) + "Gerador de Landing Page por IA — PRO" (ativo) | domínio próprio do cliente (hoje a página sai do endereço do n8n) |
| 1+ | **Site + leads com nota da IA** | o site guarda cada contato, a IA dá nota de 0 a 10 e avisa quem atender primeiro | "Leads das Landing Pages com Nota da IA" e "Métricas das Landing Pages" (ativos) | igual ao de cima |
| 2 | **Cardápio digital com pedido no WhatsApp** | o dono cola o cardápio (até bagunçado) e recebe um cardápio com busca e carrinho; o pedido chega pronto no WhatsApp dele | "Cardápio Digital com IA + Pedidos no WhatsApp" (ativo, 14/10), "VITRINE — envio de produto com imagem e confirmação do pedido", "Agente com ferramentas: frete, Pix e informação nutricional" (ativo) | trazer o carrinho para a Vitrine do Hermes, ou vender como produto à parte |
| 3 | **Atendente IA no WhatsApp (texto)** = Hermes **Start Texto R$199** | responde 24h, entende áudio e foto, marca horário, chama humano, faz follow-up | Hermes Start Texto + modelos de nicho do n8n (seção 3) | o roteiro e a base de conhecimento de cada nicho dentro do Hermes |
| 4 | **Instagram com IA** | responde direct e comentários, cria e agenda posts e carrosséis, relatório do perfil | 5 fluxos ativos no n8n6 | **o Hermes não tem Instagram**; hoje só pelo n8n (um app da Meta por cliente) |
| 5 | **Ligações com IA** = Hermes **Start Voz R$199** | IA que liga para a lista do cliente (reativar base, cobrar, confirmar) | Hermes (é o que a campanha já usa) | nada |
| 6 | **Sistema completo** = Hermes **Pro R$399 / Scale R$599** | voz + WhatsApp + CRM + agenda + vitrine + gestor | Hermes | nada |
| 7 | **Sob medida** (Enterprise) | multiagente, várias empresas e números, integrações | "Hub N8n Multi-Empresa", "AGENTE PRO 2.0", multiagente com Notion | orçamento caso a caso |

**Sites prontos por nicho** (n8n, fluxos de 3 a 36 blocos): imobiliária (11 páginas), gráfica (11),
corretora de seguros (11), empréstimos (11), contas (12), advocacia (divórcio e trabalhista), estética, cabelo,
clínica capilar, psicólogo, saúde mental, plano de saúde, casamento, turismo, cursos de idioma (francês,
português), carros, máquinas, tratores, aromas, loteria online.

---

## 3. Nichos: produto de entrada, modelo pronto e lista

O **produto de entrada** é o que a ligação oferece primeiro: o mais fácil de dizer sim. Depois a gente sobe
a escada com quem comprou.

| Nicho | Produto de entrada | Modelo pronto no n8n | Lista pela Receita (CNAE) |
|---|---|---|---|
| Lanchonete, hamburgueria, açaí, pizzaria | Cardápio digital (2) | Cardápio Digital, "delivery novo", "base_da_comunidade__delivery", "frango" | 5611-2/03 lanchonetes, 5611-2/01 restaurantes *(a acrescentar)* |
| Delivery, marmita, comida congelada | Cardápio digital (2) | "comida congelada", "delivery novo" | 5620-1/04 alimentos para consumo em casa *(a acrescentar)* |
| Restaurante | Cardápio (2) → atendente (3) | "restaurante" | 5611-2/01 *(a acrescentar)* |
| Mercadinho, supermercado | Cardápio/vitrine (2) | "supermercado" | 4712-1/00 e 4711-3/02 *(a acrescentar)* |
| Barbearia, salão | Atendente que marca horário (3) | "Barbearia_BigodeGrosso", "Barbearia: Agenda AI", "base_da_comunidade__barbearia" | 9602-5/01 *(a acrescentar)* |
| Dentista, clínica, estética | Atendente que marca consulta (3) | "dentista", "agendamento dentista por link", "clinica estetica", "inovare_saude_template" | já na captação (`clinicas_consultorios`, `estetica`) |
| Nutricionista, psicólogo | Site (1) → atendente (3) | "nutricionista aula v1 a v6", site psicólogo | já na captação (`clinicas_consultorios`) |
| Advocacia | Site (1) → atendente (3) | "advogada", "advogado trab", sites de advocacia | 6911-7/01 *(a acrescentar)* |
| Imobiliária | Ligações (5) → completo (6) | site imobiliária (11 páginas) | já na captação: **piloto atual** |
| Hotel, pousada | Atendente de reserva (3) | "base_da_comunidade__hotel e pousadas" | 5510-8/01 *(a acrescentar)* |
| Energia solar | Atendente + ligações (3/5) | "energia solar geral mais completo", "sistemas solares", "solar meu ms" | 4321-5/00 *(a acrescentar; também pega eletricistas)* |
| Provedor de internet | Atendente de suporte (3) | "provedor" | já na captação (`provedores_internet`) |
| Gráfica | Site (1) | site gráfica (11 páginas) | 1813-0/01 *(a acrescentar)* |
| Corretora de seguros, financeira | Ligações (5) | sites de seguros e empréstimos | já na captação |
| Agência de marketing | Revenda de tudo (7) + Brand OS | Brand OS, Quadro Norteador, Instagram | já na captação (`agencias_marketing`) |

Os CNAEs marcados *(a acrescentar)* não estão em `captacao\cnpj\segmentos.json`. Todos foram conferidos em 14/10 na
tabela oficial da Receita (`Cnaes.zip` da captação) e existem. Também conferidos: padaria (4721-1/02, 1091-1/02),
pet shop (4789-0/04, 9609-2/08), pousada e outros alojamentos (5590-6/99) e bares (5611-2/04, 5611-2/05).
Só entram no `segmentos.json` quando a dona escolher o nicho: alimentação deixa a base da captação bem maior.

Já fizemos sistemas desse modelo para clientes reais: advocacia, instituto de ensino, empresa de tecnologia,
órgão público, restaurante e informática (todos variações do fluxo "MODELO DE ATENDIMENTO DE TESTE GRATIS").

---

## 4. Como testar com poucas ligações

**Conta de hoje:** 48 ligações por dia → ~30% atendem (14/10: 7 de 23) → **~14 conversas por dia, ~70 por semana**.

**O que as primeiras ligações já ensinaram:** 5 de 7 desligaram nos 5 segundos da abertura genérica ("Oi, aqui é
da Inovare…"). Então **cada nicho precisa de abertura e oferta próprias**, que falem da dor dele logo na
primeira frase. Por exemplo, para uma lanchonete: *"É da [nome]? É rapidinho: vocês já recebem pedido por
cardápio no WhatsApp?"*

**Como montar:**
1. **Uma campanha por par nicho + produto** (um "braço"), cada uma com o seu agente: abertura, oferta, roteiro e
   base de conhecimento do nicho.
2. **Dividir as 48 da linha** entre os braços. A soma dos limites diários das campanhas não pode passar de 48.
   Exemplo: 3 braços × 16 por dia.
3. **Uma semana por rodada**: ~80 discadas e ~24 conversas por braço. É pouco para cravar taxa, mas basta para
   ver quem nem passa da abertura.
4. **Medir por braço:**
   - quantos ouvem a oferta inteira (registro "áudio 2 (oferta) tocado");
   - quantos conversam mais de 30 s;
   - quantos se interessam;
   - quantos marcam demonstração;
   - quantos compram.
5. **Fim da semana:** sai o pior braço, entra um nicho novo. O que vende ganha mais ligações e é o primeiro a
   usar o 2º número.
6. **Ter a demonstração pronta antes de ligar:** um cardápio de exemplo, um site de exemplo do nicho, o atendente
   respondendo no WhatsApp. O Hermes vende melhor mostrando do que explicando.

**Sugestão para a 1ª rodada** (a dona decide):
- **Lanchonete/delivery + cardápio digital**: produto barato e visual, quem decide é o dono e tem muita empresa.
- **Dentista/clínica + atendente que marca consulta**: a dor é clara e já temos vários modelos prontos.
- **Imobiliária + ligações**: continua o piloto atual, com abertura nova.

**Limite real:** com um número só (o celular da dona), cada nicho a mais divide as mesmas 48. Para testar muitos
nichos ao mesmo tempo precisa do **2º número** (item 0.2 do PLANO).

---

## 5. O que não oferecer

- **Disparo em massa, maturador de número, raspagem de grupo do WhatsApp** (há vários fluxos disso no n8n). Vão
  contra as regras do WhatsApp e a LGPD, e o PLANO já proíbe número tirado de grupo. Bloqueio aqui derruba o
  Hermes.
- **Robô de trader/Binance, bot financeiro pessoal**: fora do público.
- **Fábricas de vídeo e postadores de YouTube**: ferramenta nossa. Talvez um dia para agência, não agora.

---

## 6. Decisões da dona

1. Quais 2 ou 3 braços entram na próxima rodada.
2. Preço do site, do site com leads e do cardápio digital (os produtos fora do Hermes).
3. Se o cardápio com carrinho entra na Vitrine do Hermes ou fica como produto à parte.
4. Se o Instagram entra no Hermes ou continua só pelo n8n.
5. A abertura nova da campanha das imobiliárias.
