# Pesquisa GitHub — o que agregar nos projetos de vídeo (02/11/2026 noite)

Pedido da dona (21h): "pesquise em toda internet e GitHub profundamente projetos que podemos agregar, úteis pra melhorar
algum dos projetos de vídeo atuais". Feita por argon-pesquisa (visual/render) e gemini-pro-pesquisa (áudio/roteiro/
postagem), conferida na API do GitHub (estrelas, último commit, LICENSE) em 02/11. Nada instalado ainda.
Complementa `pesquisa_github_02nov2026.md` (manhã) — nada daqui repete o que já temos/testamos.

## TOP 10 juntando as duas pesquisas (ordem = impacto ÷ esforço)

| # | Projeto | Licença | Pra quê / onde | Custo | Por que vale |
|---|---|---|---|---|---|
| 1 | [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) (BS-RoFormer, SDR ~13 dB) | MIT | **Cortes** e **recap**: tirar a voz do parceiro e MANTER música + efeitos; hoje a voz antiga ou some tudo ou vaza | T4 ~3–5 s por Short | `pip install audio-separator[gpu]`, 5 linhas. As DUAS pesquisas puseram em 1º |
| 2 | [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) + [pedalboard](https://github.com/spotify/pedalboard) | MIT / GPL-3 (uso interno ok) | Todos: voz "de locutor" (gate+compressor+EQ) e voz -14 / trilha -26 LUFS em memória | CPU, ms | Resolve de vez "trilha audível" e volume desigual (ex.: cortes do longo a -18,9) |
| 3 | [Light-ASD](https://github.com/Junhua-Liao/Light-ASD) + [auto-vertical-reframe](https://github.com/KazKozDev/auto-vertical-reframe) | MIT | **Cortes**/comerciais 16:9→9:16 seguindo QUEM FALA, câmera suave | >100 fps T4 | Hoje o corte vertical é centro/rosto; erra com 2 pessoas |
| 4 | [SenseVoice](https://github.com/QwenAudio/SenseVoice) (+ lógica do [FunClip](https://github.com/modelscope/FunClip)) | MIT | **Cortes**, **Comédia**, cortes do longo: marca RISADA, aplauso, grito, emoção no áudio → achar o trecho viral | 70 ms / 10 s | Escolha de trecho hoje é só texto (LLM); perde o pico que é visual/sonoro |
| 5 | [VoxCPM2](https://github.com/OpenBMB/VoxCPM) e [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | Apache-2.0 | Narração PT-BR com emoção por prompt, 48 kHz; podia ser a BASE antes do RVC (no lugar de edge/Kokoro) | T4 ~8 GB, RTF 0,13–0,3 | PT nativo + comercial livre. TESTAR às cegas contra a base atual antes |
| 6 | [BallonsTranslator](https://github.com/dmMaze/BallonsTranslator) / [manga-image-translator](https://github.com/zyddnys/manga-image-translator) | GPL-3 (uso interno) | **Recap de manhwa**: apagar balões/texto do painel antes da legenda MIX | T4 ~0,3 s/página | Balão em inglês briga com a nossa legenda |
| 7 | [video-subtitle-remover](https://github.com/YaoFANGUK/video-subtitle-remover) (modo STTN) | Apache-2.0 | **Cortes**: apagar legenda queimada do parceiro quando o fundo mexe (hoje = delogo, a faixa fica visível) | T4 ~30 fps | Visto na revisão: faixa do delogo bem visível embaixo |
| 8 | [LivePortrait](https://github.com/KwaiVGI/LivePortrait) + [MuseTalk](https://github.com/TMElyralab/MuseTalk) | MIT | **Comédia Noturna** (personagem piscando/boca na voz clonada) e **mascote** dos longos | T4 30+ fps | Imagem parada vira personagem vivo |
| 9 | [Seed-VC](https://github.com/Plachtaa/seed-vc) | GPL-3 (uso interno) | **Comédia**: voz nova de famoso em zero-shot (sem treinar RVC), transfere emoção | T4 tempo real | Elenco novo em minutos |
| 10 | [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) + [auto-editor](https://github.com/WyattBlue/auto-editor) | BSD / Unlicense | Todos: corte nos limites exatos de plano; tirar tempo morto | CPU, segundos | Barato e seguro |

Também úteis (2º passo): [MiniCPM-V](https://github.com/OpenBMB/MiniCPM-V)/[Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) (nota visual do
trecho, T4 int4), [ToonCrafter](https://github.com/Doubiiu/ToonCrafter) (animar o gancho de 3 s do manhwa), [LTX-Video](https://github.com/Lightricks/LTX-Video)
(B-roll dos comerciais), [PyAV](https://github.com/PyAV-Org/PyAV)/[VidGear](https://github.com/abhiTronix/vidgear) (menos subprocesso ffmpeg),
[social-auto-upload](https://github.com/dreammis/social-auto-upload) (seletores de upload atualizados), [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) (arquitetura de fábrica de Shorts).

## NÃO usar (licença proíbe uso comercial — conferido no LICENSE)
ProPainter (S-Lab), 3d-ken-burns (CC BY-NC-SA), pesos do apple/ml-sharp, F5-TTS base (CC-BY-NC), MMAudio (pesos NC),
TangoFlux (NC), XTTS-v2 (CPML), Index-TTS (Bilibili), Fish Speech (teto de receita). CosyVoice 3 e Index-TTS: sem PT.

## O que NÃO foi confirmado
Tempos na T4 são dos benchmarks dos autores, não medidos aqui. Qualidade do VoxCPM2/Qwen3-TTS em PT-BR coloquial
precisa de teste às cegas. Regra da dona: o que pesar muito no longo → medir % e perguntar antes de ligar.

## Ordem sugerida
1 e 2 primeiro (mínimo esforço, efeito em todos os Cortes/recaps). Depois 7 + 3 nos Cortes, 4 na escolha de trecho,
6 no manhwa, 8 e 9 na Comédia, 5 como teste de voz.
