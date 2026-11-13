# Cria na area de trabalho a pasta "ManhwaReact e Rede de Canais" com todos os botoes do projeto, numerados na ordem
# de uso, e tira da area de trabalho os atalhos soltos antigos. Pode rodar de novo: recria tudo igual.
$desk = [Environment]::GetFolderPath('Desktop')
$pasta = Join-Path $desk 'ManhwaReact e Rede de Canais'
New-Item -ItemType Directory -Force -Path $pasta | Out-Null
$sh = New-Object -ComObject WScript.Shell
$ico = '%SystemRoot%\system32\imageres.dll,'

function Atalho($nome, $alvo, $argumentos, $icone, $descricao) {
    $s = $sh.CreateShortcut((Join-Path $pasta "$nome.lnk"))
    $s.TargetPath = $alvo
    if ($argumentos) { $s.Arguments = $argumentos }
    if ($alvo -like '*.bat') { $s.WorkingDirectory = Split-Path $alvo }
    if ($icone) { $s.IconLocation = $icone }
    if ($descricao) { $s.Description = $descricao }
    $s.Save()
}

Atalho '1 - COLOQUE AQUI as gravacoes - em pe ou deitadas (pasta)' 'D:\manhwa-react\1-COLOQUE-AQUI' $null $null 'Coloque aqui as gravacoes do OBS, em pe ou deitadas (o sistema separa sozinho)'
Atalho '2 - PROCESSAR as gravacoes' 'D:\manhwa-react\scripts\BOTAO_PROCESSAR.bat' $null ($ico + '152') 'Processa os videos de 1-COLOQUE-AQUI e deixa prontos em D:\hipercool-materiais\manhwa-react'
Atalho '3 - APROVAR os videos prontos' 'D:\manhwa-react\scripts\BOTAO_APROVAR_E_POSTAR.bat' $null ($ico + '289') 'Revisa os videos prontos; os aprovados entram na agenda da rede (1 por canal por dia)'
Atalho '4 - VIDEOS PRONTOS (pasta)' 'D:\hipercool-materiais\manhwa-react' $null $null 'Shorts prontos, por canal'
Atalho '5 - POSTAGEM AUTOMATICA - LIGAR' 'D:\manhwa-react\scripts\BOTAO_POSTAGEM_LIGAR.bat' $null ($ico + '232') 'Liga a postagem automatica: posta as pendentes de hoje e volta a agenda'
Atalho '6 - POSTAGEM AUTOMATICA - DESLIGAR' 'D:\manhwa-react\scripts\BOTAO_POSTAGEM_DESLIGAR.bat' $null ($ico + '207') 'Desliga a postagem automatica: nada sobe nem abre navegador ate LIGAR'
Atalho '7 - PAINEL DOS CANAIS (views e comentarios)' 'D:\postador-de-videos\bin\painel_canais.bat' '--abrir' ($ico + '144') 'Inscritos, views, likes e comentarios dos 19 canais'
Atalho '8 - CORTAR SO A CAMERA (arraste o video em cima)' 'D:\manhwa-react\scripts\BOTAO_CORTAR_CAMERA.bat' $null ($ico + '18') 'Arraste o video: tira so a webcam (sem o video de baixo) em 1920x1080'
Atalho '9 - Pasta do projeto manhwa-react' 'D:\manhwa-react' $null $null $null
Copy-Item 'D:\manhwa-react\scripts\LEIA_BOTOES.txt' (Join-Path $pasta '0 - O QUE CADA BOTAO FAZ.txt') -Force

# atalhos soltos antigos (agora dentro da pasta) e nomes antigos dentro da pasta
Remove-Item -LiteralPath (Join-Path $pasta '1 - COLOQUE AQUI as gravacoes (pasta).lnk') -ErrorAction SilentlyContinue
foreach ($velho in 'ManhwaReact - PROCESSAR.lnk', 'ManhwaReact - APROVAR E POSTAR.lnk', 'ManhwaReact - CORTAR CAMERA.lnk',
                   'ManhwaReact - COLOQUE AQUI.lnk', 'ManhwaReact - PRONTOS.lnk', 'manhwa-react.lnk', 'PAINEL DOS CANAIS.bat') {
    $p = Join-Path $desk $velho
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p }
}
Write-Output "botoes criados em $pasta"
