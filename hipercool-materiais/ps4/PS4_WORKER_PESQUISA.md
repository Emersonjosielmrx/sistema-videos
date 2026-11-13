# PS4 como worker dos vídeos — pesquisa 03/11/2026

## Confirmado (fonte aberta e lida)
- PPPwn (exploit por cabo de rede): PS4 FW 7.00 a 11.00. Precisa de um PC com porta ethernet e Linux (pode ser VM com adaptador em ponte). https://github.com/TheOfficialFloW/PPPwn
- ps4-linux-loader (ps4boot): carrega Linux no FW 5.05 a 13.52 (v25). Só funciona se o console já estiver desbloqueado.
  O loader reconhece sozinho o southbridge (Aeolia, Belize ou Baikal). Lê `bzImage` + `initramfs.cpio.gz` do pendrive, do HD interno (/data/linux/boot/) ou por FTP.
  `vram.txt` define a VRAM de 32 a 4096 MB (padrão 1024). VRAM baixa = mais RAM pra servidor sem tela. https://github.com/ps4boot/ps4-linux-loader
- Kernels: Aeolia/Belize 4.14.93 (estável), 5.3.18 (Vulkan), 5.15, 6.1, 6.12 (experimentais). Baikal só 4.14 e 5.3, sem HD interno.
  Distros: Psxitarch, Gentoo, Fedora, CuteFish. https://github.com/crashniels/PS4Linux-Documentation
- O builder crashniels/ps4-linux-image (ago/2026) gera Ubuntu 26.04, Arch, CachyOS e Fedora. O kernel crashniels/linux foi atualizado em out/2026 (6.15).

## Sem prova (ninguém publicou)
- Números de realesrgan-ncnn-vulkan, RIFE, whisper.cpp ou llama.cpp no PS4. O Vulkan "existe" a partir do 5.3.18, mas não há medição de compute.
- Encode por hardware (VCE/VAAPI) no ffmpeg: não documentado. Contar só com x264 no CPU.
- Gigabit real na ethernet. Estabilidade 24 h e controle da ventoinha.

## Estimativa (não medida)
- GPU: GCN2, 18 CUs, ~1,84 TFLOPS FP32, perto de uma RX 460. Uma T4 do Kaggle tem ~8 TFLOPS FP32.
- CPU: 8 Jaguar a 1,6 GHz. Em x264 deve ficar parecido ou um pouco melhor que o i5 de 2 núcleos do desktop.
- Consumo: fat ~140 W, slim ~80–100 W, Pro ~150 W sob carga.

## Regras
- Desbloqueado = nunca na PSN, nunca atualizar. Atualizar fecha o caminho.
- Desligar a atualização automática / não ligar em Wi-Fi com internet até decidir.

## Plano proposto (aguardando firmware e modelo da dona)
1. A dona manda o firmware (Configurações > Sistema > Informações do sistema) e o modelo CUH-xxxx.
2. Se FW <= 11.00: PPPwn, depois o loader, depois Ubuntu/Arch no pendrive USB 3.0 (>= 16 GB), depois SSH.
3. Teste decisivo: `vulkaninfo` + realesrgan-ncnn-vulkan em 10 quadros. Se rodar, vira worker de upscale para 1080p (regra 1080p mínimo).
   Se não rodar, fica só como worker de CPU (ffmpeg x264 / cortes), pela pasta compartilhada com o PC.
4. Registrar o teste em video-fila\testes.py e entrar no kanban das máquinas (maquinas.py) como "ps4".
