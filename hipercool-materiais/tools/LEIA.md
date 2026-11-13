# Ferramentas compartilhadas (D:\hipercool-materiais\tools)

Movidas de `D:\tools` em 17/10/2026, a pedido do dono ("o que outros projetos podem usar fica no materiais").
`D:\tools` agora é um LINK (junction) para esta pasta: todo script que usa `D:\tools\...` continua funcionando.
Trocar de PC: copiar `D:\hipercool-materiais` e recriar o link:
`New-Item -ItemType Junction -Path D:\tools -Target D:\hipercool-materiais\tools`

## O que está aqui (em uso)

| Item | Quem usa | Como reinstalar se sumir |
|---|---|---|
| `rclone.exe` (v1.68.2) | backup do Drive (`D:\manhwa-react\scripts\backup_drive.py`), `hipercool-videos\bin\backup_caches.py`, pacote do outro PC | baixar em https://rclone.org/downloads/ (Windows amd64), pôr aqui. A config do remoto `manhwa-drive:` fica em `%APPDATA%\rclone\rclone.conf` (não está aqui). Reautorizar: `rclone config reconnect manhwa-drive:` em janela anônima do navegador. |
| `separador\` (audio-separator 2.14.1+cpu, venv próprio + `modelos\`) | `hipercool-videos\bin\intros_voz.py` (separa a voz humana da música nas aberturas), `bin\voz_clonada` (coleta das vozes) | `python -m venv D:\hipercool-materiais\tools\separador` e `separador\Scripts\pip install "audio-separator[cpu]==2.14.1"`. Modelos em `separador\modelos`: `UVR-MDX-NET-Voc_FT.onnx` e o `model_bs_roformer_*` — o próprio audio-separator baixa sozinho na 1ª vez (`--model_file_dir`). |
| `applio\` (RVC sem fairseq, clone do github IAHispano/Applio, 18/10) | `D:\hipercool-materiais\bin\voz_clonada.py` (voz clonada: treina e converte o timbre) | `git clone --depth 1 https://github.com/IAHispano/Applio.git applio`; `applio\rvc\models` é LINK para `models\rvc` (`New-Item -ItemType Junction -Path applio\rvc\models -Target D:\hipercool-materiais\models\rvc`). Roda com `python\venv_vozes` (Python 3.11 em `python\runtimes`, pacotes em `python\requirements_vozes.txt`, instalar com `uv pip install -r` + torch/torchaudio 2.11 CPU de https://download.pytorch.org/whl/cpu). Config do Applio fica em `applio\config_local` (não no %APPDATA%). Modelos base: `core.py prerequisites --no-pretraineds-hifigan --models --no-exe`; o par pré-treinado baixa sozinho no 1º treino. **Alterado por nós:** `rvc\train\train.py` usa 0 workers no DataLoader em CPU (com 4 estourava a RAM) — um `git pull` desfaz isso. |

## O que foi APAGADO em 17/10 (ninguém usava; teste de vozes locais de 15/10)

| Item | Tamanho | O que era / como voltar |
|---|---|---|
| `tts-teste\` | 814 MB | venv do teste de voz local (kokoro-onnx 0.6.1 + onnxruntime 1.22.1). Voltar: `python -m venv tts-teste` + `pip install kokoro-onnx==0.6.1 soundfile numpy`. |
| `kokoro\` | 115 MB | modelo Kokoro TTS: `kokoro-v1.0.int8.onnx` + `voices-v1.0.bin`. Baixar de https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0). |
| `testar_vozes.py` | — | script do teste de 15/10 (amostras de vozes locais vs Gemini/edge). Resultado do teste: docs/voz_local_pc2.md no hipercool. |

## Outros modelos compartilhados

- `D:\hipercool-materiais\models\` — modelos de imagem do hipercool (recorte isnet-anime, rosto yolov8, profundidade
  depth-anything-v2, lbpcascade). Usados por `hipercool-videos\bin\fx_parallax.py` e `fx_acabamento.py`.
- Whisper: o hipercool NÃO usa modelo local (transcreve pelo Groq, whisper-large-v3, sempre pelo proxy).
