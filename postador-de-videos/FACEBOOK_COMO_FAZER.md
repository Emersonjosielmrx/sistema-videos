# Facebook — como criar conta, Página, API e postar (passo a passo para repetir)

Atualizado 25/11/2026. Escrito para outro chat (ou a dona) refazer sem começar do zero. Detalhe técnico dos tokens:
`FACEBOOK_TOKEN_API.md` (mesma pasta). Memória: `project_facebook_paginas.md`, `project_facebook_upload_tamanho.md`.

## Regras que não se quebram
1. **1 perfil do Facebook = 1 saída fixa (IP).** Webshare `rnprmtfo-NN` pela ponte local `127.0.0.1:185NN`
   (`D:\recapd-ambientes\producao\colab\ponte_proxy_fixo.py NN 185NN`). Chrome, API, medição — tudo por ela. Nunca a casa
   (exceto `msenergypara`, que nasceu e sempre foi pela casa). Nunca 2 perfis no mesmo IP.
2. **Nada de rajada.** 25/11: 6 Reels em 7 min pela API = **368 (limite de frequência/spam)** e a conta teve a
   distribuição cortada (Reels antigos pararam de ganhar view). Mínimo **15 min entre posts da mesma conta**
   (`FB_API_INTERVALO_MIN`, já no `fb_reel_api.py`). Conta nova: no máximo 3 Páginas novas/dia e 3 h entre criações.
3. Teste de post nunca em Página real sem a dona combinar.
4. Token nunca no chat; só em `D:\postador-de-videos\secrets\`.

## Perfis hoje (config\facebook_paginas.json -> "contas")
| perfil | saída | Páginas | API | estado 25/11 |
|---|---|---|---|---|
| emersonjosiel02 | rnprmtfo-58 / ponte 18558 / CDP 9798 | 9 | sim (app "post2") | **repouso até 27/11 12:08** (368 + distribuição cortada) |
| mundosolar1995 | rnprmtfo-69 / ponte 18569 / CDP 9746 | 8 | sim (app "app") | postando normal (~240 views/Reel) |
| msenergypara | casa / CDP 9401 | MS energy (+2 pausadas) | não | MS energy posta por `postar_ms_energy.py` (cliente) |
| inovare_rastreio | rnprmtfo-37 / CDP 9757 | 0 | não | parada até 27/11 (FB não deixa criar Página em conta nova) |
| emersonjosiel1995 | rnprmtfo-59 | (MS energy, Maranata, Husky, Drones — pessoais) | app existe | **fora do sistema — perguntar à dona o uso** |

## A) Perfil novo do Facebook
1. Conta do Google/e-mail com saída própria no cofre (`D:\logins-google\cofre.py`; `fish_audio.checar_conta(email)` diz o -NN).
2. Entra no Facebook PELO CHROME DO COFRE na saída dela (nunca no navegador da dona). Conta nova = esperar ~1 semana
   antes de criar Página (o FB recusa: caso inovare_rastreio).
3. Pôr em `config\facebook_paginas.json` -> `"contas"`: `{"email", "porta" (97xx livre), "saida": "rnprmtfo-NN"}`.
4. Pôr em `config\fb_fila_paginas.json`: `max_dia_por_conta` e `perfil_pessoal`.

## B) Página nova (automático)
- Fila: `config\fb_fila_paginas.json` (`fila` com chave, conta, nome, categoria, bio, arte, tags, postados_em).
- Tarefa `FacebookCriarPaginas` (50 min) + o fim de cada rodada de postagem rodam `bin\fb_criar_fila.py`: cria, foto,
  capa, config, 1º Reel e **já pega o token da API** (`_token_nova`). Estado: `logs\fb_fila_estado.json`.
- Página presa: `FacebookVigia` mata criação com log parado 15 min. Página que já tem Reel vira "pronta" sozinha.
- Conta parada: `logs\fb_fila_estado.json` -> `contas.<perfil>.parada_ate`.

## C) API para um perfil (1 vez por perfil; tudo automático)
1. App no developers.facebook.com do PRÓPRIO perfil (pelo Chrome dele). Tipo "Empresa"/"Login para Empresas".
2. Casos de uso -> "Gerenciar tudo na sua Página" -> **Personalizar** (abrir pelo HREF
   `/apps/<app_id>/use_cases/customize/?...&use_case_enum=PAGES_API`; o botão não abre pela automação) -> "+ Adicionar"
   na LINHA de `pages_manage_posts`, `pages_read_engagement` (e `read_insights` para ler views).
3. `secrets\fb_app_<perfil>.json` = `{"app_id","app_secret"}`.
4. `python bin\fb_token_auto.py <perfil> tudo` — abre o Explorador no Chrome do perfil, adiciona permissões, gera,
   "Editar configurações" (ou "Continuar" se o app mudou) -> **"Aceitar todos(as) Páginas atuais e no futuro"** ->
   troca e grava `secrets\fb_paginas_<perfil>.json`. Prints de cada passo: `logs\fb_token_<perfil>_*.png`.
5. Conferir: a saída lista as Páginas com token; o token de usuário sai "não vence".

## D) Postar
- `FacebookPaginas` (de hora em hora) -> `bin\fb_rodada_todas.py` -> `postar_facebook_paginas.py --horario --conta X`.
- Ordem: **API primeiro** (`bin\fb_reel_api.py`, ~2 min/Reel) -> Chrome (`fb_reel_bs.py`) só se a API recusar.
  `FB_SEM_API=1` = só Chrome. Com a criação ocupando o Chrome, a rodada posta só pela API.
- Escada (`bin\fb_escada.py`): teto 3/dia por Página, sobe sozinho; **368 segura a conta inteira 6 h**.
- **Repouso de conta** = `logs\fb_fila_estado.json` -> `contas.<perfil>.parada_ate`: a escada dá teto 0 a TODA Página
  da conta (inclusive as criadas depois) e o criador não cria nela. Repouso só da API: `logs\fb_api_descanso.json`.
- Horário: 08-23 h; "nobre" do FB 19-22 h (o FB rende mais 18-21 h e madrugada que 21-24 h).

## E) Medir
- `PainelFacebookViews` (de hora em hora, `bin\cron_fb_painel.bat`): 1) `services.facebook.medir` (HTTP) e
  2) **`bin\fb_medir_api.py` (Graph API, cada conta pela saída dela)** -> `logs\fb_views.jsonl` (`"fonte": "api"`) ->
  `fb_painel_dados.py` -> painel :8790 "Medições Facebook" (coluna **Via** api/chrome em cada Reel + comparação).
- O campo `views` da API bate com o HTTP (Bicho 1231 x 1232) e é mais novo — **não precisa de `read_insights`**.
- Conta com distribuição cortada: os Reels novos dela ficam em 0 (25/11 emersonjosiel02: 7 de 7 em 0 com 12 h no ar).

## F) Quando der problema
| sintoma | causa | o que fazer |
|---|---|---|
| nada posta, "não baixou" | Drive lento | já tem prazo por MB (catalogo.baixar) |
| `ERR_PROXY`/timeout em tudo | ponte pendurada | `fb_saude.ponte(perfil, saida)` (o vigia faz sozinho) |
| `368 ... Limitamos a frequência` | rajada de posts | parar a conta 24-48 h; ver views dos Reels antigos |
| Reels com 0 view numa conta só | distribuição cortada | repouso 48 h; não postar por cima |
| upload estoura | vídeo > 38 MB pelo Chrome | API resolve; Chrome tem prazo por MB |
| ponte lenta (4-13 s) | `PrioridadeVSCode` rebaixou a ponte | ela tem exceção (fica Normal); medir `curl -w %{time_total}` |

## G) Ferramentas (bin\)
| arquivo | faz |
|---|---|
| `fb_token_auto.py <perfil> tudo` | gera o token da API sozinho no Chrome do perfil |
| `fb_token_assistido.py trocar <perfil>` | refaz a lista de tokens de Página (Página nova) |
| `fb_app_permissao.py <perfil> <perm...>` | liga permissões no caso de uso do app |
| `fb_app_segredo.py <perfil> ver/redefinir` | redefine a Chave Secreta do app (valida pela API antes de gravar) |
| `fb_reel_api.py teste <chave>` | posta 1 Reel pela API numa Página |
| `fb_medir_api.py [chaves]` | mede views/seguidores pela API |
| `fb_saude.py` | religa ponte caída, apaga trava morta |

## H) O que rende (análise 25/11, 78-85 Reels — refazer com mais dados)
- Hora: 18-21 h = 427 views/Reel; 12-18 h = 398; 00-08 h = 330; 21-24 h = 190 (pior). -> `NOBRE = (18, 21)`.
- Espaçamento 30-60 min pareceu melhor, mas só 5 Reels: mantido o mínimo de 15 min.
- Duração e "?" na legenda: diferença só na MÉDIA (1-2 virais); pela mediana 4-16% — não mudou o seletor.
- Volume: todas as Páginas têm 10+ dias de estoque (Hindi 10, Mundo 13, Forja 14); repõe sozinho.
- API x Chrome: mesma conta rende igual. 0 view = conta com distribuição cortada, não a API.
- Relatórios: D:\tmp\fbrel\noite\melhoria_*.md
