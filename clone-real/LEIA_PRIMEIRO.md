# Clone Real (Motion Sync no Google Flow) — PAUSADO em 01/11/2026

Ideia (vídeo https://youtu.be/OoMpgOJFTCw, Valeria Abtibool): **IMAGEM = APARÊNCIA, VÍDEO = MOVIMENTO**. A pessoa da
imagem repete os gestos, a boca e o timing de um vídeo REAL. A fala original (português) é recolocada por cima, e a boca
bate porque segue o movimento da fala original.

Dona, 01/11: aprovou o resultado no vídeo real da Advance ("ficaram boas, deu certo"). **Projeto pausado; retomar
depois.**

## Onde está cada coisa
| O quê | Onde |
|---|---|
| Código (funciona, é usado por aqui) | `D:\projeto-navegador-sem-navegador\services\veo_flow\flow_gerar.py` → `FlowGerador.motion()`, `MOTION_PROMPT`, `_para_1080`; `flow_http.py` → `subir_video()`, `falha_geracao()` |
| Histórico completo dos testes | `referencia\MOTION_SYNC_historico_testes.md` (o original fica em `D:\projeto-navegador-sem-navegador\MOTION_SYNC.md`) |
| Prompt mestre do vídeo (MotionFlow AI) | `referencia\prompt_mestre_MotionFlowAI.txt` |
| Resultados | `resultados\advance\` (**vídeo real da Advance, pessoa trocada, fala em PT**), `resultados\dono\`, `resultados\testes_flow\` |
| Scripts dos testes | `scripts_teste\` (rodar com `D:\hipercool-materiais\python\venv\Scripts\python.exe`) |

## Como usar (1 trecho de até 10 s)
```
cd D:\projeto-navegador-sem-navegador
D:\hipercool-materiais\python\venv\Scripts\python.exe -m services.veo_flow.flow_gerar fabiovideoseducativos motion "" saida.mp4 --imagem pessoa.png --video trecho.mp4 --fundo video
```
- `--fundo video` = mantém o cenário do vídeo; `--fundo imagem` = usa o cenário da foto.
- O texto entre aspas é opcional: descrição curta em inglês da pessoa da foto (ex.: `"man (short brown hair, purple t-shirt)"`).
- Pra sair em português com a fala real: depois de gerar, colocar o áudio do trecho original por cima:
  `ffmpeg -i saida.mp4 -i trecho.mp4 -map 0:v -map 1:a -c:v copy -c:a aac -shortest final_PT.mp4`
  (o `scripts_teste\teste_advance.py` faz tudo isso de uma vez: corta 10 s, gera a pessoa nova, troca, recoloca a fala).

## O que já se sabe (provado em 01/11)
- Por dentro: ferramenta do agente `generate_video_edit_video`, modelo `abra_edit` (Omni 1.1 Flash). Upload do vídeo
  por HTTP (`/upload/v1/flow/upload/video/<projeto>`), sem reCAPTCHA. O Chrome só abre pra pegar o token.
- **Limite: 3, 5 ou 10 s por geração** (catálogo do modelo). **20 créditos** por geração; a versão `abra_edit_360p`
  custa 10. Falha não cobra.
- Saída em 720p; `motion()` sobe pra 1080x1920 sozinho.
- Armadilhas: vídeo base **com áudio** é recusado (SPEECH_EDIT_BLOCKED), e `motion()` tira o áudio sozinho. Pedir **logo depois
  de enviar o vídeo** dá "state: FAILED" (código 13); é preciso esperar ~2 min, e o `motion()` já espera. Vídeo parado
  (foto com zoom) falha. Muitos pedidos seguidos na mesma conta dão `UNUSUAL_ACTIVITY` (esperar ou trocar de conta).
- A troca de pessoa às vezes sai **meio a meio**: no vídeo da Advance trocou o rosto e o cabelo, mas o corpo e a barba ficaram do original.
  Trocar roupa e cenário funciona melhor que trocar a pessoa inteira.

## Contas do Flow (01/11)
- Com crédito e com o modelo: **fabiovideoseducativos (830)**, mundosolar (50), canalalucinaai (50).
- Arquivo de cookie velho (não confirmado logout): emerson2030, emersonjosiel649, inovaremanhwaverseesp,
  emersonjosiel2027, emersoncunha, jogoscomia2.

## Pendências pra quando retomar
1. **Vídeo longo em pedaços de 10 s** (mesma imagem de referência em todos, emendar, áudio original inteiro por cima). Testar a
   emenda: a pessoa pode variar entre os pedaços. Ex.: a Advance inteira (39 s = 4 pedaços ≈ 80 créditos).
2. Variações não testadas: **M** (prompt forte pra trocar a pessoa inteira) e **N** (mulher), em
   `scripts_teste\teste_advance2.py` (aceita `<conta> <variações>`, ex. `mundosolar MN`). Na fabio deram UNUSUAL_ACTIVITY
   e na mundosolar o Chrome travou: rodar de novo com calma.
3. Copiar o `flow_gerar.py`/`flow_http.py` novos pro `dist\nsn_worker` e instalar nos notebooks e no PC2
   (`maquina_remota.py instalar-nsn <maq>`).
4. Escolher onde ligar (ideias levantadas em 01/11, na ordem sugerida):
   - **Solares (Advance/Globo/MS):** 1 vídeo real do cliente vira 5–10 versões (cenário/roupa), teste A/B no placar.
   - **Clone dos produtos:** gravação real do dono em vários cenários, com a fala real (sem voz clonada).
   - **Mascote viva:** movimento humano real (vídeo-base nosso/liberado).
   - Narrador com rosto nos canais de recap/comentários; serviço vendável no Painel de Clientes.
5. Regras: nada de repostar o mesmo vídeo disfarçado em vários canais nossos (vídeo único por canal); só
   pessoas autorizadas ou fictícias; marcar "conteúdo alterado/IA" no YouTube e no Instagram; não serve pra traduzir (a boca segue
   a fala original).
