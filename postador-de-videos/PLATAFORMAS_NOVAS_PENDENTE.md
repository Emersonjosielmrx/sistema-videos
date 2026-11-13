# Plataformas novas de postagem — PENDENTE (decidido 25/10/2026)

Análise completa em memória [[project-plataformas-novas]]. O dono aprovou criar/expandir estas 3.
Encaixam no sistema de etapas do Drive (`config\etapas.json`): rede nova = acrescentar no fim da
lista do projeto + escrever o postador, que chama `bin\etapas.py registrar()`.

## 1. Kwai (EM ANDAMENTO desde 25/10)
- **Por quê:** Brasil é o maior mercado do Kwai; tem fundo de criador e pago por view; tolera repost/IA.
- **Contas:** criar/logar com as contas Google que têm cookies de TikTok (13: canalalucinaai,
  canalhistoriacomia, entrevistacomia, fabricadeautomacoesia, filmescomia00, inovaremanhwabr,
  inovaremanhwaverse esp/french/hindi/ita/russian, jornalcomia, msenergypara). Login "Entrar com Google"
  pelo cofre (`D:\logins-google\cofre`), igual aos outros serviços da fábrica.
- **Falta:** confirmar se dá para postar pelo navegador; escrever `kwai_contas.py` (criar/logar) e o postador.
- **29/10 (Fable) — sondagem real pelo navegador do cofre (jornalcomia, escondido, sem clicar):** o site
  `www.kwai.com` é SÓ de assistir: não tem página de envio (`/upload`, `/creator/upload`, `/creator-center/upload` dão
  404; nenhum `input type=file`; os únicos links de criador vão para o `creatormarketplace.kwai.com`, que é o
  marketplace de anunciantes). E a conta estava "Fazer login" (os 59 perfis do cofre com dados do kwai.com são só
  visitas, não login). **Conclusão: não dá para postar no Kwai por navegador.** Caminhos que restam (decisão da dona):
  (a) o app "Kwai para computador" (Windows) — precisa instalar no PC e automatizar a janela (sem garantia de envio por
  ele); (b) o app Android no Redroid da VPS (já usado para o WhatsApp) com automação por ADB/uiautomator — é o que
  tem mais chance, mas é um projeto; (c) checar com o Kwai se há "Kwai Creator Center" web para contas verificadas
  de criador (não apareceu para esta conta). Prints: `D:\hipercool-materiais	estes_kwai\`.
- **29/10 (Fable, 2ª passada) — o que JÁ existe no PC (a dona avisou: "já temos o app e até emuladores"):**
  - `D:\projetos-navegador\credential-factory\kwai_contas.py` + `kwai_contas.json`: **49 de 56 contas Google do cofre
    já têm conta Kwai criada/logada (26/10, "Continue com o Google")**. Falharam 7: contapessoal, emersonjosiel2027/2029,
    fabricadeautomacoes0 (Chrome fechou), fabricadeautomacoesia, filmescomia00, jogoscomia ("não confirmou login").
  - Atalho **"Kwai" da Área de Trabalho** = o PWA do kwai.com (`chrome_proxy.exe --app-id=hoghjm…` no perfil
    emersonjosiel2027). É o mesmo site: **também não tem envio**. Sondado de novo em 29/10 com a conta canalalucinaai
    (logada em 26/10): o site voltou a mostrar "Fazer login" (sessão web do Kwai dura pouco) e `/upload` continua 404.
  - **Emulador:** Redroid (Android 12 x86_64 em Docker) na VPS `hermes-bloqueio`, kit em `D:\whatsapp-activator2\vps-redroid`
    (`/opt/vps-redroid` na VPS; Magisk + TrickyStore com keybox de hardware, Play Integrity passou em 26/10; app Toque
    `com.waa11y` resolve o anti-toque; proxy residencial BR). Em 29/10 o contêiner estava **desligado** (`manter-vivo.sh`
    só liga 2×/semana para o WhatsApp), VPS com 3 GB de RAM livre e 7,9 GB de disco (92% cheio).
  - **Caminho decidido (D18 em FABLE_DECISOES.md): postar pelo app Android do Kwai dentro do Redroid.** Fluxo:
    `adb push` do vídeo → `am start -a android.intent.action.SEND -t video/mp4` para `com.kwai.video` → Toque confirma
    "Publicar" → ler a tela (`uiautomator dump`) para confirmar. Ferramenta preparada: `bin\kwai_redroid.py`
    (`--sonda` só olha; `postar` exige o app logado). **Depende da dona (2 cliques, pelo `conectar.bat`/scrcpy):**
    instalar o Kwai pela Play Store do Redroid e entrar na conta (login Google/SMS é dela: regra "não aceito OAuth
    nem digito código"). Antes disso o postador não tem onde postar. Uma conta por Redroid (regra dos celulares).
  - **Não fazer:** baixar APK de site de terceiros (fonte não confiável), rodar Kwai e WhatsApp no mesmo Redroid ao
    mesmo tempo (o `manter-vivo` desliga o contêiner), like/view automático.


## 2. Facebook Reels — expandir para todos os nichos
- **Por quê:** o Facebook paga Reel no Brasil (Content Monetization); hoje o `bin\facebook_cdp_poster.py`
  só serve o MS Energy (página mundosolarenergia).
- **Falta:** criar 1 Página grátis por nicho (pelo navegador) e apontar o postador existente para cada uma.

## 3. Dailymotion — para o recap LONGO
- **Por quê:** monetiza vídeo longo com anúncio e é frouxo com repost; o Shorts não rende o conteúdo longo.
- **Falta:** criar conta (navegador) e escrever o postador; encaixar como etapa do recapd.

## Fora (motivo)
- Snapchat/X/Rumble: Brasil fora, ou exige plano pago, ou público é EUA.
- Pinterest/Threads: só alcance, sem pagamento direto (fazer depois, se sobrar).
