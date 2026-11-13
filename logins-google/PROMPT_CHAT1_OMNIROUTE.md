# PROMPT — CHAT 1: OMNIROUTE (gateway de IA)

> Cole isto num chat novo pra trabalhar SÓ no OmniRoute. Autossuficiente.

---

Você é meu parceiro técnico no projeto **OmniRoute** — um gateway de IA self-hosted
que agrega vários providers num endpoint só. Trabalho local, commit/push só com minha confirmação.

## Contexto
- OmniRoute roda num VPS: dashboard `http://157.173.207.22:20128`, API `http://157.173.207.22:20128/v1`
- **Senha admin do dashboard:** `sW5pgAG9obRu`
- **Chave de inferência** (usada pelo hipercool): `<SEGREDO_REMOVIDO>` (Bearer)
- Login admin via API: `POST /api/auth/login` body `{"password":"<SEGREDO_REMOVIDO>"}` → cookie de sessão
- Listar conexões: `GET /api/providers` (com cookie). Adicionar: `POST /api/providers`.
- Python do ambiente: `D:\hipercool-videos\venv\Scripts\python.exe` (sempre `PYTHONUTF8=1`)
- Toda a documentação e credenciais estão em `D:\logins-google\` (arquivos 04, 06, CREDENCIAIS_SECRETO.md).

## Estado atual (2026-07-02)
- **38 contas Antigravity (OAuth)** já cadastradas no OmniRoute.
- **8 contas faltam adicionar** (via OAuth Antigravity): inovaremanhwaverse **thai, viet, hindi, russian, french, ita, esp, ind** (@gmail.com). Senha: `mariaedineia`.
- Providers APIKEY já ativos: api-airforce, freeaiapikey, opencode, opencode-zen, openrouter, pollinations.
- **Providers que EU QUERO ADICIONAR** (chaves já testadas e válidas, em `D:\logins-google\04_API_KEYS_PROVIDERS_INVENTARIO.md` e em `D:\hipercool-inferior-fix\secrets\<prov>_keys.json`):
  - Groq (3 chaves válidas), Cohere (1), DeepInfra (1), Fireworks (1), Together (1), Novita (6).
  - Mistral: 6 chaves mortas → gerar novas depois.

## Tarefas
1. Descobrir o formato exato do `POST /api/providers` pra adicionar um provider apikey (inspecionar uma conexão apikey existente como openrouter).
2. Adicionar os providers válidos (Groq, Cohere, DeepInfra, Fireworks, Together, Novita) no OmniRoute, testando cada um após adicionar.
3. Adicionar as 8 contas Antigravity que faltam (fluxo OAuth — pode precisar de navegador logado).
4. Documentar tudo em `D:\logins-google\` conforme for fazendo.

Comece confirmando o login admin e me mostrando o formato de uma conexão apikey existente.
