# PROMPT PRO AGENTE NO PC2 — virar "fazedor de depth" do MotionFrames

> Cole isto no Claude que roda NO PC2 (a máquina que fica quase sempre ociosa,
> antes registrada como 192.168.18.7). O objetivo: o PC2 gerar DEPTH MAPS de parallax
> 2.5D dos painéis de manhwa em background, o tempo todo, e entregar pro projeto principal.

## Contexto (o que é isso)
Existe um projeto "MotionFrames" que dá MOVIMENTO REAL (parallax 2.5D) às imagens de
manhwa de um pipeline de vídeo. A etapa cara é o DEPTH MAP (estimativa de profundidade por
IA, ~3-20s por imagem em CPU — nenhuma máquina tem GPU dedicada). São ~13.200 painéis em
181 capítulos. A máquina principal (Windows, IP 192.168.18.36) fica quase sempre ocupada
renderizando vídeo, então sobra pouco tempo de CPU pra gerar depth lá. VOCÊ (PC2) fica
ocioso quase sempre → você é o lugar ideal pra moer esses depths sem parar.

NÃO precisa de GPU. Roda em CPU pura com `transformers` + `torch` (CPU) + Pillow.
Modelo: `depth-anything/Depth-Anything-V2-Small-hf` (~100MB, baixa sozinho no 1º uso).

## PROBLEMA ATUAL: as duas máquinas não se enxergam
Da máquina principal (192.168.18.36), o PC2 está invisível: nem ping, nem SMB (445), nem a
porta 8771 respondem. Provável causa: IP do PC2 mudou (DHCP), ou está em outra sub-rede
(ex: um no cabo, outro no wi-fi), ou firewall bloqueando. RESOLVA isso primeiro:

1. Descubra o IP atual deste PC2: `ipconfig` (procure IPv4 na faixa 192.168.18.x).
   - Se NÃO for 192.168.18.x, as máquinas estão em redes diferentes — me diga qual é a
     sub-rede pra alinharmos (talvez precise conectar ambos no mesmo roteador/faixa).
2. Confirme que alcança a principal: `ping 192.168.18.36` e
   `Test-NetConnection 192.168.18.36 -Port 445`. Se falhar, é firewall/sub-rede.
3. Anote o IP atual do PC2 pra atualizarmos o `workers.json` do projeto principal.

## TAREFA 1 — instalar o ambiente (uma vez)
- Python 3.10+ (qualquer um; não precisa ser o venv da outra máquina).
- `pip install transformers torch pillow numpy` (torch CPU basta; não precisa CUDA).
- ffmpeg no PATH (só pra fase futura de gerar o clip; pro depth não é obrigatório).
- Teste: `python -c "from transformers import pipeline; print('ok')"`.

## TAREFA 2 — pegar o código e os painéis
Precisa de 2 coisas da máquina principal (192.168.18.36):
- **O script** `depth_prefetch.py` + `parallax_core.py` (estão em
  `D:\hipercool-motionframes\engine\` na principal). Copie pra cá por SMB/pendrive/git.
  São ~11KB no total, autossuficientes.
- **Os painéis**: `D:\hipercool-inferior-fix\workspace\panels\` (181 pastas de cap, ~13.200
  .jpg). Duas opções:
  (a) **SMB**: a principal compartilha essa pasta; você lê direto pela rede (mais simples,
      mas depende da rede estar boa).
  (b) **Sincronizar**: copiar os painéis pra um disco local do PC2 (mais rápido pra
      processar, mas ocupa espaço). Recomendo (a) pra começar.
- **Onde devolver o depth**: o cache fica em `D:\hipercool-motionframes\cache\depth\<md5>.png`
  na principal. Aponte o PC2 pra escrever NESSE diretório via SMB (assim o pipeline principal
  consome direto), OU escreva local e sincronize de volta. O nome é md5 do CONTEÚDO da
  imagem, então não há conflito entre máquinas — as duas podem moer caps diferentes em
  paralelo e os arquivos nunca colidem.

## TAREFA 3 — ajustar caminhos no script e rodar
No `depth_prefetch.py`, ajuste no topo (são as únicas 2 linhas de caminho):
- `PANELS_ROOT` → o caminho de rede/local de onde você lê os painéis (ex:
  `\\192.168.18.36\panels` ou cópia local).
- `CACHE_DEPTH` → o caminho onde grava o depth (ex: `\\192.168.18.36\motionframes\cache\depth`
  ou local + sync).
O script é IDEMPOTENTE (pula painel já no cache) e já PULA a rodada se detectar `ffmpeg.exe`
rodando (na principal isso evita competição; no PC2, se você não renderiza, pode usar
`--ignore-ffmpeg` pra rodar sempre).

Rodar sem parar (você fica ocioso, então pode moer direto):
```
python engine/depth_prefetch.py --ignore-ffmpeg
```
Pra dividir o trabalho e não colidir esforço com a principal: combine faixas de cap. Ex:
PC2 processa da metade pra frente:
```
python engine/depth_prefetch.py --ignore-ffmpeg --obra <substring de uma obra>
```
(ou me peça pra adicionar uma flag `--skip-first N` / `--only-even` se quiser split limpo.)

## TAREFA 4 — manter rodando sempre
- Crie uma tarefa agendada do Windows (ou um loop) que reinicia o `depth_prefetch.py` se
  ele terminar, pra você ir moendo 24/7 enquanto está ocioso.
- Registre progresso num log (o script já grava em `logs/depth_prefetch.log`).

## Me devolva no final
1. IP atual do PC2 (pra atualizar `workers.json` da principal).
2. Conseguiu enxergar a principal (192.168.18.36) por SMB? Se não, qual o erro.
3. Escolheu SMB ou sync pros painéis/cache?
4. Quantos depths já gerou (contagem de .png no cache).

## Regras
- Trabalho LOCAL; não commitar/postar nada. É só geração de cache.
- Não precisa validar vídeo aqui — o depth é insumo; a validação visual é na principal.
- Qualidade esperada do depth: PNG cinza, range 0-255, std alto (separação de planos). Se
  sair tudo chapado (std baixo) ou preto, algo está errado no modelo — me avise.
