# 06 — OmniRoute: Antigravity x Sua Lista (dado REAL do gateway)

> Fonte: `GET /api/providers` do OmniRoute (157.173.207.22:20128), admin logado 2026-07-02.
> O Antigravity roda **via OmniRoute** (conexões OAuth), não pelas sessões locais.
> Dados brutos: `omni_providers_raw.json`, `funil_omniroute_antigravity.json`.

## Números
- Antigravity no OmniRoute: **38 contas OAuth**
- Sua lista-mestre: **43 contas**
- Já no OmniRoute (das suas): **35**
- **Faltam adicionar no OmniRoute: 8**
- No OmniRoute mas fora da sua lista: 3 (emersonjosielmrx@gmail.com, hayllamikeycesouza@gmail.com, volupecenografiaintegrada@gmail.com)

## ❌ FALTAM no OmniRoute (adicionar via OAuth Antigravity) — 8
1. inovaremanhwaversethai@gmail.com
2. inovaremanhwaverseviet@gmail.com
3. inovaremanhwaversehindi@gmail.com
4. inovaremanhwaverserussian@gmail.com
5. inovaremanhwaversefrench@gmail.com
6. inovaremanhwaverseita@gmail.com
7. inovaremanhwaverseesp@gmail.com
8. inovaremanhwaverseind@gmail.com

> Senha de todas (da lista-mestre): `mariaedineia`. (esp e ind não tinham senha listada
> explícita, mas seguem o padrão inovaremanhwaverse* = mariaedineia — confirmar).

## Providers APIKEY já no OmniRoute
`api-airforce, freeaiapikey, opencode, opencode-zen, openrouter, pollinations`
> Groq/Cohere/DeepInfra/Fireworks/Together/Novita/Gemini **ainda NÃO estão** — são os que a
> Haylla quer adicionar (chaves válidas já testadas, ver 04_API_KEYS_PROVIDERS_INVENTARIO.md).

## ✅ ADICIONADOS em 2026-07-02 (13 conexões, todas testadas OK pelo OmniRoute)
| Provider | Qtd chaves | Nomes | Teste OmniRoute |
|---|---|---|---|
| groq | 3 | Groq-1, Groq-2, Groq-3 | OK, OK, OK |
| cohere | 1 | Cohere-1 | OK |
| deepinfra | 1 | DeepInfra-1 | OK |
| fireworks | 1 | Fireworks-1 | OK |
| together | 1 | Together-1 | OK |
| novita | 6 | Novita-1..6 | OK x6 |
> Adicionados via `POST /api/providers` (body: provider, authType:"apikey", name, apiKey, priority, isActive).
> Teste disparado via `POST /api/providers/{id}/test`.
> **Falta ainda:** Gemini (35 chaves da lista-mestre) e Mistral (gerar novas). E as 8 contas Antigravity OAuth.

## Como adicionar (endpoints admin descobertos)
- Login: `POST /api/auth/login` body `{"password":"<SEGREDO_REMOVIDO>"}` → cookie de sessão
- Listar: `GET /api/providers` (com cookie)
- Adicionar apikey provider: `POST /api/providers` (formato a confirmar — campos base:
  `provider`, `authType:"apikey"`, `name`, `apiKey`, `priority`, `isActive`)
- Adicionar conta Antigravity: fluxo OAuth (precisa do navegador logado na conta Google)
