# Painel de Orçamentos MS Energy — arquitetura e operação

> Caminho do código: **PC1 `D:\ms-energy\painel-orcamentos\`** (cópia de referência) → publicado na **VPS 62.171.128.241
> (`ssh hermes-prod` a partir do PC1) em `/opt/orcamentos-ms/`**. Endereço: **https://orcamentos.opus-sem-limites.com.br**
> Criado em 27/11/2026 a pedido da dona: “painel para os vendedores fazerem seus orçamentos, o mais bonito e moderno
> possível, visual baseado no Hermes Call, hospedado na mesma VPS, com o máximo de opções”.

## 1. O que é
Site onde cada vendedor da MS Energy entra com usuário e senha e monta a proposta de energia solar do cliente em
6 passos (cliente → consumo → sistema → itens extras → preço e pagamento → revisão). O sistema dimensiona sozinho
(painéis, inversor, cabos, estrutura), calcula preço, economia, payback e TIR, e gera **a mesma proposta em PDF** que era
feita à mão em `D:\ms-energy\propostas\gerar_proposta.py` (9–10 páginas A4). Cada orçamento ganha um número
(`MSaamm-0001`) e um **link público** para o cliente (`/p/<token>`) com botão de baixar PDF e falar no WhatsApp do
vendedor. O painel conta quantas vezes o cliente abriu.

## 2. Peças
| Arquivo | Função |
|---|---|
| `servidor/motor.py` | Contas e HTML da proposta (porte do `gerar_proposta.py`). `CONFIG_PADRAO` = preços/catálogo iniciais. |
| `servidor/app.py` | FastAPI: login (cookie + PBKDF2), API, PDF (Chromium via Playwright), página pública, métricas. |
| `servidor/web/` | Painel (HTML/CSS/JS puro, sem build). Visual Hermes: fundo quase preto, verde `#22c55e`, ícones Lucide. |
| `servidor/img/` | Fotos usadas na proposta (copiadas de `D:\ms-energy\propostas\_img`). |
| `servidor/dados/` | **Volume com os dados**: `banco.sqlite`, `pdf/` (cache 7 dias), `CREDENCIAIS_INICIAIS.txt`. |
| `servidor/Dockerfile`, `docker-compose.yml` | Contêiner `orcamentos-ms`, porta **127.0.0.1:8101** (fechada para a internet). |
| `traefik-orcamentos.yml` | Copiado para `/opt/traefik-config/dynamic/orcamentos.yml` (rota + HTTPS Let's Encrypt). |
| `instalar_vps.sh` | Sobe/atualiza na VPS. `--build` reconstrói a imagem (só precisa se mudar o Dockerfile). |

## 3. Decisões
- **Mesma VPS do Hermes, sem tocar nele**: segue o padrão do `painel-clientes` (contêiner próprio + arquivo de rota do
  Traefik). Só se mexe em `/opt/orcamentos-ms`, no contêiner `orcamentos-ms` e em `dynamic/orcamentos.yml`.
- **SQLite** (um arquivo) em vez de Postgres: pouca escrita, backup = copiar `dados/`.
- **PDF no servidor com Chromium** (igual ao gerador original) → o PDF sai idêntico ao que já foi aprovado.
- **Código por volume**: atualizar = copiar `app.py`/`motor.py`/`web/` e `docker restart orcamentos-ms`.
- **Preço sugerido = fixo + R$/kWp × kWp + adicionais** (híbrido, solo), calibrado nas propostas feitas à mão:
  3,75 kWp = R$ 13.900 e 7,5 kWp = R$ 22.900. Itens extras e baterias somam o preço de catálogo. Tudo editável pelo
  administrador em **Catálogo e preços**. Vendedor tem desconto máximo (padrão 5%); acima disso só o admin salva.
- **Baterias viram opções de preço** (sem bateria / com cada bateria), cada uma com a sua página de pagamento — como
  nas propostas híbridas de 25/11.
- Pagamento padrão = o que a dona definiu nas propostas de novembro: 50% em 21×; 50% em 3× boleto ou 12× cartão;
  financiamento Solfácil 120× 2,15%, BV 96× 2,19%, Santander 96× 2,29% com o aviso “parcela estimada … score de crédito”.

## 4. Funções do painel
- **Visão Geral**: orçamentos, valor orçado, ticket médio, vendas fechadas, taxa de fechamento, gráfico por dia, funil
  por status, “retornar hoje”, clientes que abriram a proposta, ranking de vendedores (admin), meta e comissão (vendedor).
- **Novo orçamento** (atalho `N`): consumo por kWh, valor da conta ou 12 meses; folga; on-grid / híbrido / micro;
  painel; nº de painéis e inversor automáticos ou manuais; telhado/solo; itens extras com quantidade e preço; item livre;
  cortesia; baterias; preço manual com limite; à vista com desconto, parcelamento direto, cartão, entrada + financiamento,
  escolha das financeiras, tabela de parcelas 24×–120×; observações; texto “por que esta solução”; status e data de
  retorno; prévia da proposta; resumo ao vivo; validação de CPF/CNPJ.
- **Orçamentos**: busca, filtros (status, vendedor, tipo, datas), ordenação, planilha CSV, WhatsApp, PDF, copiar link,
  duplicar, mudar status (com motivo da perda), apagar, gaveta com histórico e anotações.
- **Clientes**, **Simulador rápido** (com “copiar resumo para o WhatsApp”), **Catálogo e preços**, **Vendedores**
  (meta, comissão, senha nova, desativar), **Dados da empresa**, **Minha conta**, tema claro/escuro, celular.

## 5. Operação
Na VPS (`ssh hermes-prod` a partir do PC1):
```
cd /opt/orcamentos-ms && bash instalar_vps.sh            # sobe/atualiza
docker logs --tail 50 orcamentos-ms                       # registro
cat /opt/orcamentos-ms/servidor/dados/CREDENCIAIS_INICIAIS.txt   # senha inicial do admin
cp /opt/orcamentos-ms/servidor/dados/banco.sqlite ~/backup_orc_$(date +%F).sqlite   # backup manual
```
Do Omarchy o caminho é Omarchy → `scp` para o PC1 → `"C:\Program Files\Git\usr\bin\scp.exe"` do PC1 para `hermes-prod`
(o scp do Windows falha com “lost connection”); comandos na VPS vão em base64 (`echo <b64> | base64 -d | bash`).

## 6. Ferramentas de conferência (rodam DENTRO do contêiner, na VPS)
- `prints.py`: cria 2 orçamentos de exemplo, tira prints de todas as telas (computador e celular) e do link do cliente
  em `dados/_prints/`, e no fim APAGA os orçamentos e zera o contador do mês. Uso:
  `cp /opt/orcamentos-ms/prints.py servidor/dados/_prints.py && docker exec orcamentos-ms python /app/dados/_prints.py`
- `pdf_teste.py`: gera um PDF híbrido de exemplo direto pelo motor (não grava no banco) em `dados/_prints/`.
- Apague `dados/_prints*` depois de olhar.

## 7. Armadilhas já resolvidas
- `python:3.12-slim` virou Debian 13 e o Playwright 1.49 não instala nele → a imagem usa `python:3.12-slim-bookworm`.
- Trava (`_trava`) pedida duas vezes ao criar orçamento travava o servidor inteiro → `RLock` e `proximo_num(c)` usa a
  mesma conexão.
- Cookie `secure` agora segue o protocolo real (`request.url.scheme`), senão o login não funciona em http local.
- Robôs varrem `/.env`, `/wp-...`: rotas com ponto ou desconhecidas respondem 404.
- Página de produtos com muitos itens + várias baterias estourava a folha → tabela `compacto` e preços `multi`.
- A VPS corta conexões SSH seguidas (“Connection closed by remote host”): esperar e repetir, juntar comandos num só.

## 8. Regras de preço do vendedor (27/11, pedido da dona)
- **Acréscimo oculto por vendedor** (`usuarios.acrescimo_pct`, só o admin vê/edita em Vendedores). O motor recebe
  `fator = 1 + acréscimo/100` do DONO do orçamento (nunca dos dados enviados) e aplica no preço do solar e nos preços de
  catálogo de itens extras e baterias (`motor.com_fator`, arredonda para cima em R$ 10). Luiz = vendedor, 15%.
- **Vendedor não muda regras de preço** (`app.travar_dados_vendedor`): item de catálogo nunca abaixo do catálogo,
  sem cortesia, números do pagamento sempre os da empresa (ele só liga/desliga as formas), valor final nunca abaixo do
  sugerido (pode aumentar e somar “outros custos”). `/api/config` para vendedor não traz a regra de preço nem a margem.
- **Financiamento = simulação**: toda parcela simulada leva +`pagamento.financiamento.margem_pct` (padrão 10%,
  `motor.fator_fin`), e a proposta diz em vermelho que é apenas simulação e que a parcela pode subir.
- **Orçamento fácil** (`#/facil`, botão verde do menu e tecla N): conversa em etapas (nome, WhatsApp, cidade, conta
  ou kWh, telhado, bateria, itens, outros custos) que monta e salva o orçamento e já mostra PDF/WhatsApp/link.
  O editor de 6 passos virou “Orçamento completo”.
- **Ar-condicionado (27/11)**: não leva o acréscimo do material. O vendedor digita o preço (`extras[].preco_vendedor`,
  obrigatório ao salvar) e entra `usuarios.acrescimo_ar_pct` oculto (padrão 10%) → `preco = preco_vendedor × (1+ar%)`.
  Para o vendedor o catálogo manda `preco_livre=True` e preço 0. O Orçamento fácil pergunta o preço de cada modelo.
- Acessos: `dados/CREDENCIAIS_INICIAIS.txt` (admin com senha gerada; luiz/1234).

## 9. WhatsApp do vendedor — “Meu WhatsApp” (27/11)
- O vendedor conecta o WhatsApp (QR code ou código), liga/desliga o robô e vê/responde as conversas.
- **Robô e conexão** = API de CLIENTE do **FluxIA** (VPS 157, `https://fluxia.157-173-207-22.sslip.io`, `/api/client/flows…`),
  com o login FluxIA do vendedor (`usuarios.fluxia_login/fluxia_senha`, admin preenche em Vendedores). Luiz = `luiz`
  (fluxo 5 “Advance Solar (menu)”).
- **Conversas** = direto do **Hermes Call** (mesma linha do FluxIA, sessão achada pelo nome `FluxIA - <nome do fluxo>`):
  `/api/sessions/{sid}/chats`, `/chats/{jid}/messages`, `/messages/text`. Chave do Hermes e URLs em
  `dados/segredos.json` (chmod 600; copiada do `whatsapp_connections` do FluxIA; nunca vai para o navegador).
  Nomes dos contatos vêm do FluxIA (`/contacts`); robô por conversa = `/conversations/{id}/ai`.
- Desconectar pede 2 confirmações (apaga o pareamento; volta só com QR). Admin vê o WhatsApp de cada vendedor
  em “WhatsApp dos vendedores” (`?vendedor=ID`).
- 27/11: a linha da Advance estava **desconectada** (`logged_out`) no Hermes — o Luiz precisa reconectar pelo QR.

## 10. Histórico
- 27/11/2026 — v3: ar-condicionado com preço do vendedor (+10% oculto) e “Meu WhatsApp” (FluxIA + Hermes).
- 27/11/2026 — v2: acréscimo oculto, travas do vendedor, margem 10% no financiamento, Orçamento fácil.
- 27/11/2026 — versão 1 publicada e conferida (login, cálculo, orçamento, PDF 10–11 páginas em ~3 s, link público,
  métricas, HTTPS válido, prints de todas as telas). Admin inicial em `dados/CREDENCIAIS_INICIAIS.txt`.
