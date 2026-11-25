# MacBook Pro 2017 ("desktop") → Omarchy 4.5? — análise pra fazer DEPOIS

Pedido da dona (24/11 ~00:40): o "desktop" é um MacBook Pro 2017 com Windows LTSC (dual boot do Boot Camp). Ela quer
trocar pra Omarchy 4.5 e usar como máquina principal pra programar (o PC1 vive ocupado). Medo: perder som e câmera,
como já aconteceu antes (o Windows foi o único sistema que ela conseguiu com áudio). "Documente e faça depois."

## O que é a máquina (lido do Windows dela, 24/11)

| Peça | Identificação | Por que importa no Linux |
|---|---|---|
| Modelo | **MacBookPro14,1** (13", 2017, 2 portas Thunderbolt, **sem Touch Bar**), BIOS 529.140.2.0.0 | sem Touch Bar = um problema a menos |
| CPU | Intel i5-7360U (2 núcleos / 4 threads) | render: 2,6 s no teste padrão (o mais rápido da casa hoje, depois do PC1 livre) |
| Som | **Cirrus Logic CS8409** (alto-falantes + microfone interno) | É ESTE o problema do áudio no Linux |
| Câmera | **FaceTime HD**, Broadcom 14e4:1570 | precisa de driver extra no Linux |
| Wi-Fi | Broadcom 802.11ac 14e4:43a3 | costuma funcionar com o driver brcmfmac + firmware |
| Teclado/trackpad | Apple SPI Keyboard / SPI Trackpad (05ac:0276) | driver `applespi` já vem no kernel Linux |
| Disco | Apple SSD AP0256 (256 GB) | dividido com o macOS (dual boot) |

## Resposta às perguntas dela

**1. Dá pra reaproveitar os drivers do Windows no Omarchy?** Não. Driver do Windows (.sys) não roda no Linux. Mas o
Linux tem drivers PRÓPRIOS, feitos pela comunidade, pra exatamente essas peças:
- **Som (CS8409):** o kernel normal não liga os alto-falantes do MacBook; existe um driver da comunidade feito pra
  MacBook Pro 2016-2019 com esse chip (projeto `snd_hda_macbookpro`, do GitHub `davidjo`). É ele que dá som.
  Precisa ser compilado e reinstalado a cada atualização de kernel (ou via DKMS). Conferir a versão pro kernel do
  Omarchy (7.2.x) ANTES de trocar.
- **Câmera (FaceTime HD):** driver da comunidade `facetimehd` (GitHub `patjak`), precisa extrair o firmware da câmera.
  Há pacote no AUR do Arch (Omarchy é Arch).
- Wi-Fi e teclado/trackpad: normalmente funcionam sem nada extra.

**2. Ficaria sem câmera e sem som?** Sem esses 2 drivers da comunidade, sim — é o que aconteceu antes. Com eles,
costuma funcionar, mas é mais trabalhoso e pode quebrar numa atualização do kernel.

**3. Dá pra pôr um Windows mais leve e reaproveitar os drivers?** Sim, esse é o caminho mais seguro pro som e a câmera:
os drivers do Boot Camp (pacote de suporte da Apple, que inclui o Cirrus e a FaceTime HD) servem em qualquer Windows
10/11. Dá pra baixar o pacote de novo pela ferramenta `Brigadier` (GitHub `timsutton`), que puxa o pacote certo pro
modelo MacBookPro14,1.

## Recomendação (decidir quando for fazer)

- **Mais seguro:** manter Windows (ou trocar por um mais leve) + drivers Boot Camp; usar o Omarchy só nos notebooks
  de render. Som/câmera garantidos.
- **Omarchy no MacBook (o que ela quer):** fazer em DUAL BOOT, sem apagar o Windows/macOS, e testar som e câmera com os
  drivers acima ANTES de mudar de vez. Se não der som, volta pro Windows sem perder nada.
- Antes de qualquer coisa: backup do que está no MacBook (o Cortes/Shorts roda nele hoje — instalar_pc3.py) e tirar
  ele da fila de render enquanto estiver sendo reinstalado.

## Estado de hoje (pra não esquecer)

- Ele roda os Shorts de parceiro (Cortes), Veo e navegador; acesso `ssh desktop` (porta 2223).
- No ranking de render (teste igual pra todos, 8 s 1080x1920 veryfast, 24/11): PC1 livre ~1,5-2 s (estimado) · MacBook
  2,6 s · S20 Ultra 3,3 s · PC2 3,5 s · Asus X 3,9 s · S20 4,2 s · Itaú 4,5 s · STI 4,6 s · G20 6,3 s · HP 8,7 s ·
  PC1 ocupado 10,2 s.

## Levantamento feito 24/11 01:15 (a pedido da dona: "faz o do Mac")

### Disco (Apple SSD 234 GB, GPT) — SEM espaço livre pra instalar outro sistema ao lado
| Partição | Tamanho | O que é |
|---|---:|---|
| C: BOOTCAMP | 93,8 GB (30,3 livres) | Windows LTSC (produção roda aqui) |
| D: "Emerson" | 130,3 GB (18 livres) | arquivos dela (NTFS) |
| sem letra | 9,3 GB | partição do macOS / recuperação (APFS) — não mexer |
| sem letra | 0,3 + 0,1 GB | EFI / boot |
Dual boot com Omarchy = precisa ENCOLHER C: ou D: (~50 GB). Maiores pastas do D: hipercool-materiais 26 GB, "pc hp"
13,9, Downloads 12,3, trader_binance 10,4, logins-google 9,2, inovare-claw-build 7,6, tmp 6,4, DRIVES BOTC 5,7.

### ✅ Drivers do Boot Camp JÁ ESTÃO no disco — reaproveitáveis num Windows mais leve
`D:\DRIVES BOTC\BootCamp\Drivers\Cirrus` (SOM CS8409), `...\Broadcom` (Wi-Fi/Bluetooth), `$WinPEDriver$` (teclado,
trackpad, SSD e vídeo Intel da Apple, prontos pra injetar na instalação), e `DRIVES-MAC-BRANCO-bootcamp`.
=> Windows leve novo + rodar o `Setup.exe` da pasta BootCamp = som e câmera funcionando. Guardar cópia no Drive
ANTES de formatar (não depender só do D: do próprio Mac).

### ⚠️ VÍRUS PROVÁVEL em `D:\DRIVES BOTC\#Pa$$w0rD__2025--0pe..._Set-Up!`
Padrão de ladrão de senhas disfarçado de instalador pirata: .exe com nome em letras estilizadas, arquivos de nome sem
sentido (Brees.nc, Higpotdoot.hi), centenas de DLLs do Windows copiadas, cópias de GameOverlayUI.exe/idmBroker.exe.
Criada 28/07/2026. Defender ligado e atualizado, 0 ameaças detectadas na história, sem rastro no Prefetch — bom sinal,
NÃO é garantia. NÃO foi executado nem apagado (decisão da dona). Se alguém rodou o .exe: trocar senhas salvas no
navegador desse Mac. Recomendado: apagar a pasta e rodar verificação completa do Defender.
