# Observações caps 2-3 — para avaliar depois do cap 4

Data: 14/10/2026

## 1. Propaganda do scan NÃO está sendo filtrada (confirmado)

**Panel 009 do cap 2**: propaganda pura da Blackout Comics (logo, URL blackoutcomics.com,
"acesso antecipado ao capítulo", Discord). Entrou no vídeo com narração normal do narrador
("Eita! O drama já começou em nível máximo").

**Panel 010 do cap 2**: gradiente vazio (branco→cinza), painel de transição sem conteúdo.
Também entrou com narração genérica do narrador.

**Causa raiz**: `is_propaganda()` em `fx_detect.py` filtra por keywords na **descrição
gerada pelo LLM**, mas o LLM descreveu o panel 009 como "Tela final exibe créditos da obra
sobre fundo branco com logotipos" — sem repetir as keywords "blackout", "acesso antecipado",
etc. A detecção falhou.

**Possíveis correções (não mexer agora)**:
- Adicionar keywords "créditos", "logotipos", "tela final" à lista de propaganda
- Adicionar OCR real (EasyOCR/PaddleOCR ONNX) no painel original antes de gerar descrição
- Detectar painéis "quase vazios" (gradientes, fundos sólidos) por análise de variância da imagem
- O painel 010 poderia ser filtrado por variância/entropia baixa (é um degradê puro)

## 2. Contexto narrativo pode estar fraco

O dono reportou que "alguns detalhes da história não ficam claros" nos caps 2 e 3.
Analisando a narração do cap 2:

- O narrador reage BEM aos momentos de impacto (estilo viral, como pedido)
- MAS: em sequências densas de diálogo (painéis 17-36), o narrador faz comentários genéricos
  ("A tensão é tanta que daria para cortar com uma faca", "Fica claro que algo sombrio
  aconteceu") sem dar contexto do QUE está acontecendo na cena
- O narrador deveria contextualizar: QUEM são os personagens, QUAL é a situação, POR QUE
  isso importa — não só reagir. Exemplo: em vez de "O rappaz está suando frio", dizer
  "Joo Inhyuk não esperava que a herança do pai fosse uma PESSOA"
- *Hipótese*: o prompt de narração foca em engajamento/humor mas não instrui suficientemente
  sobre dar CONTEXTO/RESUMO da cena. O modelo gera reações virais sem explicar a trama.

**Possível correção no prompt de narração (não mexer agora)**:
- Adicionar instrução explícita: "O narrador DEVE contextualizar a cena para quem não leu
  o manhwa. A cada 5-8 painéis, resuma brevemente O QUE está acontecendo e POR QUÊ, não
  apenas reaja emocionalmente."

## 3. Painéis possivelmente fora de ordem no meio do capítulo

O dono reportou que "tem alguns quadros que parecem fora de ordem" no meio do vídeo.
- No começo está bom ("e no comeso e muito bom")
- "essa desordem no meio pode ser avaliada"

Análise: O pipeline segue a ordem dos painéis no diretório (panel_000.jpg, panel_001.jpg,
etc.). NÃO há reordenação no código. Se painéis parecem fora de ordem, pode ser:
1. O scan original já veio com painéis fora de ordem (erro do scraper)
2. A narração de um painel não bate com a descrição visual, dando sensação de descontinuidade
3. Painéis de transição/flashback do manhwa (mudança de cena sem aviso) ficam confusos
   sem narração explicativa

Para confirmar se é bug (painéis trocados) vs. narrativa (o manhwa usa flashbacks):
- Comparar a ordem dos painéis .jpg com o manhwa original
- Se for flashback do manhwa, o narrador deveria sinalizar ("enquanto isso...",
  "voltando no tempo...", "ele se lembrava de...")

**Ação**: Não mexer. Esperar o cap 4 para ver se o problema persiste. Se persistir, pode
ser necessário ajustar o prompt de narração para detectar e sinalizar mudanças de cena.
