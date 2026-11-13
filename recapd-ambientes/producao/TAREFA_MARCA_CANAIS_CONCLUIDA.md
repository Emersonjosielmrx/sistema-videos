# Marca dos 3 canais Noturnos — CONCLUÍDA (18/10/2026)

Conferido na página **pública** dos canais em 18/10: banner, foto e nome no ar, sem marca-d'água.

| Canal | Conta | channel_id | porta cofre | Foto | Banner |
|---|---|---|---|---|---|
| Dorama Noturno | maiteanajessicajesus@gmail.com | UCCF2-yciERdJbuTnruw4jVg | 9754 | casal sob a lua | "Os momentos mais marcantes dos doramas" |
| Curiosidades Noturnas | gabriellyvitoriaisabelaaraujo@gmail.com | UCRdCdrORHLWiki711nRgkeQ | 9755 | coruja com lupa | "Fatos que você não sabia" |
| Filme Noturno | simonerebecaluizasilva@gmail.com | UCfP-zfZaA-n6lK7CyQl197g | 9756 | pipoca + claquete | "As melhores cenas do cinema" |

## Onde está tudo

Pasta: `D:\recapd-ambientes\producao\material\marca_canais\`

- `<slug>_perfil.png` — foto (1024x1024)
- `<slug>_banner.jpg` — banner final (2560x1440, com o texto)
- `<slug>_banner_bruto.png` — arte sem texto (para refazer o texto se precisar)
- `aplicar_marca.py` — sobe banner/foto no Studio, tira marca-d'água, publica
- `conferir_marca.py` — confere na página pública (sem login)

Slugs: `doramanoturno`, `curiosidadesnoturnas`, `filmenoturno`.

## Passo a passo (para trocar a marca de um canal)

1. Coloque a imagem nova com o nome certo na pasta acima (ex.: `filmenoturno_banner.jpg`).
2. Rode (abre o Chrome da conta visível, leva ~1–2 min):
   ```
   python D:\recapd-ambientes\producao\material\marca_canais\aplicar_marca.py simonerebecaluizasilva@gmail.com UCfP-zfZaA-n6lK7CyQl197g filmenoturno banner,foto
   ```
   Use só `banner` ou só `foto` para trocar um deles. Sucesso = imprime `enviado` e `publicado ...: True`.
3. Confira na página pública (as imagens novas podem levar alguns minutos pra aparecer):
   ```
   python D:\recapd-ambientes\producao\material\marca_canais\conferir_marca.py
   ```
   Ele baixa foto e banner para `%TEMP%\conferir_marca\` — abra as imagens e veja se são as novas.

## Se der erro

- **`Timeout 90000ms` esperando os botões** ou **timeout ao conectar no CDP**: sobrou um Chrome da conta aberto/travado na porta (9754/9755/9756). Feche-o e rode de novo:
  ```
  Get-NetTCPConnection -LocalPort 9756 -State Listen | % { Stop-Process -Id $_.OwningProcess -Force }
  ```
  Atenção: isso fecha o Chrome dessa conta — confira antes que nenhum postador está usando (o cofre compartilha o mesmo Chrome entre projetos).
- **Pede login do Google**: a sessão da conta caiu → `python D:\logins-google\cofre.py logar <email>` e entre na conta.
- **`botão de banner/foto não encontrado`**: o YouTube mudou o texto da página. O script acha cada seção pelo texto dela: banner = "6 MB", foto = "98 x 98", marca-d'água = "Tempo de exibição". Abra o Studio > Personalização > Branding, veja o texto atual e ajuste em `aplicar_marca.py`.
- **Último recurso, manual**: `python D:\logins-google\cofre.py logar <email>` abre o Chrome da conta → studio.youtube.com → Personalização → Branding → Alterar foto, Alterar banner, Remover marca-d'água → Publicar.

## Por que o script abre o Chrome vazio e navega depois

Abrir o Chrome já com a URL do Studio (`cofre.abrir(email, url=...)`) às vezes deixava a página sem os botões e o Chrome sem responder (aconteceu 2× no Filme Noturno). Abrindo vazio, criando aba nova e navegando com `wait_until="commit"` funcionou nos 3 canais.
