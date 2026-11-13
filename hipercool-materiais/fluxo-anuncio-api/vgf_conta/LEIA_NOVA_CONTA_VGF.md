# Como criar mais uma conta no Very Good FFmpeg (ffmpeg na nuvem) e ligar no n8n6

## O que é
Very Good FFmpeg (https://verygoodffmpeg.com) roda comandos ffmpeg na nuvem por API. Os fluxos do n8n6 que usam:
Vídeo de Anúncio V3/V3b e Editor de Reels (original, V2, V3, V4 MIX, V5). Conta grátis: **sem cartão**, entra com
Google, ganha **US$ 1 = 2 GB** de processamento. Quando acabar, cria-se outra conta com outro Google do cofre.

A conta atual é `aulacomia@gmail.com`, com a chave em `..\vgf_chave.txt` e a credencial n8n6 `ReRD13CCkctXbd8w`
("Very Good FFmpeg (Bearer)").

## Regras
- **Nunca** mostrar a chave em log, chat ou documento. O script só imprime o começo e o fim dela.
- **Nunca** pôr cartão. Se o site pedir cartão, pare e anote.
- O Google tem de ser uma conta do cofre (`D:\logins-google\cofre.py`) já logada. Se não estiver logada:
  `login_em_lote.py`. A dona digita só a senha; não faça login de 1 em 1.
- RAM: abaixo de ~3 GB livres, rode `chrome_conta._liberar_ram` antes de abrir o Chrome.
- Feche o Chrome no fim (o script já fecha com `cofre.fechar`).
- Rode sem janela. Use `--visivel` só se o login sem janela falhar, e avise a dona antes.

## Passo a passo
1. Escolha um Google do cofre que ainda **não** tenha conta no Very Good FFmpeg.
2. Rode:
   ```
   cd D:\hipercool-materiais\fluxo-anuncio-api\vgf_conta
   python vgf_nova_conta.py <email@gmail.com> --n8n
   ```
   O script faz isto:
   - abre o Chrome do cofre daquela conta;
   - entra em /sign-in e aperta "Continue with Google" (escolhe a conta e aceita a tela de consentimento da 1ª vez);
   - vai à página de chaves da API e cria uma chave chamada "n8n" se não houver nenhuma;
   - copia a chave pelo botão Copy e testa cada candidata em `POST /api/tmp-file`. Esse teste não gasta crédito:
     200 = chave boa, 401 = errada;
   - guarda só as chaves boas em `vgf_chave_<email>.txt`;
   - com `--n8n`, cria a credencial **Header Auth** no n8n6: nome `Authorization`, valor `Bearer <chave>`, título
     "Very Good FFmpeg (Bearer) <email>". O script imprime o **id** da credencial.
   - deixa prints de cada etapa em `provas\<email>_*.png`. Se algo falhar, olhe os prints.
3. Trocar os fluxos para a conta nova. Não edite os fluxos marcados "ok" à mão; troque pelo gerador:
   - Vídeo de Anúncio V3: `python ..\v3\gera_v3.py <id_da_credencial>`, depois `python ..\n8n6.py importa <json>`.
   - Editor de Reels: o id da credencial vem de `..\v3\cred_id.txt`. Ponha o id novo nesse arquivo e rode
     `python ..\editor\gera_editor.py`. Depois rode `python ..\editor_v2\gera_versoes.py` e importe
     `fluxo_v2..v5.json` com `python ..\n8n6.py importa ..\editor_v2\fluxo_vN.json`. O original "- ok" só se a dona
     pedir.
   - Também dá para trocar só a credencial dentro do n8n (nó "🎬 Very Good FFmpeg…", campo Credential).
4. Teste ponta a ponta. Esta é a prova de que a conta funciona:
   ```
   python D:\hipercool-materiais\fluxos-n8n\_testes\testa_envio_v4.py <video.mp4> webhookn8n6.inovareinteligenciaartificial.com editor-reel-v4 --edita
   ```
   O resultado tem de dar `etapa=pronto` e o vídeo tem de sair 1080x1920. Confira com
   `D:\hipercool-materiais\bin\ffprobe.exe`.
5. Anote no `..\PROGRESSO.md`: o e-mail da conta nova, a data, o id da credencial e quanto crédito sobrou na antiga.

## Para usar a API direto (sem n8n)
- Cabeçalho: `Authorization: Bearer <chave>`.
- `POST /api/tmp-file` → `{data:{upload_url, download_url}}`. Suba o arquivo com PUT no `upload_url` (vale 1 h). O
  navegador não consegue subir direto (CORS); o arquivo tem de passar por um servidor.
- `POST /api/ffmpeg` com o comando e as entradas → `{data:{id,status}}`. Depois consulte até terminar. Exemplo
  completo em `..\teste_vgf.py <pedido.json>` (lê a chave de `..\vgf_chave.txt`).
- Armadilhas:
  - o serviço **não tem ffprobe**;
  - não aceita redirecionamento de shell;
  - fontes vão em `inputs/` com `fontsdir=inputs`;
  - saída com cartão em JPEG vira yuvj420p: use `scale=out_range=tv,format=yuv420p` e `-color_range tv`;
  - o catbox derruba downloads feitos da nuvem: sirva os arquivos pelo webhook `-arquivo` do n8n.

## Arquivos
- `vgf_nova_conta.py`: o script desta pasta (cria/reaproveita a conta, gera e testa a chave, cria a credencial).
- `..\vgf_painel.py`: o script original de 30/10 (conta aulacomia, fixo). Não mexer.
- `..\teste_vgf.py`: manda um pedido de ffmpeg e acompanha.
